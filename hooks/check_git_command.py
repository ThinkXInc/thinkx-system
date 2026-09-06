#!/usr/bin/env python3
"""thinkx-system/hooks/check_git_command.py   【Claude Code PreToolUse フック】

Bash コマンドを検査し、安全な git 操作(add / commit / push 非 force)だけを無承認にする。
harness(Claude Code)が Bash 実行の前に自動で呼ぶ。人間も LLM も直接は実行しない。
承認削減 version 1。材料: docs/approval_cases_v1.md(事例 I)。判定基準・安全モデル: docs/DEPLOY_APPROVAL_LEVELS.md。

大原則(安全側に倒す):
  - allow を返すのは、コマンドが git add / commit / push(非 force)**のみ**で構成されているときだけ。
  - それ以外は何も出力せず終了(通常の許可フローに委ねる)。**deny は絶対に返さない**
    (このフックは承認を「足す」だけ。止めるのは settings の deny の仕事)。
  - deny ルール(force push / reset --hard / clean / rm -rf 等)はフックの allow より強い
    (Claude Code 仕様)。だからフックが緩めても危険な操作は止まったまま。
  - コマンド置換 `$(...)` / バッククォート / リダイレクト `>` `<` を含むものは allow しない
    (git add/commit に偽装した実行を通さないため。安全側 = 迷ったら委ねる)。
  - 解析不能・例外・想定外は全て「委ねる」(= 出力なしで exit 0)。既定は承認プロンプト。

version を増やすとき(安全と確認できてから)は ALLOWED を広げるのでなく、まず
docs/approval_cases_v2.md に実例を貯め、この scope を段階的に拡張する。想像で広げない。

入力: stdin に PreToolUse の JSON(tool_name, tool_input.command)。
出力: allow のときだけ hookSpecificOutput を stdout に。常に exit 0。
python3 標準ライブラリのみ。
"""
from __future__ import annotations

import json
import shlex
import sys

# version 1 の scope。非破壊・可逆で、かつ settings の ask ルールが無いもの
# (ask があるとフックの allow は仕様上上書きされるので、curl/ssh はここに入れられない。
#  curl/ssh の安全な観測は固定スクリプト python3 側で扱う)。
#   git add    : ステージング。可逆
#   git commit : ローカルコミット。可逆(複数行メッセージで allow が崩れる件の本命)
#   git push   : 非 force のみ(force/mirror/delete/prune は下の FORCE_FLAGS で弾く。force は deny も勝つ)
GIT_SAFE_SUBCMDS = {"add", "commit", "push"}

# push で許さないフラグ(破壊・巻き戻し)。1 つでもあれば委ねる。
FORCE_FLAGS = {"--force", "-f", "--force-with-lease", "--force-if-includes",
               "--mirror", "--delete", "--prune"}

# コマンド置換・リダイレクトを含むものは委ねる(偽装実行を通さない)
UNSAFE_MARKERS = ("$(", "`", ">", "<")

# サブコマンドの区切り(Claude Code が認識するのと同じ集合)
OPERATORS = {"&&", "||", ";", "|", "&", "|&"}


def segment_is_safe(seg: list[str]) -> bool:
    """1 サブコマンドが安全な git 操作か。"""
    if len(seg) < 2 or seg[0] != "git":
        return False
    sub = seg[1]
    if sub not in GIT_SAFE_SUBCMDS:
        return False
    if sub == "push" and any(tok in FORCE_FLAGS for tok in seg[2:]):
        return False
    return True


def decision_allow(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }))


def command_is_safe_git(cmd: str) -> bool:
    if not cmd.strip():
        return False
    if any(m in cmd for m in UNSAFE_MARKERS):
        return False
    try:
        tokens = shlex.split(cmd, comments=False, posix=True)
    except ValueError:
        return False  # 引用符が閉じない等 → 委ねる

    # 演算子トークンでサブコマンドに割る(引用内の改行は 1 トークンに残るので割れない)
    segments: list[list[str]] = []
    current: list[str] = []
    for tok in tokens:
        if tok in OPERATORS:
            segments.append(current)
            current = []
        else:
            current.append(tok)
    segments.append(current)

    non_empty = [seg for seg in segments if seg]
    if not non_empty:
        return False
    return all(segment_is_safe(seg) for seg in non_empty)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0  # 入力が読めない → 委ねる
    if data.get("tool_name") != "Bash":
        return 0
    cmd = str(data.get("tool_input", {}).get("command", ""))
    if command_is_safe_git(cmd):
        decision_allow("git add / commit / push(非 force)のみ。非破壊・可逆。承認削減 v1")
    return 0  # allow でも defer でも常に 0(exit 2 はブロックになるので使わない)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # フックは絶対に落とさない。既定は委ねる
