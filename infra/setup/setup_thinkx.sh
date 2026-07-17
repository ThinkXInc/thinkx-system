# thinkx
#
# prerequisites:
#  - setup_user.sh
#  - setup_webserver.sh
#  - check_deploykey.py thinkx-system が OK + clone_monorepo.sh 済み
#  - push_env.sh thinkx(/tmp/thinkx.env。真実は thinkx/.env)
#  - push_assets.sh thinkx(/tmp/thinkx-video.tgz。真実は thinkx/web-server/views/video)
#

# repository(monorepo 前提。clone と symlink は clone_monorepo.sh が行う)
[ -e /src/thinkx/web-server ] || printf '\033[31mFAIL: /src/thinkx が無い。先に clone_monorepo.sh を流す\033[0m\n'

# .env  (git 管理外。push_env.sh で /tmp/thinkx.env を配った前提)
[ -f /tmp/thinkx.env ] && sudo install -o kaz -g serveradmins -m 640 /tmp/thinkx.env /src/thinkx/.env || printf '\033[33mWARN: thinkx.env 未配布(push_env.sh)\033[0m\n'

# venv
cd /src/thinkx/web-server
sudo -u kaz python3.9 -m venv --without-pip venv
sudo -u kaz curl -s https://bootstrap.pypa.io/pip/3.9/get-pip.py -o get-pip.py
sudo -u kaz ./venv/bin/python get-pip.py
sudo -u kaz ./venv/bin/pip install --upgrade pip
sudo -u kaz ./venv/bin/pip install -r requirements.txt

# front build  (js/css は .gitignore の生成物。repo のタスクは --watch 常駐のみのため --watch を外してワンショット実行)
cd /src/thinkx/web-server/views
sudo -u kaz npm install
sudo -u kaz npx babel src/js --out-dir js
sudo -u kaz npx lessc src/less/main.less css/main.css

# video  (git 管理外。push_assets.sh で /tmp/thinkx-video.tgz を配った前提)
[ -f /tmp/thinkx-video.tgz ] && sudo tar xzf /tmp/thinkx-video.tgz -C /src/thinkx/web-server/views || printf '\033[33mWARN: thinkx 動画未配布(push_assets.sh)\033[0m\n'
sudo chown -R kaz:serveradmins /src/thinkx/web-server/views/video 2>/dev/null

# uwsgi daemon
sudo ln -sf /src/thinkx/web-server/uwsgi/uwsgi_thinkx.service /etc/systemd/system/uwsgi_thinkx.service
# stop を SIGQUIT に(uwsgi は SIGTERM を reload 扱いで stop がハングする)
sudo mkdir -p /etc/systemd/system/uwsgi_thinkx.service.d
printf '[Service]\nKillSignal=SIGQUIT\nTimeoutStopSec=10\n' | sudo tee /etc/systemd/system/uwsgi_thinkx.service.d/override.conf > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable uwsgi_thinkx.service
sudo systemctl restart uwsgi_thinkx.service

# run uwsgi
sudo systemctl reload nginx
ls -l /tmp/uwsgi_thinkx.sock

# verify  (末尾に色で成否: 緑=200 / 黄=応答あるが≠200 / 赤=応答なし)
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: thinkxinc.com" http://localhost:8005/)
[ "$code" = 200 ] && C='\033[32mOK' || { [ "$code" = 000 ] && C='\033[31mFAIL' || C='\033[33mWARN'; }
printf "${C}: thinkx 8005 -> ${code}\033[0m\n"
