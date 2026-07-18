# restart nginx-web-root

echo "== restart_nginx-web-root =="
sudo nginx -t -p /src/nginx-web-root -c /src/nginx-web-root/nginx.conf
sudo systemctl restart nginx

# verify  (active + 実プロセスが nginx-web-root 設定 + 8005 応答)
sleep 1
systemctl is-active --quiet nginx && sudo cat /proc/$(cat /run/nginx.pid)/cmdline | tr '\0' ' ' | grep -q nginx-web-root && [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://localhost:8005/)" != 000 ] && printf '\033[32mOK: restart_nginx-web-root nginx active(nginx-web-root 設定・8005 応答)\033[0m\n' || printf '\033[31mFAIL: restart_nginx-web-root nginx=%s\033[0m\n' "$(systemctl is-active nginx)"
