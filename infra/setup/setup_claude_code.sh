# thinkx-system/infra/setup/setup_claude_code.sh
#
# サーバーに Claude Code を導入する(docs/サーバー編集のエージェント化計画.md v1.1)。
# 対象は staging の web のみ(prod には置かない・同計画 1章)。
# 前提:
#  - setup_webserver.sh 済み(node v18+ / tmux が入っている)
#  - 認証は本スクリプトでは行わない。初回に tmux 内で claude を起動して対話ログイン(オーナー)

echo "== setup_claude_code =="

sudo npm install -g @anthropic-ai/claude-code

# verify  (claude と tmux が使えること)
command -v claude > /dev/null && command -v tmux > /dev/null && printf '\033[32mOK: setup_claude_code claude=%s / tmux あり(初回は tmux 内で claude を起動して対話ログイン)\033[0m\n' "$(claude --version 2>/dev/null | head -1)" || printf '\033[31mFAIL: setup_claude_code claude=%s tmux=%s\033[0m\n' "$(command -v claude || echo なし)" "$(command -v tmux || echo なし)"
