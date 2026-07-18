# run nginx-web-root

echo "== run_nginx-web-root =="
sudo systemctl start nginx

# verify  (active + 実プロセスが nginx-web-root 設定)
sleep 1
systemctl is-active --quiet nginx && sudo cat /proc/$(cat /run/nginx.pid)/cmdline | tr '\0' ' ' | grep -q nginx-web-root && printf '\033[32mOK: run_nginx-web-root nginx active(nginx-web-root 設定)\033[0m\n' || printf '\033[31mFAIL: run_nginx-web-root nginx=%s\033[0m\n' "$(systemctl is-active nginx)"
