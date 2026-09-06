# hooks — Claude Code フック(ワークスペース共通)

harness(Claude Code)が自動で呼ぶフック。人間も LLM も直接は実行しない。
`.claude/settings.json` の `hooks` に登録され、ツールのライフサイクルの各点で走る。
人間が意図して叩く ops スクリプト(`infra/scripts/`)とは別カテゴリ。terraform 専用の
コスト見積もり(`infra/scripts/cost-hook.sh`・PostToolUse)は infra スコープなので infra/ 側に置く。

## check_git_command.py 【PreToolUse】

Bash コマンドの直前に走り、そのコマンドを承認なしで通してよいか(安全な git か)だけを判定する。

- **allow を返す**: コマンドが git add / commit / push(非 force)**だけ**で構成されるとき。
- **委ねる(出力なし)**: それ以外。force / delete / mirror フラグ、`$(...)`・バッククォート・
  リダイレクト `>` `<`、解析不能、例外。**deny は返さない**(止めるのは settings の deny の役割)。
- deny(force push・reset --hard・clean・rm -rf・sudo・鍵/tfstate 等)は settings が止める。
  フックはその床の上で承認を足すだけ。deny と ask のルールはフックの allow より優先。
- 登録: `hooks.PreToolUse` に matcher `"Bash"`・`python3 "$CLAUDE_PROJECT_DIR/hooks/check_git_command.py"`。

なぜ git だけをフックにするか(curl/ssh は固定 wrapper、git add/WebFetch は settings):
判定の割り当ては `docs/approval_cases_v1.md`「判定方式の割り当て」。
設計・安全モデル・実行時の流れは `docs/DEPLOY_APPROVAL_LEVELS.md`。
