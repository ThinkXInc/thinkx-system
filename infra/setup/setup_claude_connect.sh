# thinkx-system/infra/setup/setup_claude_connect.sh   【分類: 変更系(unit の設置・起動)】
#
# Claude 接続ページ(infra/claude_connect)を staging の web に常駐させる。
# 対象は staging の web のみ(prod には置かない — infra/docs/CLAUDE_CONNECT_PLAN.md 大原則1)。
# 前提:
#  - setup_claude_code.sh 済み(claude と tmux が入っている・claude-session.service が enable 済み)
#  - clone_monorepo.sh 済み(/src/thinkx-system に infra/claude_connect がある)
#  - 認証は本スクリプトでは行わない(要ログインになったらページから行う)
# 使い方: ssh <web-stg> 'bash -s' < infra/setup/setup_claude_connect.sh

echo "== setup_claude_connect =="

sudo ln -sf /src/thinkx-system/infra/claude_connect/claude_connect.service /etc/systemd/system/claude_connect.service
sudo systemctl daemon-reload
sudo systemctl enable claude_connect
sudo systemctl restart claude_connect

sleep 2

systemctl is-enabled claude_connect
systemctl is-active claude_connect
sudo journalctl -u claude_connect -n 5 --no-pager

# verify  (private IP:8008 の /connect/state が state を返すこと)
STATE="$(curl -s -m 30 "http://$(hostname -I | awk '{print $1}'):8008/connect/state" | head -1)"
[ -n "$STATE" ] && systemctl is-active claude_connect > /dev/null && printf '\033[32mOK: setup_claude_connect %s\033[0m\n' "$STATE" || printf '\033[31mFAIL: setup_claude_connect state=%s active=%s\033[0m\n' "${STATE:-取得不可}" "$(systemctl is-active claude_connect)"
