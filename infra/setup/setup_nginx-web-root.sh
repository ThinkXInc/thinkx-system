# nginx-web-root
#
# prerequisites:
#  - setup_user.sh
#  - setup_webserver.sh
#  - check_deploykey.py thinkx-system が OK + clone_monorepo.sh 済み
#

# repository(monorepo 前提。clone と symlink は clone_monorepo.sh が行う)
[ -e /src/nginx-web-root/nginx.conf ] || printf '\033[31mFAIL: /src/nginx-web-root が無い。先に clone_monorepo.sh を流す\033[0m\n'

# systemd
sudo ln -sf /src/nginx-web-root/nginx.service /etc/systemd/system/nginx.service
sudo systemctl daemon-reload

# run nginx  (*enable --now は既起動の apt 版 nginx を再起動しないため、必ず restart で乗っ取る)
sudo nginx -t -p /src/nginx-web-root -c /src/nginx-web-root/nginx.conf
sudo systemctl enable nginx
sudo systemctl restart nginx

# verify  (末尾に色で成否: 緑=OK / 赤=FAIL。実プロセスが nginx-web-root 設定で 8005 が応答することまで確認)
sudo cat /proc/$(cat /run/nginx.pid)/cmdline 2>/dev/null | tr '\0' ' ' | grep -q nginx-web-root && curl -s -o /dev/null --max-time 5 http://localhost:8005/ && printf '\033[32mOK: setup_nginx-web-root 完了(nginx-web-root 設定で稼働・8005 応答)\033[0m\n' || printf '\033[31mFAIL: setup_nginx-web-root(旧 nginx のまま or 8005 無応答)\033[0m\n'
