# thinkx-system/infra/setup/setup_claude_code.sh
#
# サーバーに Claude Code を導入する(docs/サーバー編集のエージェント化計画.md v1.1)。
# 対象は staging の web のみ(prod には置かない・同計画 1章)。
# 前提:
#  - setup_webserver.sh 済み(node v18+ / tmux / kaz の npm prefix=~/.npm-global と PATH が入っている)
#  - 認証は本スクリプトでは行わない。初回に tmux 内で claude を起動して対話ログイン(オーナー)
# 注1: install は kaz のユーザー配下(~/.npm-global)のみ。root(/usr/local)に入れない —
#      `claude update` が sudo なしでセッション内から完結する状態を保つ(オーナー指示 2026-09-28)。
#      root と user の二重 install は PATH の前後で版ずれを起こす(2026-09-28 実測)。
# 注2: この npm は allowScripts 既定ブロックのため、postinstall(本体バイナリ取得)の許可指定が必須。
#      update 後に `claude native binary not installed` になったら postinstall 不発 —
#      node ~/.npm-global/lib/node_modules/@anthropic-ai/claude-code/install.cjs で直る。

echo "== setup_claude_code =="

sudo -u kaz -H npm install -g --allow-scripts=@anthropic-ai/claude-code @anthropic-ai/claude-code

# 起動時に tmux + claude を自動で立てる(停止で tmux は消えるが認証 /home/kaz/.claude は残る)
# claude は systemd の既定 PATH に無いため、unit 側の Environment=PATH に ~/.npm-global/bin を含めてある
sudo ln -sf /src/thinkx-system/infra/setup/claude-session.service /etc/systemd/system/claude-session.service
sudo systemctl daemon-reload
sudo systemctl enable claude-session

# verify  (存在でなくバージョンが取れること = 本体バイナリまで入っていること。kaz のログインシェルで引く)
CV="$(sudo -u kaz -H bash -lc 'claude --version' 2>/dev/null | head -1)"
[ -n "$CV" ] && command -v tmux > /dev/null && printf '\033[32mOK: setup_claude_code claude %s / tmux あり(初回は tmux 内で claude を起動して対話ログイン)\033[0m\n' "$CV" || printf '\033[31mFAIL: setup_claude_code claude --version=%s tmux=%s\033[0m\n' "${CV:-取得不可}" "$(command -v tmux || echo なし)"
