#!/usr/bin/env python3
"""thinkx-system/infra/scripts/devserver.py   【分類: 観測系 + ローカル dev のプロセス管理(可逆)】

手元の開発サーバーの起動・停止・応答確認を 1 本に畳む。
承認プロンプト(settings の ask: curl 前置一致、引き金不明のローカル操作)に掛からない
固定コマンド列として置く。材料: docs/approval_cases_v2.md(dev サーバー停止・起動 6 回・
localhost GET 9 回で昇格。M/V/AH/AL/AM/AO)。

  python3 infra/scripts/devserver.py status <name>             listener と / の http code
  python3 infra/scripts/devserver.py start <name>              起動 + 応答が返るまで待つ(居たら何もしない)
  python3 infra/scripts/devserver.py stop <name>               そのポートの python だけ止める
  python3 infra/scripts/devserver.py restart <name>            stop → start
  python3 infra/scripts/devserver.py get <name> <path> [--contains S]... [--save] [--repeat N]
                                                               GET の code(+本文の文字列有無 / 本文の保存)

大原則:
  - 対象サーバーは下の SERVERS の固定集合のみ。任意ホスト・任意コマンド・任意 PID は受けない。
  - GET のみ。POST は持たない(dev のデータを変える操作は承認を残す — 事例 AN)。
  - stop はポートの listener のうち**プロセス名に python を含むものだけ**に TERM を送る。
    macOS は AirPlay が :5000 に居るため、ポートだけで kill すると system プロセスを巻き込む。
  - 本文の分析は抱え込まない。--save で保存した先を Read / Grep ツールで見る(事例 AM 再発の方針)。
  - ログは /tmp/devserver-<name>.log(セッションをまたいで同じ場所・リポジトリを汚さない)。
python3 標準ライブラリのみ(接続先は http://127.0.0.1 固定なので CA 問題なし)。戻り値 0/1。
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

# ---- 定数(固定集合。増やすときはここに足す = レビューされる) ----
WS = pathlib.Path(__file__).resolve().parents[2]
SERVERS = {
    # name: (port, 起動 cwd(WS 相対), 起動コマンド, 追加環境変数)
    "podcast":  (8010, "podcast/web-server", ("venv/bin/python", "main.py"), {}),
    "podcast2": (8012, "podcast/web-server", ("venv/bin/python", "main.py"), {"PORT": "8012"}),
    "thinkx":   (5000, "thinkx/web-server",  ("venv/bin/python", "main.py"), {}),
}
PATH_OK = re.compile(r"^/[A-Za-z0-9._/%?&=+-]*$")   # クエリ込みの GET パス。空白・引用符・# は拒否
WAIT_TRIES, WAIT_INTERVAL = 30, 0.5

G, R, Y, Z = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)
    return done.returncode, done.stdout + done.stderr


def ok(msg: str) -> int:
    print(f"{G}OK: {msg}{Z}")
    return 0


def fail(msg: str) -> int:
    print(f"{R}FAIL: {msg}{Z}")
    return 1


def log_path(name: str) -> pathlib.Path:
    return pathlib.Path(tempfile.gettempdir()) / f"devserver-{name}.log"


def listeners(port: int) -> list[tuple[int, str]]:
    """port を LISTEN している (pid, プロセス名) の一覧。"""
    rc, out = run(["lsof", "-nP", "-ti", f":{port}", "-sTCP:LISTEN"])
    pids = [int(p) for p in out.split() if p.strip().isdigit()]
    result = []
    for pid in pids:
        _, comm = run(["ps", "-o", "comm=", "-p", str(pid)])
        result.append((pid, comm.strip()))
    return result


def http_get(port: int, path: str, want_body: bool) -> tuple[str, str]:
    """(code または ERR 表示, 本文) を返す。接続先は 127.0.0.1 固定。"""
    url = f"http://127.0.0.1:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as res:
            return str(res.status), res.read().decode("utf-8", "replace") if want_body else ""
    except urllib.error.HTTPError as e:
        return str(e.code), e.read().decode("utf-8", "replace") if want_body else ""
    except OSError as e:
        return f"ERR({e})", ""


def python_pids(port: int) -> list[int]:
    return [pid for pid, comm in listeners(port) if "python" in comm.lower()]


def wait_ready(port: int) -> str:
    """python の listener が現れて GET が返るまで待つ。
    AirPlay(ControlCenter)が :5000 で先に 403 を返すため、応答だけでは readiness にならない。"""
    for _ in range(WAIT_TRIES):
        if python_pids(port):
            code, _ = http_get(port, "/", want_body=False)
            if not code.startswith("ERR"):
                return code
        time.sleep(WAIT_INTERVAL)
    return "unreachable"


def show_status(name: str) -> tuple[bool, str]:
    port = SERVERS[name][0]
    procs = listeners(port)
    for pid, comm in procs:
        mark = "" if "python" in comm.lower() else f" {Y}(python でない — 対象外){Z}"
        print(f":{port} pid={pid} {comm}{mark}")
    code, _ = http_get(port, "/", want_body=False)
    print(f"GET http://127.0.0.1:{port}/ -> {code}")
    return bool(python_pids(port)), code


# ---- サブコマンド ----
def cmd_status(args: argparse.Namespace) -> int:
    listening, code = show_status(args.name)
    if listening and not code.startswith("ERR"):
        return ok(f"{args.name} 稼働中(:{SERVERS[args.name][0]} -> {code})")
    return fail(f"{args.name} 未起動(python の listener なし)" if not listening
                else f"{args.name} listener はあるが応答なし({code})")


def cmd_stop(args: argparse.Namespace) -> int:
    import os
    import signal
    port = SERVERS[args.name][0]
    stopped, skipped = [], []
    for pid, comm in listeners(port):
        if "python" not in comm.lower():
            skipped.append(f"{pid}({comm.rsplit('/', 1)[-1]})")
            continue
        # Flask debug の自動リロードは親子 2 プロセスで、子(listener)だけ殺すと親が蘇らせる。
        # グループごと TERM し、取れないときだけ単体 kill に落とす。
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            run(["kill", str(pid)])
        stopped.append(pid)
    if skipped:
        print(f"{Y}python でない listener はそのまま: {' '.join(skipped)}{Z}")
    if not stopped:
        return ok(f"{args.name} 止める対象なし(:{port} に python の listener なし)")
    time.sleep(1)
    remain = python_pids(port)
    if remain:
        return fail(f"{args.name} stop 後も残存 pid={remain}")
    return ok(f"{args.name} 停止(pid {' '.join(map(str, stopped))})")


def cmd_start(args: argparse.Namespace) -> int:
    port, cwd, cmd, env_add = SERVERS[args.name]
    if python_pids(port):
        code = wait_ready(port)
        return ok(f"{args.name} は既に稼働中(:{port} -> {code}。再起動は restart)")
    import os
    log = log_path(args.name)
    with open(log, "ab") as f:
        subprocess.Popen(list(cmd), cwd=str(WS / cwd), stdout=f, stderr=f,
                         env={**os.environ, **env_add}, start_new_session=True)
    code = wait_ready(port)
    if code == "unreachable":
        _, tail = run(["tail", "-5", str(log)])
        print(tail.strip())
        return fail(f"{args.name} 起動したが {WAIT_TRIES * WAIT_INTERVAL:.0f} 秒応答なし(ログ {log})")
    return ok(f"{args.name} 起動(:{port} -> {code}。ログ {log})")


def cmd_restart(args: argparse.Namespace) -> int:
    if cmd_stop(args) != 0:
        return 1
    return cmd_start(args)


def cmd_get(args: argparse.Namespace) -> int:
    if not PATH_OK.match(args.path):
        return fail(f"get: パスの形式が不正(先頭 / ・空白や引用符は不可): {args.path}")
    if not 1 <= args.repeat <= 10:
        return fail("get: --repeat は 1..10")
    port = SERVERS[args.name][0]
    want_body = bool(args.contains or args.save)

    bad = []
    body = ""
    for i in range(args.repeat):
        code, body = http_get(port, args.path, want_body)
        tag = f" try{i + 1}" if args.repeat > 1 else ""
        print(f"GET :{port}{args.path} -> {code}{tag}")
        if code.startswith("ERR") or code.startswith("5"):
            bad.append(code)
    for needle in args.contains:
        count = body.count(needle)
        print(f'contains "{needle}": {count} 箇所')
        if count == 0:
            bad.append(f'contains "{needle}"=0')
    if args.save:
        saved = pathlib.Path(tempfile.gettempdir()) / f"devserver-{args.name}-get.html"
        saved.write_text(body, encoding="utf-8")
        print(f"本文を保存: {saved}(Read / Grep ツールで見る)")
    if bad:
        return fail(f"get {args.name}: " + " / ".join(bad))
    return ok(f"get {args.name}{args.path}" + (f"・文字列 {len(args.contains)} 件" if args.contains else ""))


def main() -> int:
    ap = argparse.ArgumentParser(prog="devserver.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    for sub_name, fn, extra in (
            ("status", cmd_status, False), ("start", cmd_start, False),
            ("stop", cmd_stop, False), ("restart", cmd_restart, False), ("get", cmd_get, True)):
        p = sub.add_parser(sub_name)
        p.add_argument("name", choices=sorted(SERVERS))
        if extra:
            p.add_argument("path", help="GET するパス(クエリ可。例 /clip_videos?id=...)")
            p.add_argument("--contains", action="append", default=[], help="本文にあるはずの文字列(繰り返し可)")
            p.add_argument("--save", action="store_true", help="本文を /tmp に保存して Read/Grep で見る")
            p.add_argument("--repeat", type=int, default=1, help="回数 1..10(既定 1)")
        p.set_defaults(fn=fn)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        print(f"\n{Y}サブコマンドを指定してください(status / start / stop / restart / get)。{Z}")
        return 1
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
