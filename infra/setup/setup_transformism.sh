# transformism
#
# prerequisites:
#  - setup_user.sh
#  - setup_webserver.sh
#  - check_deploykey.py thinkx-system が OK + clone_monorepo.sh 済み
#  - push_env.sh transformism(/tmp/transformism.env。真実は transformism/.env)
#

# repository(monorepo 前提。clone と symlink は clone_monorepo.sh が行う)
[ -e /src/transformism/web-server ] || printf '\033[31mFAIL: /src/transformism が無い。先に clone_monorepo.sh を流す\033[0m\n'

# .env  (git 管理外。push_env.sh で /tmp/transformism.env を配った前提)
[ -f /tmp/transformism.env ] && sudo install -o kaz -g serveradmins -m 640 /tmp/transformism.env /src/transformism/.env || printf '\033[33mWARN: transformism.env 未配布(push_env.sh)\033[0m\n'

# venv
cd /src/transformism/web-server
sudo -u kaz python3.9 -m venv --without-pip venv
sudo -u kaz curl -s https://bootstrap.pypa.io/pip/3.9/get-pip.py -o get-pip.py
sudo -u kaz ./venv/bin/python get-pip.py
sudo -u kaz ./venv/bin/pip install --upgrade pip
sudo -u kaz ./venv/bin/pip install -r requirements.txt

# front build
cd /src/transformism/web-server/views
sudo -u kaz npm install
sudo -u kaz npx babel src/js --out-dir js
sudo -u kaz npx lessc src/less/main.less css/main.css

# uwsgi daemon
sudo ln -sf /src/transformism/web-server/uwsgi/uwsgi_transformism.service /etc/systemd/system/uwsgi_transformism.service
# stop を SIGQUIT に(uwsgi は SIGTERM を reload 扱いで stop がハングする)
sudo mkdir -p /etc/systemd/system/uwsgi_transformism.service.d
printf '[Service]\nKillSignal=SIGQUIT\nTimeoutStopSec=10\n' | sudo tee /etc/systemd/system/uwsgi_transformism.service.d/override.conf > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable uwsgi_transformism.service
sudo systemctl restart uwsgi_transformism.service

# run uwsgi
sudo systemctl reload nginx
ls -l /tmp/uwsgi_transformism.sock

# verify  (受け入れ = ルートゴールデン /→200)
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: transformism.art" http://localhost:8006/)
[ "$code" = 200 ] && C='\033[32mOK' || { [ "$code" = 000 ] && C='\033[31mFAIL' || C='\033[33mWARN'; }
printf "${C}: transformism 8006 -> ${code}\033[0m\n"
