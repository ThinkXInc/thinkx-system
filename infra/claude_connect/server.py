#!/usr/bin/env python3
"""thinkx-system/infra/claude_connect/server.py

staging の Claude Code 常駐セッション(tmux `claude`・claude-session.service)の状態を返し、
スマホのブラウザからの再接続とログインコードの転送を行う。python3 標準ライブラリのみ。
kaz で動かす(tmux も claude も kaz のもの)。bind は web の private IP:8008。LB 以外から
届かないことは SG(8000〜8009 を LB SG からのみ許可)が保証する。

  GET  /connect/         画面(同じディレクトリの index.html)
  GET  /connect/state    {"state", "url", "disk_free_gb", "observed_at"}
  POST /connect/session  state に応じて再接続し、動作後の {"state", "url"} を返す
  POST /connect/code     body {"code"} を pane に貼って Enter。動作後の {"state", "url"} を返す
  GET  /connect/deploy   本番に出る内容(コミット一覧・再起動されるサービス)。何も変えない
  POST /connect/deploy   origin/develop から release を切って production へ push(押す=承認)。本番の応答を確認して返す

state:
  connected        tmux あり・pane が claude・ログイン済み
  session_missing  tmux セッション `claude` が無い
  login_required   ログアウトしている(claude が居ない場合も含む)、または claude がログイン画面を出している
  unknown          上のどれでもない(ログイン済みなのに claude が落ちて shell に戻っている等)

画面の文言は 2026-09-04 に Claude Code 2.1.223 で実測したもの(infra/findings.md)。推測で足さない。
認証情報(トークン・コード)はログに出さない。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SESSION = "claude"
REPO = "/src/thinkx-system"
CLAUDE_COMMAND = "claude --remote-control"  # claude-session.service の ExecStart と同じ
PORT = 8008
INDEX_HTML = Path(__file__).with_name("index.html")

# 実測した文言(2.1.223)。部分一致で緩く見る。
URL_HEADER = "Use the url below"
CODE_PROMPT = "Paste code here"
ENTER_PROMPTS = ("Choose the text style", "Select login method", "Press Enter to continue")
CONNECTED_MARK = "/remote-control is active"

CODE_PATTERN = re.compile(r"^[A-Za-z0-9#_\-]{1,512}$")
STEP_WAIT_SECONDS = 1.5
MAX_STEPS = 12

action_lock = threading.Lock()

# 操作中にサーバーが「いま何をしているか」。画面はこれを 1 秒ごとに読んで段階表示にする。
# phase: idle / starting_session / first_run / url_ready / sending_code / waiting_code /
#        security_notes / starting / connected
progress = {"phase": "idle", "since": None}


def set_phase(phase: str) -> None:
    if progress["phase"] != phase:
        progress["phase"] = phase
        progress["since"] = time.time()


def phase_from_screen(lines: list[str]) -> str:
    if screen_has(lines, CONNECTED_MARK):
        return "connected"
    if screen_has(lines, "Press Enter to continue"):
        return "security_notes"
    if screen_has(lines, CODE_PROMPT):
        return "waiting_code"
    if screen_has(lines, "Choose the text style", "Select login method"):
        return "first_run"
    return "starting"


def run(args: list[str], timeout: int = 20) -> tuple[int, str]:
    """外部コマンドを引数リストで実行し、(戻り値, 標準出力) を返す。shell は使わない。"""
    try:
        done = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=REPO)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)
    return done.returncode, done.stdout


def tmux(*args: str) -> tuple[int, str]:
    return run(["tmux", *args])


def has_session() -> bool:
    return tmux("has-session", "-t", SESSION)[0] == 0


def pane_command() -> str:
    rc, out = tmux("list-panes", "-t", SESSION, "-F", "#{pane_current_command}")
    return out.strip().splitlines()[0].strip() if rc == 0 and out.strip() else ""


def screen_lines() -> list[str]:
    rc, out = tmux("capture-pane", "-p", "-t", SESSION)
    return [line.rstrip() for line in out.splitlines()] if rc == 0 else []


login_cache = {"at": 0.0, "value": False}
LOGIN_CACHE_SECONDS = 3.0


def is_logged_in() -> bool:
    """`claude auth status` は node の起動を伴い重い(5 秒ごとの状態取得で CPU の 1 割を食った・実測)。
    数秒だけ結果を使い回す。操作の直後は set_phase 側で呼び直されるので鮮度は足りる。"""
    if time.time() - login_cache["at"] < LOGIN_CACHE_SECONDS:
        return login_cache["value"]
    rc, out = run(["claude", "auth", "status", "--json"])
    value = False
    if rc == 0:
        try:
            value = bool(json.loads(out).get("loggedIn"))
        except ValueError:
            value = False
    login_cache["at"] = time.time()
    login_cache["value"] = value
    return value


def find_url(lines: list[str]) -> str | None:
    """行頭が http の行から「Paste code here」の手前までを繋いで URL にする。

    URL は TUI が pane 幅で複数行に折って描く(ハード改行。capture-pane -J でも 1 行に戻らない)。
    文言行(「Use the url below」「Paste code here」)は行頭に空白があり、URL の各行には無い。
    見出し行は pane が低い(80x24)と画面外に出ることがあるので当てにしない。
    """
    for i, line in enumerate(lines):
        if not line.startswith("http"):
            continue
        pieces = []
        for follow in lines[i:]:
            if CODE_PROMPT in follow or not follow or follow.startswith(" "):
                break
            pieces.append(follow.strip())
        url = "".join(pieces)
        return url if "://" in url else None
    return None


def screen_has(lines: list[str], *needles: str) -> bool:
    return any(needle in line for line in lines for needle in needles)


# 接続中の画面に出る「/remote-control is active · … https://claude.ai/code/session_…」の URL。
# 会話が進むと画面外に流れるので、見えたときに覚えておき、セッションを作り直したら忘れる。
SESSION_URL_PREFIX = "https://claude.ai/code/session_"
remembered = {"session_url": None}


def find_session_url(lines: list[str]) -> str | None:
    for line in lines:
        for token in line.split():
            if token.startswith(SESSION_URL_PREFIX):
                return token
    return None


def session_url(lines: list[str]) -> str | None:
    seen = find_session_url(lines)
    if seen:
        remembered["session_url"] = seen
    return remembered["session_url"]


def disk_free_gb() -> int:
    return shutil.disk_usage("/").free // (1024 ** 3)


def observe() -> dict:
    if not has_session():
        return {"state": "session_missing", "url": None}

    command = pane_command()
    lines = screen_lines()
    url = find_url(lines)

    if command == "claude":
        if url or screen_has(lines, CODE_PROMPT, *ENTER_PROMPTS):
            return {"state": "login_required", "url": url}
        if is_logged_in():
            return {"state": "connected", "url": None, "session_url": session_url(lines)}
        return {"state": "login_required", "url": None}

    if is_logged_in():
        return {"state": "unknown", "url": None}
    return {"state": "login_required", "url": None}


def start_session() -> None:
    """claude-session.service の ExecStart と同じ形で tmux を立てる。"""
    remembered["session_url"] = None
    tmux("new-session", "-d", "-s", SESSION, "-c", REPO, CLAUDE_COMMAND)


def restart_session() -> None:
    tmux("kill-session", "-t", SESSION)
    start_session()


def press_enter() -> None:
    tmux("send-keys", "-t", SESSION, "Enter")


def walk_login_prompts() -> dict:
    """初回対話(theme → login method → URL)を Enter で進め、URL が出るか接続中になるまで待つ。"""
    asked_login = False
    for _ in range(MAX_STEPS):
        time.sleep(STEP_WAIT_SECONDS)
        lines = screen_lines()
        url = find_url(lines)
        set_phase("url_ready" if url else phase_from_screen(lines))
        if url:
            return {"state": "login_required", "url": url}
        if screen_has(lines, CONNECTED_MARK):
            return {"state": "connected", "url": None, "session_url": session_url(lines)}
        if screen_has(lines, *ENTER_PROMPTS):
            press_enter()
            continue
        if screen_has(lines, CODE_PROMPT):
            continue  # コード待ち。URL が画面外なら人間が pane で見る(runbook)
        if pane_command() == "claude" and not is_logged_in() and not asked_login:
            tmux("send-keys", "-t", SESSION, "-l", "/login")
            press_enter()
            asked_login = True
    return observe()


def reconnect() -> dict:
    current = observe()
    state = current["state"]

    try:
        if state == "connected":
            return current
        set_phase("starting_session")
        if state == "session_missing":
            start_session()
        elif state == "unknown":
            restart_session()
        elif state == "login_required":
            if current["url"]:
                return current
            if pane_command() != "claude":
                restart_session()

        return walk_login_prompts()
    finally:
        set_phase("idle")


def paste_code(code: str) -> dict:
    if not has_session() or pane_command() != "claude":
        raise LookupError("claude が動いていません。先に「セッションを再接続」を押してください")
    if not screen_has(screen_lines(), CODE_PROMPT):
        raise LookupError("コードの入力待ちではありません。先に「セッションを再接続」を押してください")

    try:
        set_phase("sending_code")
        tmux("send-keys", "-t", SESSION, "-l", code)
        press_enter()
        return walk_login_prompts()
    finally:
        set_phase("idle")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---- 本番への反映(押す=承認・オーナー指示 2026-09-06) --------------------------------------
# infra/scripts/deploy_production_from_staging.sh の git 部分と同じことを staging 上で行う。
# origin/develop(= staging で見えている内容)から release/<日付> を切って push し、production へ
# fast-forward で push する。取り込みは本番の deploy-timer(60 秒ごと・sync_from_origin.sh prod)。
# PR は作らない(staging に gh が無く、production に branch protection も無い)。
# git 管理外のアセット(views/video)はここでは出ない(staging から本番 web へ届かない)。
# 作業ツリーには触れない(fetch と plumbing と push だけ。checkout は clean のまま — D-58/D-60)。

PRODUCTION_URL = "https://thinkxinc.com/"
PRODUCTION_WAIT_SECONDS = 75
SERVICE_BY_PREFIX = (("thinkx/", "thinkx"), ("transformism/", "transformism"), ("kazukiotsukacom/", "kazukiotsukacom"),
                     ("nginx-web-root/", "nginx"), ("loadbalancer/", "nginx"), ("podcast/", "podcast"))


def git(*args: str, timeout: int = 60) -> tuple[int, str]:
    return run(["git", "-C", REPO, *args], timeout=timeout)


def git_out(*args: str) -> str:
    rc, out = git(*args)
    if rc != 0:
        raise RuntimeError(f"git {' '.join(args)} が失敗: {out.strip()[:200]}")
    return out.strip()


def services_for(paths: list[str]) -> list[str]:
    found: list[str] = []
    for path in paths:
        for prefix, service in SERVICE_BY_PREFIX:
            if path.startswith(prefix) and service not in found:
                found.append(service)
    return found


def deploy_preview() -> dict:
    """本番に出る内容(コミット一覧と再起動されるサービス)。何も変えない。"""
    git_out("fetch", "--quiet", "origin")
    sha = git_out("rev-parse", "origin/develop")
    prod = git_out("rev-parse", "origin/production")
    same = git_out("rev-parse", f"{sha}^{{tree}}") == git_out("rev-parse", f"{prod}^{{tree}}")
    commits = [] if same else [line for line in git_out("log", "--oneline", "--no-merges", f"{prod}..{sha}").splitlines() if line]
    paths = [] if same else [line for line in git_out("diff", "--name-only", prod, sha).splitlines() if line]
    return {"same": same, "sha": sha, "production_sha": prod, "commits": commits, "services": services_for(paths)}


def next_release_name() -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    name, n = f"release/{day}", 2
    while git("rev-parse", "--verify", "--quiet", f"origin/{name}")[0] == 0:
        name = f"release/{day}-{n}"
        n += 1
    return name


def production_http_status() -> int:
    rc, out = run(["curl", "-s", "-o", "/dev/null", "-m", "15", "-w", "%{http_code}", PRODUCTION_URL], timeout=20)
    return int(out) if rc == 0 and out.strip().isdigit() else 0


def deploy_to_production() -> dict:
    try:
        set_phase("deploy_fetch")
        preview = deploy_preview()
        if preview["same"]:
            return {"result": "already", **preview, "production_url": PRODUCTION_URL}

        sha, prod = preview["sha"], preview["production_sha"]
        set_phase("deploy_release")
        release = next_release_name()
        rel = sha
        if git("merge-base", "--is-ancestor", prod, sha)[0] != 0:
            # release が squash merge されると production の履歴が develop から切れる。production を第2親に
            # 持つ merge commit を release の先頭に置いて繋ぐ(tree は sha と同一。deploy_production_from_staging.sh と同じ)
            rel = git_out("commit-tree", f"{sha}^{{tree}}", "-p", sha, "-p", prod,
                          "-m", f"release: production の履歴を繋ぐ(tree は origin/develop {sha} と同一)")
        git_out("push", "--quiet", "origin", f"{rel}:refs/heads/{release}")

        set_phase("deploy_push")
        git_out("push", "--quiet", "origin", f"{rel}:production")

        set_phase("deploy_wait")
        time.sleep(PRODUCTION_WAIT_SECONDS)

        set_phase("deploy_check")
        status = production_http_status()
        return {"result": "deployed", **preview, "release": release, "release_sha": rel,
                "production_http": status, "production_url": PRODUCTION_URL}
    finally:
        set_phase("idle")


class Handler(BaseHTTPRequestHandler):
    server_version = "claude_connect/1"

    def log_message(self, fmt: str, *args) -> None:  # 既定の request line ログを path だけにする(body・query を出さない)
        print(f"{now_iso()} {self.command} {self.path.split('?')[0]}", flush=True)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_index(self) -> None:
        if not INDEX_HTML.exists():
            self.send_json(404, {"error": "index.html がありません"})
            return
        body = INDEX_HTML.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw or b"{}")
        except ValueError as e:
            raise ValueError("body が JSON ではありません") from e
        if not isinstance(data, dict):
            raise ValueError("body は JSON オブジェクトにしてください")
        return data

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        try:
            if path == "/connect":
                self.send_response(301)
                self.send_header("Location", "/connect/")
                self.end_headers()
            elif path == "/connect/":
                self.send_index()
            elif path == "/connect/state":
                self.send_json(200, {**observe(), "phase": progress["phase"], "disk_free_gb": disk_free_gb(), "observed_at": now_iso()})
            elif path == "/connect/deploy":
                self.send_json(200, {**deploy_preview(), "observed_at": now_iso()})
            else:
                self.send_json(404, {"error": "not found"})
        except Exception as e:  # ハンドラで落とさない
            self.send_json(500, {"error": f"{type(e).__name__}: {e}"})

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
        try:
            if path == "/connect/session":
                with action_lock:
                    result = reconnect()
                self.send_json(200, {**result, "observed_at": now_iso()})
            elif path == "/connect/code":
                code = str(self.read_json_body().get("code", "")).strip()
                if not CODE_PATTERN.match(code) or code.startswith("-"):
                    self.send_json(400, {"error": "コードの形式が違います。認証後に表示された文字列をそのまま貼ってください"})
                    return
                with action_lock:
                    result = paste_code(code)
                self.send_json(200, {**result, "observed_at": now_iso()})
            elif path == "/connect/deploy":
                if not action_lock.acquire(blocking=False):
                    self.send_json(409, {"error": "別の操作が進行中です。終わってからもう一度押してください"})
                    return
                try:
                    result = deploy_to_production()
                finally:
                    action_lock.release()
                self.send_json(200, {**result, "observed_at": now_iso()})
            else:
                self.send_json(404, {"error": "not found"})
        except ValueError as e:
            self.send_json(400, {"error": str(e)})
        except LookupError as e:
            self.send_json(409, {"error": str(e)})
        except Exception as e:  # ハンドラで落とさない
            self.send_json(500, {"error": f"{type(e).__name__}: {e}"})


def private_ip() -> str:
    rc, out = run(["hostname", "-I"])
    if rc != 0 or not out.split():
        raise OSError("hostname -I で private IP が取れません")
    return out.split()[0]


def main() -> None:
    address = (private_ip(), PORT)
    print(f"{now_iso()} claude_connect listening on {address[0]}:{address[1]}", flush=True)
    ThreadingHTTPServer(address, Handler).serve_forever()


if __name__ == "__main__":
    main()
