# stop thinkx

echo "== stop thinkx =="
sudo systemctl stop uwsgi_thinkx.service

# verify
systemctl is-active --quiet uwsgi_thinkx && printf '\033[31mFAIL: uwsgi_thinkx まだ active\033[0m\n' || printf '\033[32mOK: uwsgi_thinkx stopped\033[0m\n'
