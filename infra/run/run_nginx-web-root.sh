# run nginx-web-root

echo "== run nginx-web-root =="
sudo systemctl start nginx

# verify
systemctl is-active --quiet nginx && printf '\033[32mOK: nginx active\033[0m\n' || printf '\033[31mFAIL: nginx %s\033[0m\n' "$(systemctl is-active nginx)"
