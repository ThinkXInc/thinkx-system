# thinkx-system/infra/setup/setup_filedrop.sh
#
# filedrop(ブラウザのドラッグ&ドロップで素材を /src/thinkx-system/Downloads に受ける)を導入する。
# 対象は staging の web のみ。入口は https://staging.thinkxinc.com/filedrop/(LB の basic auth 配下)。
# 前提: clone_monorepo.sh 済み

echo "== setup_filedrop =="

sudo -u kaz git -C /src/thinkx-system pull --ff-only
sudo -u kaz mkdir -p /src/thinkx-system/Downloads
sudo ln -sf /src/thinkx-system/infra/filedrop/filedrop.service /etc/systemd/system/filedrop.service
sudo systemctl daemon-reload
sudo systemctl enable filedrop
sudo systemctl restart filedrop
sleep 1

# verify  (8008 が実際に応答すること)
[ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:8008/)" = 200 ] && printf '\033[32mOK: setup_filedrop 8008 応答(入口は https://staging.thinkxinc.com/filedrop/)\033[0m\n' || printf '\033[31mFAIL: setup_filedrop 8008 が応答しない(systemctl status filedrop / journalctl -u filedrop)\033[0m\n'
