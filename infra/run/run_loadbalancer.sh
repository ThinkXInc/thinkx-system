# start LB (supercom3L: nginx)

echo "== run_loadbalancer =="
sudo systemctl start nginx.service

# verify  (active + 実プロセスが /src/loadbalancer 設定)
sleep 1
systemctl is-active --quiet nginx && sudo cat /proc/$(cat /run/nginx.pid)/cmdline | tr '\0' ' ' | grep -q /src/loadbalancer && printf '\033[32mOK: run_loadbalancer nginx active(/src/loadbalancer 設定)\033[0m\n' || printf '\033[31mFAIL: run_loadbalancer nginx=%s\033[0m\n' "$(systemctl is-active nginx)"
