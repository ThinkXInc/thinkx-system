# restart nginx-web-root

echo "== restart nginx-web-root =="
sudo nginx -t -p /src/nginx-web-root -c /src/nginx-web-root/nginx.conf
sudo systemctl restart nginx

# verify
systemctl is-active --quiet nginx && printf '\033[32mOK: nginx active\033[0m\n' || printf '\033[31mFAIL: nginx %s\033[0m\n' "$(systemctl is-active nginx)"
