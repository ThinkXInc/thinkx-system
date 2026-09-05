#!/usr/bin/env python3
"""thinkx-system/infra/scripts/stg.py   【分類: 観測系(見るだけ。状態を変えない)】

staging web(web1-stg)の Claude Code 常駐セッションと claude_connect を Mac から観測する。
承認プロンプト(settings の ask: ssh/curl 前置一致)に掛からない固定コマンド列として置く。
計画書: infra/docs/STG_OBSERVE_PLAN.md。前提の実測: infra/findings.md 2026-09-05。

  python3 infra/scripts/stg.py check                 uptime / unit / tmux / state / pane 末尾 / 外形
  python3 infra/scripts/stg.py watch [--interval 5] [--max 54] [--log-lines 8]
                                                     state の遷移を connected まで見守る
  python3 infra/scripts/stg.py log [--unit claude_connect] [--since-min 30] [-n 50]
                                                     journalctl(相対時刻。サーバーは UTC)
  python3 infra/scripts/stg.py doctor                前提(ユーザー・hostname・TZ・bind・DNS・unit)を機械検証

大原則(計画書):
  - 観測のみ。send-keys / kill / restart / logout は持たない。
  - リモートで実行する文字列は全てこのファイル内の固定リテラル。引数として受け取らない。
    値引数は整数かホワイトリストに限り、置換して埋める。
  - ログイン URL は出さない(url=yes/no)。--show-url を付けたときだけ出す。
  - 前提が崩れたら doctor が検出する。定数を毎回再発見しない。
python3 標準ライブラリのみ。戻り値 0/1。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

# ---- 定数(前提。崩れたら doctor が検出し、ここと findings を更新する) ----
HOST = "supercom-web1-stg"                       # infra/docs/hostname.md ①層。ログインは ubuntu
SSH = ["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", HOST]
STATE_URL = "http://web1:8008/connect/state"     # bind は private IP のみ(127.0.0.1 は不可)。web1 は dns.tf の内部名
PUBLIC = "https://staging.thinkxinc.com"
PUBLIC_PATHS = ("/", "/connect/", "/connect/state")
PUBLIC_EXPECT = 401                              # Basic 認証の外からは 401 が正常(findings 2026-09-05 N-4)
LOG_UNITS = ("claude_connect", "claude-session")
EXPECT = {
    "user": "ubuntu",
    "hostname": "web1-stg",
    "sudo": "ok",
    "tz": "Etc/UTC",
    "listen": "192.168.2.11:8008",               # terraform local.web_ip(固定)
    "web1": "192.168.2.11",
    "enabled_claude_session": "enabled",
    "enabled_claude_connect": "enabled",
    "state_http": "200",
}

G, R, Y, Z = "\033[32m", "\033[31m", "\033[33m", "\033[0m"

# ---- リモートで実行する固定リテラル ----
REMOTE_CHECK = r"""
uptime
echo "--- units (claude-session claude_connect nginx uwsgi_thinkx)"
systemctl is-active claude-session claude_connect nginx uwsgi_thinkx
echo "--- tmux (kaz)"
sudo -n -u kaz tmux ls 2>&1
sudo -n -u kaz tmux list-panes -t claude -F '#{pane_current_command}' 2>&1
echo "--- state"
curl -s -m 30 http://web1:8008/connect/state
echo
echo "--- pane tail 8"
sudo -n -u kaz tmux capture-pane -p -t claude 2>&1 | grep -v '^[[:space:]]*$' | grep -v '^Permission ' | tail -8
"""

REMOTE_WATCH = r"""
prev=""; i=0
while [ "$i" -lt __MAX__ ]; do
  i=$((i+1))
  s="$(curl -s -m 10 http://web1:8008/connect/state | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["state"], "url=" + ("yes" if d.get("url") else "no"))' 2>/dev/null)"
  [ -n "$s" ] || s="unreachable"
  if [ "$s" != "$prev" ]; then echo "$(date -u +%T)Z $s"; prev="$s"; fi
  case "$s" in connected*) break;; esac
  [ "$i" -lt __MAX__ ] && sleep __INTERVAL__
done
echo "--- journal tail (claude_connect, GET /connect/state を除く)"
sudo -n journalctl -u claude_connect --no-pager -n 5000 -o cat | grep -v 'GET /connect/state' | tail -n __LOGN__
"""

REMOTE_LOG = "sudo -n journalctl -u __UNIT__ --no-pager --since -__MIN__min -n __N__ -o cat"

REMOTE_DOCTOR = r"""
echo "user=$(id -un)"
echo "hostname=$(hostname)"
echo "sudo=$(sudo -n true 2>/dev/null && echo ok || echo fail)"
echo "tz=$(timedatectl show -p Timezone --value 2>/dev/null)"
echo "listen=$(ss -ltn 2>/dev/null | awk '{print $4}' | grep ':8008$' | head -1)"
echo "web1=$(getent hosts web1 | awk '{print $1}' | head -1)"
echo "enabled_claude_session=$(systemctl is-enabled claude-session 2>/dev/null)"
echo "enabled_claude_connect=$(systemctl is-enabled claude_connect 2>/dev/null)"
echo "state_http=$(curl -s -m 10 -o /dev/null -w '%{http_code}' http://web1:8008/connect/state)"
"""


def ssh_run(remote: str, timeout: int) -> tuple[int, str]:
    """固定リテラル remote を ssh で流し、(戻り値, 標準出力+標準エラー) を返す。shell は使わない。"""
    try:
        done = subprocess.run(SSH + [remote], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 1, f"ssh timeout ({timeout}s)"
    except OSError as e:
        return 1, str(e)
    return done.returncode, done.stdout + done.stderr


def ok(msg: str) -> int:
    print(f"{G}OK: {msg}{Z}")
    return 0


def fail(msg: str) -> int:
    print(f"{R}FAIL: {msg}{Z}")
    return 1


def unreachable(sub: str, out: str) -> int:
    print(out.strip())
    return fail(f"stg {sub} ssh 到達不可(staging 停止中? 別名 {HOST})")


def hide_urls(lines: list[str], show_url: bool) -> list[str]:
    """pane に描かれたログイン URL を隠す。

    URL は pane 幅で複数行に折れる(ハード改行)。行頭が http の行から、空行・行頭空白の行の手前までが
    1 つの URL(server.py find_url と同じ判定)。その塊を 1 行の目印に置き換える。
    """
    if show_url:
        return lines
    out: list[str] = []
    hiding = False
    for line in lines:
        if hiding and line and not line.startswith(" "):
            continue
        hiding = False
        if line.startswith("http"):
            out.append("<url hidden; --show-url で表示>")
            hiding = True
            continue
        out.append(line)
    return out


def public_code(path: str) -> str:
    """外形の HTTP code。Mac の python3 は CA バンドルが無いことがあるので curl(OS の信頼ストア)で取る。"""
    try:
        done = subprocess.run(["curl", "-s", "-o", "/dev/null", "-m", "15", "-w", "%{http_code}", PUBLIC + path],
                              capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"ERR({e})"
    return done.stdout.strip() or f"ERR(curl rc={done.returncode})"


# ---- サブコマンド ----
def cmd_check(args: argparse.Namespace) -> int:
    rc, out = ssh_run(REMOTE_CHECK, timeout=90)
    lines = out.splitlines()
    if rc == 255 or not lines:
        return unreachable("check", out)

    state = None
    for i, line in enumerate(lines):
        if line.startswith("{"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            state = d.get("state")
            if not args.show_url:
                d["url"] = "yes" if d.get("url") else "no"
            lines[i] = json.dumps(d, ensure_ascii=False)
            break

    print("\n".join(hide_urls(lines, args.show_url)).strip())

    print(f"--- 外形 {PUBLIC} (期待 {PUBLIC_EXPECT})")
    bad = []
    for p in PUBLIC_PATHS:
        code = public_code(p)
        print(f"{p:<16}{code}")
        if code != str(PUBLIC_EXPECT):
            bad.append(f"{p}={code}")

    problems = []
    if state is None:
        problems.append("state 取得不可")
    if bad:
        problems.append("外形 " + " ".join(bad))
    if problems:
        return fail("stg check " + " / ".join(problems))
    return ok(f"stg check state={state} 外形 {len(PUBLIC_PATHS)}/{len(PUBLIC_PATHS)} = {PUBLIC_EXPECT}")


def cmd_watch(args: argparse.Namespace) -> int:
    if not (1 <= args.interval <= 60 and 1 <= args.max <= 720 and 1 <= args.log_lines <= 200):
        return fail("stg watch 範囲外: --interval 1..60 / --max 1..720 / --log-lines 1..200")
    remote = (REMOTE_WATCH.replace("__MAX__", str(args.max))
              .replace("__INTERVAL__", str(args.interval))
              .replace("__LOGN__", str(args.log_lines)))
    rc, out = ssh_run(remote, timeout=args.interval * args.max + 60)
    if rc == 255 or not out.strip():
        return unreachable("watch", out)
    print(out.strip())
    last = [line for line in out.splitlines() if line.endswith("url=yes") or line.endswith("url=no")]
    final = last[-1].split()[1] if last else "unknown"
    if final == "connected":
        return ok("stg watch connected")
    return fail(f"stg watch 最終 state={final}({args.interval}s x {args.max})")


def cmd_log(args: argparse.Namespace) -> int:
    if args.unit not in LOG_UNITS:
        return fail(f"stg log --unit は {' / '.join(LOG_UNITS)} のみ")
    if not (1 <= args.since_min <= 10080 and 1 <= args.n <= 2000):
        return fail("stg log 範囲外: --since-min 1..10080 / -n 1..2000")
    remote = (REMOTE_LOG.replace("__UNIT__", args.unit)
              .replace("__MIN__", str(args.since_min))
              .replace("__N__", str(args.n)))
    rc, out = ssh_run(remote, timeout=60)
    if rc == 255:
        return unreachable("log", out)
    print(out.strip() or f"{Y}(直近 {args.since_min} 分に {args.unit} のログなし。時刻はサーバー UTC){Z}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    rc, out = ssh_run(REMOTE_DOCTOR, timeout=60)
    got = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    if rc == 255 or not got:
        return unreachable("doctor", out)
    bad = 0
    for key, want in EXPECT.items():
        have = got.get(key, "")
        mark = f"{G}OK{Z}" if have == want else f"{R}NG{Z}"
        bad += have != want
        print(f"{mark}  {key:<24}{have:<24}(期待 {want})")
    if bad:
        return fail(f"stg doctor 前提が {bad} 件崩れている — stg.py の定数と infra/findings.md を更新")
    return ok(f"stg doctor 前提 {len(EXPECT)} 件すべて成立")


def main() -> int:
    ap = argparse.ArgumentParser(prog="stg.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("check", help="uptime / unit / tmux / state / pane 末尾 / 外形")
    p.add_argument("--show-url", action="store_true", help="ログイン URL を隠さず出す")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("watch", help="state の遷移を connected まで見守る")
    p.add_argument("--interval", type=int, default=5, help="秒(既定 5)")
    p.add_argument("--max", type=int, default=54, help="回数(既定 54 = 約 4.5 分)")
    p.add_argument("--log-lines", type=int, default=8, help="終了時に出す journal 行数(既定 8)")
    p.set_defaults(fn=cmd_watch)

    p = sub.add_parser("log", help="journalctl(相対時刻・サーバー UTC)")
    p.add_argument("--unit", default="claude_connect", help="claude_connect(既定) / claude-session")
    p.add_argument("--since-min", type=int, default=30, help="直近 N 分(既定 30)")
    p.add_argument("-n", type=int, default=50, help="最大行数(既定 50)")
    p.set_defaults(fn=cmd_log)

    p = sub.add_parser("doctor", help="前提(ユーザー・hostname・TZ・bind・DNS・unit)を機械検証")
    p.set_defaults(fn=cmd_doctor)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        print(f"\n{Y}サブコマンドを指定してください(check / watch / log / doctor)。{Z}")
        return 1
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
