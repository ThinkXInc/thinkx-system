#!/usr/bin/env python3
"""thinkx-system/infra/scripts/verify_deploy.py   【分類: 観測系(見るだけ。状態を変えない)】

デプロイの「反映前の差分」と「反映後の着地」を Mac から観測する。
承認プロンプト(settings の ask: ssh/curl 前置一致)に掛からない固定コマンド列として置く。
材料: docs/approval_cases_v2.md(着地確認 7 回・本番 URL 観測 7 回で昇格)。

  python3 infra/scripts/verify_deploy.py preview
      本番に何が出るかの事前確認。develop と production の先端・tree・未反映コミット・
      触るディレクトリ + staging の claude_connect が返すデプロイプレビュー。
  python3 infra/scripts/verify_deploy.py landed staging|prod [--file F --contains S]... [--unit U]
      着地確認。サーバーの先端コミットが追従先ブランチと一致するか + 指定ファイルに
      指定文字列が入ったか + unit の起動時刻。
  python3 infra/scripts/verify_deploy.py site staging|prod [--repeat N] [--path P] [--contains S]...
      公開 URL の応答。http code / 接続時間 / 合計時間 / 接続先 IP。--contains で本文の
      文字列有無も見る(staging は Basic 認証を loadbalancer/.env から読む)。

大原則(stg.py と同じ):
  - 観測のみ。deploy / restart / 書き込みは持たない。
  - 接続先(ホスト・ドメイン・unit)はこのファイル内の固定リテラル。任意ホスト・任意 URL は受けない。
  - リモートで実行する文字列は固定リテラル。値引数(探す文字列・ファイルパス・回数)は
    検証してから shlex.quote で埋める。ファイルパスは /src/thinkx-system 配下のみ。
python3 標準ライブラリのみ。https は Mac の python3 に CA バンドルが無いことがあるため
curl(OS の信頼ストア)を subprocess で叩く(stg.py と同じ判断)。戻り値 0/1。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shlex
import subprocess
import sys

# ---- 定数(前提。崩れたらここと infra/findings.md を更新する) ----
WS = pathlib.Path(__file__).resolve().parents[2]
ENVS = ("staging", "prod")
HOST = {"staging": "supercom-web1-stg", "prod": "supercom-web1"}     # infra/docs/hostname.md ①層
TRACK = {"staging": "origin/develop", "prod": "origin/production"}   # deploy timer の追従先
SITE = {"staging": "https://staging.thinkxinc.com", "prod": "https://thinkxinc.com"}
# パスごとの期待 code。/remote_control/ は Basic 認証(外からは 401 が正常。2026-10-01 実測)
SITE_PATHS = {"staging": {"/": 200, "/connect/": 200, "/podcast/": 200},
              "prod": {"/": 200, "/about": 200, "/remote_control/": 401}}
REPO = "/src/thinkx-system"                                          # サーバー側 checkout(固定)
UNITS = ("uwsgi_thinkx", "claude_connect", "nginx")
BASIC_AUTH_ENV = WS / "loadbalancer" / ".env"                        # STAGING_BASIC_AUTH_USER/PASS
FILE_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")               # .. と絶対パスは下で別途拒否
PATH_OK = re.compile(r"^/[A-Za-z0-9._/-]*$")

G, R, Y, Z = "\033[32m", "\033[31m", "\033[33m", "\033[0m"

# ---- リモートで実行する固定リテラル(値は shlex.quote 済みのものだけ埋める) ----
# checkout(__REPO__)の所有者は kaz。ubuntu のままだと git の所有権チェックと 640 のファイルで
# 読めないため、読み取りも kaz で行う(stg.py の tmux と同じ)。
REMOTE_LANDED = """
sudo -n -u kaz git -C __REPO__ log --oneline -1
echo "head=$(sudo -n -u kaz git -C __REPO__ rev-parse HEAD)"
systemctl show __UNIT__ -p ActiveEnterTimestamp
__GREPS__
"""

REMOTE_GREP = 'echo "grep __FILE__ -> $(sudo -n -u kaz grep -c -F -- __NEEDLE__ __REPO__/__FILE__ 2>/dev/null || true) 箇所"'

REMOTE_PREVIEW = "curl -s -m 60 http://web1:8008/connect/deploy"


def run(cmd: list[str], timeout: int = 60, stdin: str | None = None) -> tuple[int, str]:
    """コマンドを流し (戻り値, 標準出力+標準エラー) を返す。shell は使わない。"""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=stdin)
    except subprocess.TimeoutExpired:
        return 1, f"timeout ({timeout}s): {cmd[0]}"
    except OSError as e:
        return 1, str(e)
    return done.returncode, done.stdout + done.stderr


def ssh_run(env: str, remote: str, timeout: int = 60) -> tuple[int, str]:
    return run(["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", HOST[env], remote], timeout)


def git(args: list[str]) -> str:
    rc, out = run(["git", "-C", str(WS)] + args)
    return out.strip() if rc == 0 else ""


def ok(msg: str) -> int:
    print(f"{G}OK: {msg}{Z}")
    return 0


def fail(msg: str) -> int:
    print(f"{R}FAIL: {msg}{Z}")
    return 1


def staging_auth() -> str:
    """loadbalancer/.env から Basic 認証を読み "user:pass" を返す(無ければ空)。値は表示しない。"""
    try:
        text = BASIC_AUTH_ENV.read_text()
    except OSError:
        return ""
    cred = {}
    for line in text.splitlines():
        key, _, value = line.partition("=")
        if key in ("STAGING_BASIC_AUTH_USER", "STAGING_BASIC_AUTH_PASS"):
            cred[key] = value.strip()
    if len(cred) == 2:
        return cred["STAGING_BASIC_AUTH_USER"] + ":" + cred["STAGING_BASIC_AUTH_PASS"]
    return ""


def fetch_head(url: str, auth: str, body: bool = False) -> tuple[str, str]:
    """(code/時間/IP の1行, 本文) を返す。認証は ps に出さないよう curl の --config 標準入力で渡す。"""
    config = f'user = "{auth}"\n' if auth else ""
    fmt = "HTTP %{http_code}  connect %{time_connect}s  total %{time_total}s  remote %{remote_ip}"
    cmd = ["curl", "-s", "-m", "15", "-K", "-", "-w", fmt, url]
    if not body:
        cmd[1:1] = ["-o", "/dev/null"]
    rc, out = run(cmd, timeout=20, stdin=config)
    if rc != 0 and "HTTP" not in out:
        return f"ERR(curl rc={rc})", ""
    head = out[out.rfind("HTTP "):].strip()
    return head, out[: out.rfind("HTTP ")]


# ---- サブコマンド ----
def cmd_preview(args: argparse.Namespace) -> int:
    git(["fetch", "-q", "origin"])
    dev, prod = git(["rev-parse", "--short", "origin/develop"]), git(["rev-parse", "--short", "origin/production"])
    dev_tree, prod_tree = git(["rev-parse", "origin/develop^{tree}"]), git(["rev-parse", "origin/production^{tree}"])
    if not (dev and prod):
        return fail("preview: origin/develop か origin/production を解決できない(fetch 失敗?)")
    print(f"develop    {dev}\nproduction {prod}")

    if dev_tree == prod_tree:
        print("未反映コミット: なし(tree 一致)")
    else:
        print("--- 未反映コミット(production..develop)")
        print(git(["log", "--oneline", "--no-merges", "origin/production..origin/develop"]) or "(なし)")
        changed = git(["-c", "core.quotepath=false", "diff", "--name-only", "origin/production", "origin/develop"])
        dirs = sorted({line.split("/", 1)[0] for line in changed.splitlines() if line})
        print("--- 触るディレクトリ: " + (" ".join(dirs) or "(なし)"))

    print("--- staging claude_connect のデプロイプレビュー")
    rc, out = ssh_run("staging", REMOTE_PREVIEW, timeout=90)
    try:
        d = json.loads(out.strip().splitlines()[-1])
        print(f"same={d.get('same')} commits={len(d.get('commits', []))} services={d.get('services')}")
    except (ValueError, IndexError):
        print(f"{Y}(プレビュー取得不可: {out.strip()[:200] or 'ssh 失敗'}){Z}")

    if dev_tree == prod_tree:
        return ok("preview 差分なし(本番は develop と同内容)")
    return ok("preview 差分あり(上の一覧が本番に出る)")


def cmd_landed(args: argparse.Namespace) -> int:
    if len(args.file) != len(args.contains):
        return fail("landed: --file と --contains は同数をペアで(--file F --contains S の順)")
    greps = []
    for file in args.file:
        if not FILE_OK.match(file) or ".." in file:
            return fail(f"landed: --file は {REPO} 配下の相対パスのみ: {file}")
        greps.append(file)

    grep_lines = "\n".join(
        REMOTE_GREP.replace("__FILE__", shlex.quote(f)).replace("__NEEDLE__", shlex.quote(s))
        for f, s in zip(greps, args.contains))
    remote = (REMOTE_LANDED.replace("__GREPS__", grep_lines)
              .replace("__REPO__", REPO).replace("__UNIT__", args.unit))

    git(["fetch", "-q", "origin"])
    local_sha = git(["rev-parse", TRACK[args.env]])
    rc, out = ssh_run(args.env, remote, timeout=90)
    if rc == 255 or not out.strip():
        return fail(f"landed {args.env}: ssh 到達不可({HOST[args.env]})")
    print(out.strip())

    server_sha = next((line[5:] for line in out.splitlines() if line.startswith("head=")), "")
    problems = []
    if not local_sha or server_sha != local_sha:
        problems.append(f"先端不一致(追従先 {TRACK[args.env]}={local_sha[:9]} / サーバー={server_sha[:9]})")
    for line in out.splitlines():
        if line.startswith("grep "):
            count = line.rsplit("-> ", 1)[-1].replace(" 箇所", "").strip()
            if not (count.isdigit() and int(count) > 0):
                problems.append(line)
    if problems:
        return fail(f"landed {args.env}: " + " / ".join(problems))
    checked = f"・文字列 {len(greps)} 件" if greps else ""
    return ok(f"landed {args.env}: サーバー先端 = {TRACK[args.env]}{checked}")


def cmd_site(args: argparse.Namespace) -> int:
    if not 1 <= args.repeat <= 10:
        return fail("site: --repeat は 1..10")
    paths = dict(SITE_PATHS[args.env])
    if args.path:
        if not PATH_OK.match(args.path):
            return fail(f"site: --path の形式が不正(先頭 / の英数パスのみ): {args.path}")
        paths = {args.path: SITE_PATHS[args.env].get(args.path, 200)}
    auth = staging_auth() if args.env == "staging" else ""
    if args.env == "staging" and not auth:
        print(f"{Y}loadbalancer/.env に Basic 認証が無い(素の 401 が返る){Z}")

    bad = []
    for path, expect in paths.items():
        url = SITE[args.env] + path
        for i in range(args.repeat):
            head, body = fetch_head(url, auth, body=bool(args.contains))
            tag = f" try{i + 1}" if args.repeat > 1 else ""
            print(f"{path:<18}{head}{tag}" + (f"  (期待 {expect})" if expect != 200 else ""))
            if not head.startswith(f"HTTP {expect}"):
                bad.append(f"{path}={head.split()[1] if ' ' in head else head}(期待 {expect})")
        for needle in args.contains:
            found = needle in body
            print(f'{"":<18}contains "{needle}": {"yes" if found else "NO"}')
            if not found:
                bad.append(f'{path} contains "{needle}"')
    if bad:
        return fail(f"site {args.env}: " + " / ".join(bad))
    return ok(f"site {args.env}: {len(paths)} パス全て期待どおり" + (f"・文字列 {len(args.contains)} 件" if args.contains else ""))


def main() -> int:
    ap = argparse.ArgumentParser(prog="verify_deploy.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("preview", help="develop と production の差分(本番に何が出るか)")
    p.set_defaults(fn=cmd_preview)

    p = sub.add_parser("landed", help="サーバーの先端が追従先と一致するか + ファイル内文字列 + unit 起動時刻")
    p.add_argument("env", choices=ENVS)
    p.add_argument("--file", action="append", default=[], help=f"{REPO} 配下の相対パス(--contains とペアで繰り返し可)")
    p.add_argument("--contains", action="append", default=[], help="そのファイルに入っているはずの文字列")
    p.add_argument("--unit", default="uwsgi_thinkx", choices=UNITS, help="起動時刻を見る unit(既定 uwsgi_thinkx)")
    p.set_defaults(fn=cmd_landed)

    p = sub.add_parser("site", help="公開 URL の http code / 接続時間 / 合計 / 接続先 IP")
    p.add_argument("env", choices=ENVS)
    p.add_argument("--repeat", type=int, default=1, help="各 URL を測る回数 1..10(既定 1)")
    p.add_argument("--path", default="", help="既定の固定パス群の代わりに見るパス(先頭 / の英数パスのみ)")
    p.add_argument("--contains", action="append", default=[], help="本文にあるはずの文字列(繰り返し可)")
    p.set_defaults(fn=cmd_site)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        print(f"\n{Y}サブコマンドを指定してください(preview / landed / site)。{Z}")
        return 1
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
