# nginx-web-root
#
# prerequisites:
#  - setup_user.sh
#  - setup_webserver.sh
#  - check_deploykey.py nginx-web-root が OK(鍵配置・GitHub 認証)
#

# clone repository
cd /src
sudo -u kaz git clone git@github-nginx-web-root:ThinkXInc/nginx-web-root.git

# systemd
sudo ln -sf /src/nginx-web-root/nginx.service /etc/systemd/system/nginx.service
sudo systemctl daemon-reload

# run nginx
sudo nginx -t -p /src/nginx-web-root -c /src/nginx-web-root/nginx.conf
sudo systemctl enable --now nginx

# verify  (末尾に色で成否: 緑=OK / 赤=FAIL)
systemctl is-active --quiet nginx && printf '\033[32mOK: nginx-web-root up\033[0m\n' || printf '\033[31mFAIL: nginx not active\033[0m\n'
