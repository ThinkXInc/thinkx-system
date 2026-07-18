# stop LB (supercom3L: nginx)

echo "== stop_loadbalancer =="
sudo systemctl stop nginx.service

# verify
systemctl is-active --quiet nginx && printf '\033[31mFAIL: stop_loadbalancer nginx まだ active\033[0m\n' || printf '\033[32mOK: stop_loadbalancer nginx stopped\033[0m\n'
