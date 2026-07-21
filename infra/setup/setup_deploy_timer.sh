# setup deploy timer (pull 型・60秒ごとに origin を反映)
#
#  前提: clone_monorepo.sh 済み / push_discord_webhook.sh で webhook 配布済み(任意)
#  使い方: ENVX=staging bash setup_deploy_timer.sh
#          ENVX=prod    bash setup_deploy_timer.sh
#
#  staging は origin/develop を、prod は origin/production を追う。
#  sync_from_origin.sh は /usr/local/bin へ複製する(git が実行中のスクリプトを書き換えないため)。

echo "== deploy timer: ENVX=$ENVX =="

sudo install -m 0755 /src/thinkx-system/infra/run/sync_from_origin.sh /usr/local/bin/sync_from_origin.sh

sudo ln -sf /src/thinkx-system/infra/setup/deploy-timer@.service /etc/systemd/system/deploy-timer@.service
sudo ln -sf /src/thinkx-system/infra/setup/deploy-timer@.timer /etc/systemd/system/deploy-timer@.timer

sudo systemctl daemon-reload
sudo systemctl enable --now "deploy-timer@$ENVX.timer"

sleep 2

systemctl is-enabled "deploy-timer@$ENVX.timer"
systemctl is-active "deploy-timer@$ENVX.timer"
systemctl list-timers "deploy-timer@$ENVX.timer" --no-pager

sudo systemctl start "deploy-timer@$ENVX.service"
sudo journalctl -u "deploy-timer@$ENVX.service" -n 20 --no-pager

[ -x /usr/local/bin/sync_from_origin.sh ] && systemctl is-active "deploy-timer@$ENVX.timer" >/dev/null && printf '\033[32mOK: deploy timer (%s) 稼働中\033[0m\n' "$ENVX" || printf '\033[31mFAIL: deploy timer が起動していない\033[0m\n'
