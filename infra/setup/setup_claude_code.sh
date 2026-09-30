# thinkx-system/infra/setup/setup_claude_code.sh
#
# サーバーに Claude Code を導入する(docs/サーバー編集のエージェント化計画.md v1.1)。
# 対象は staging の web のみ(prod には置かない・同計画 1章)。
# 前提:
#  - setup_webserver.sh 済み(tmux が入っている)
#  - 認証は本スクリプトでは行わない。初回に tmux 内で claude を起動して対話ログイン(オーナー)
# 注1: 導入は kaz の native installer(~/.local/bin/claude・自動更新あり)。npm 方式は使わない —
#      postinstall 不発で実体が壊れる事故が 2 回起きた(findings 2026-09-28 / 2026-10-01・D-83)。
#      sudo なしで `claude update` がセッション内から完結する(オーナー指示 2026-09-28)。
# 注2: PATH は .bashrc の先頭(非対話ガードより前)に置く。.profile は Ubuntu 標準の
#      ~/.local/bin ブロックが効く。systemd から使う分は unit 側の Environment=PATH が正

echo "== setup_claude_code =="

sudo -u kaz -H bash -c 'curl -fsSL https://claude.ai/install.sh | bash'
sudo -u kaz -H sed -i '1i export PATH=/home/kaz/.local/bin:$PATH' /home/kaz/.bashrc

# 起動時に tmux + claude を自動で立てる(停止で tmux は消えるが認証 /home/kaz/.claude は残る)
# claude は systemd の既定 PATH に無いため、unit 側の Environment=PATH に ~/.local/bin を含めてある
sudo ln -sf /src/thinkx-system/infra/setup/claude-session.service /etc/systemd/system/claude-session.service
sudo systemctl daemon-reload
sudo systemctl enable claude-session

# verify  (バージョンが取れること = 実体まで入っていること。kaz のログインシェルで引く)
CV="$(sudo -u kaz -H bash -lc 'claude --version' 2>/dev/null | head -1)"
[ -n "$CV" ] && command -v tmux > /dev/null && printf '\033[32mOK: setup_claude_code claude %s / tmux あり(初回は tmux 内で claude を起動して対話ログイン)\033[0m\n' "$CV" || printf '\033[31mFAIL: setup_claude_code claude --version=%s tmux=%s\033[0m\n' "${CV:-取得不可}" "$(command -v tmux || echo なし)"
