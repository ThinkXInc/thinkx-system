#!/usr/bin/env python3
"""thinkx-system/hooks/suggest_wrapper.py   【Claude Code PreToolUse フック】

生の ssh / curl / nohup / python heredoc を見つけたら、一度だけ止めて
「既製の観測スクリプト(infra/scripts/README.md の一覧)を使えないか」を実行者に見せる。
harness(Claude Code)が Bash 実行の前に自動で呼ぶ。人間も LLM も直接は実行しない。
材料: docs/approval_cases_v2.md(wrapper・カタログ・CLAUDE.md の案内があっても
生コマンドが書かれ続けた実測 2026-10-02)。check_git_command.py と並ぶ 2 本目の hook。

大原則:
  - **deny はしない。承認も変えない。** 該当したら exit 2 で一度止め、stderr の案内を
    実行者(LLM)に届けるだけ。実行者は wrapper に切り替えるか、wrapper が合わなければ
    コマンド先頭に `NOWRAP=1 ` を付けて出し直す(このフックは素通しし、settings の
    ask / deny がそのまま効く = 従来の承認フロー)。
  - 迷ったら委ねる(exit 0・出力なし)。解析不能・例外も全て委ねる。
  - 対象パターンは README の一覧に対応する語だけ。広げるときは実例を貯めてから。

入力: stdin に PreToolUse の JSON(tool_name, tool_input.command)。
出力: 該当時のみ stderr に案内を書き exit 2。それ以外は出力なしで exit 0。
python3 標準ライブラリのみ。
"""
from __future__ import annotations

import json
import re
import shlex
import sys

# 先頭にこれが付いていたら素通し(wrapper が合わないときの逃げ道。承認フローは従来どおり)
BYPASS = "NOWRAP=1"

# 対象の語(コマンド位置のトークンとして現れたときだけ)と、対応する案内
HINTS = {
    "ssh":   "ssh の観測 → stg.py check/log/watch(staging)、verify_deploy.py landed(着地確認)",
    "curl":  "curl → verify_deploy.py site(公開 URL)、devserver.py get(手元 dev。--save で本文保存)",
    "nohup": "dev サーバーの起動・停止・再起動 → devserver.py start/stop/restart",
}

# python heredoc(ファイル編集の再発明)はトークンでなく形で見る
HEREDOC_RE = re.compile(r"\bpython3?\s+-\s*<<")

# これを含むコマンドは wrapper 自身の実行なので素通し
WRAPPER_PATH = "infra/scripts/"

OPERATORS = {"&&", "||", ";", "|", "&", "|&"}


def command_tokens(cmd: str) -> list[str]:
    """各サブコマンドの先頭(コマンド位置)トークンを集める。解析不能なら全トークン扱い。"""
    try:
        tokens = shlex.split(cmd, comments=False, posix=True)
    except ValueError:
        return re.findall(r"[A-Za-z0-9_./-]+", cmd)
    heads: list[str] = []
    at_head = True
    for tok in tokens:
        if tok in OPERATORS:
            at_head = True
            continue
        if at_head:
            # 環境変数代入(VAR=...)はコマンド位置を消費しない
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok):
                continue
            heads.append(tok)
            at_head = False
    return heads


def build_hints(cmd: str) -> list[str]:
    if cmd.strip().startswith(BYPASS) or WRAPPER_PATH in cmd:
        return []
    heads = {h.rsplit("/", 1)[-1] for h in command_tokens(cmd)}
    hints = [text for word, text in HINTS.items() if word in heads]
    if HEREDOC_RE.search(cmd):
        hints.append("python heredoc でのファイル書き換え → Edit ツール(承認なし・diff 可視)。読むのは Read ツール")
    return hints


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    cmd = str(data.get("tool_input", {}).get("command", ""))
    hints = build_hints(cmd)
    if not hints:
        return 0
    print("このコマンドには既製のスクリプトがあるかもしれません(正本: infra/scripts/README.md の一覧):",
          file=sys.stderr)
    for hint in hints:
        print(f"  - {hint}", file=sys.stderr)
    print("一覧に無い・wrapper が合わない場合は、同じコマンドの先頭に `NOWRAP=1 ` を付けて"
          "出し直すとこの案内は出ません(承認フローは従来どおり)。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # フックは絶対に落とさない。既定は委ねる
