# stop nginx-web-root

echo "== stop nginx-web-root =="
sudo systemctl stop nginx

# verify
systemctl is-active --quiet nginx && printf '\033[31mFAIL: nginx まだ active\033[0m\n' || printf '\033[32mOK: nginx stopped\033[0m\n'
