# restart LB (supercom3L: nginx)  — 先に config 検証(失敗すれば restart の前に気づける)

echo "== restart_loadbalancer =="
sudo nginx -t -c /src/loadbalancer/nginx.conf
sudo systemctl restart nginx.service
## reload(無停止)の場合:
# sudo systemctl reload nginx.service

# verify  (active + 実プロセスが /src/loadbalancer 設定 + 443 応答)
sleep 1
systemctl is-active --quiet nginx && sudo cat /proc/$(cat /run/nginx.pid)/cmdline | tr '\0' ' ' | grep -q /src/loadbalancer && [ "$(curl -sk -o /dev/null --max-time 5 -w '%{http_code}' https://localhost/)" != 000 ] && printf '\033[32mOK: restart_loadbalancer nginx active(/src/loadbalancer 設定・443 応答)\033[0m\n' || printf '\033[31mFAIL: restart_loadbalancer nginx=%s\033[0m\n' "$(systemctl is-active nginx)"
