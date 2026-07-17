# nginx-web-root
#
# prerequisites:
#  - setup_user.sh
#  - setup_webserver.sh
#  - check_deploykey.py thinkx-system が OK + setup_monorepo.sh 済み
#

# repository(monorepo 前提。clone と symlink は setup_monorepo.sh が行う)
[ -e /src/nginx-web-root/nginx.conf ] || printf '\033[31mFAIL: /src/nginx-web-root が無い。先に setup_monorepo.sh を流す\033[0m\n'

# systemd
sudo ln -sf /src/nginx-web-root/nginx.service /etc/systemd/system/nginx.service
sudo systemctl daemon-reload

# run nginx
sudo nginx -t -p /src/nginx-web-root -c /src/nginx-web-root/nginx.conf
sudo systemctl enable --now nginx

# verify  (末尾に色で成否: 緑=OK / 赤=FAIL)
systemctl is-active --quiet nginx && printf '\033[32mOK: nginx-web-root up\033[0m\n' || printf '\033[31mFAIL: nginx not active\033[0m\n'
