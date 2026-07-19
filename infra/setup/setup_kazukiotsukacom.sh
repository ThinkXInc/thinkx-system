# kazukiotsukacom
#
# prerequisites:
#  - setup_user.sh
#  - setup_webserver.sh
#  - check_deploykey.py thinkx-system が OK + clone_monorepo.sh 済み
#  - push_env.sh kazukiotsukacom(/tmp/kazukiotsukacom.env。真実は kazukiotsukacom/.env)
#

# repository(monorepo 前提。clone と symlink は clone_monorepo.sh が行う)
[ -e /src/kazukiotsukacom/web-server ] || printf '\033[31mFAIL: /src/kazukiotsukacom が無い。先に clone_monorepo.sh を流す\033[0m\n'

# .env  (git 管理外。push_env.sh で /tmp/kazukiotsukacom.env を配った前提)
[ -f /tmp/kazukiotsukacom.env ] && sudo install -o kaz -g serveradmins -m 640 /tmp/kazukiotsukacom.env /src/kazukiotsukacom/.env || printf '\033[33mWARN: kazukiotsukacom.env 未配布(push_env.sh)\033[0m\n'

# venv
cd /src/kazukiotsukacom/web-server
sudo -u kaz python3.9 -m venv --without-pip venv
sudo -u kaz curl -s https://bootstrap.pypa.io/pip/3.9/get-pip.py -o get-pip.py
sudo -u kaz ./venv/bin/python get-pip.py
sudo -u kaz ./venv/bin/pip install --upgrade pip
sudo -u kaz ./venv/bin/pip install -r requirements.txt

# front build  (js/css は .gitignore の生成物。repo のタスクは --watch 常駐のみのため --watch を外してワンショット実行)
cd /src/kazukiotsukacom/web-server/views
sudo -u kaz npm install
sudo -u kaz npx babel src/js --out-dir js
sudo -u kaz npx lessc src/less/main.less css/main.css

# uwsgi daemon
sudo ln -sf /src/kazukiotsukacom/web-server/uwsgi/uwsgi_kazukiotsukacom.service /etc/systemd/system/uwsgi_kazukiotsukacom.service
# stop を SIGQUIT に(uwsgi は SIGTERM を reload 扱いで stop がハングする)
sudo mkdir -p /etc/systemd/system/uwsgi_kazukiotsukacom.service.d
printf '[Service]\nKillSignal=SIGQUIT\nTimeoutStopSec=10\n' | sudo tee /etc/systemd/system/uwsgi_kazukiotsukacom.service.d/override.conf > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable uwsgi_kazukiotsukacom.service
sudo systemctl restart uwsgi_kazukiotsukacom.service

# run uwsgi
sudo systemctl reload nginx
ls -l /tmp/uwsgi_kazukiotsukacom.sock

# verify  (末尾に色で成否: 緑=200 / 黄=応答あるが≠200 / 赤=応答なし)
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: kazukiotsuka.com" http://localhost:8007/)
[ "$code" = 200 ] && C='\033[32mOK' || { [ "$code" = 000 ] && C='\033[31mFAIL' || C='\033[33mWARN'; }
printf "${C}: kazukiotsuka 8007 -> ${code}\033[0m\n"
