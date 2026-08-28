# podcast(タイムライン編集サイト) — web 機で実行する
#
# prerequisites:
#  - setup_user.sh / setup_webserver.sh / setup_nginx-web-root.sh
#  - check_deploykey.py thinkx-system が OK + clone_monorepo.sh 済み
#  - デプロイ済みで /src/podcast/web-server が存在すること
#  - .env は不要(data は既定の /src/podcast/data。ローカルと同一構造 — D-52)
#

# repository(monorepo 前提。clone と symlink は clone_monorepo.sh が行う)
[ -e /src/podcast/web-server ] || printf '\033[31mFAIL: /src/podcast が無い。先に clone_monorepo.sh とデプロイを流す\033[0m\n'

# ffmpeg(サーバー書き出しに使う。エンコーダは export_audio.py が aac に自動フォールバック)
export NEEDRESTART_MODE=a
sudo apt-get install -y ffmpeg

# venv(サーバーの python3 = 3.10。requirements の click 8.5 が 3.10+ 前提)
cd /src/podcast/web-server
sudo -u kaz python3 -m venv venv
sudo -u kaz ./venv/bin/pip install --upgrade pip
sudo -u kaz ./venv/bin/pip install -r requirements.txt

# uwsgi daemon
sudo ln -sf /src/podcast/web-server/uwsgi/uwsgi_podcast.service /etc/systemd/system/uwsgi_podcast.service
# stop を SIGQUIT に(uwsgi は SIGTERM を reload 扱いで stop がハングする)
sudo mkdir -p /etc/systemd/system/uwsgi_podcast.service.d
printf '[Service]\nKillSignal=SIGQUIT\nTimeoutStopSec=10\n' | sudo tee /etc/systemd/system/uwsgi_podcast.service.d/override.conf > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable uwsgi_podcast.service
sudo systemctl restart uwsgi_podcast.service

# 保存トリガー同期の flusher(D-52。編集保存を git commit/push する)
sudo install -m 0755 /src/thinkx-system/infra/run/podcast_data_sync.py /usr/local/bin/podcast_data_sync.py
sudo ln -sf /src/thinkx-system/infra/setup/podcast-data-sync.service /etc/systemd/system/podcast-data-sync.service
sudo ln -sf /src/thinkx-system/infra/setup/podcast-data-sync.timer /etc/systemd/system/podcast-data-sync.timer
sudo systemctl daemon-reload
sudo systemctl enable --now podcast-data-sync.timer

# run nginx
sudo systemctl reload nginx
ls -l /tmp/uwsgi_podcast.sock

# verify  (末尾に色で成否: 緑=200 / 黄=応答あるが≠200 / 赤=応答なし)
code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8010/podcast/)
[ "$code" = 200 ] && C='\033[32mOK' || { [ "$code" = 000 ] && C='\033[31mFAIL' || C='\033[33mWARN'; }
printf "${C}: podcast 8010 -> ${code}\033[0m\n"
