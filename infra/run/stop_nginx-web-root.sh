# stop nginx-web-root

echo "== stop_nginx-web-root =="
sudo systemctl stop nginx

# verify
systemctl is-active --quiet nginx && printf '\033[31mFAIL: stop_nginx-web-root nginx まだ active\033[0m\n' || printf '\033[32mOK: stop_nginx-web-root nginx stopped\033[0m\n'
