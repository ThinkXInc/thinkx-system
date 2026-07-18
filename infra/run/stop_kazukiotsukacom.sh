# stop kazukiotsukacom

echo "== stop kazukiotsukacom =="
sudo systemctl stop uwsgi_kazukiotsukacom.service

# verify
systemctl is-active --quiet uwsgi_kazukiotsukacom && printf '\033[31mFAIL: stop_kazukiotsukacom uwsgi_kazukiotsukacom まだ active\033[0m\n' || printf '\033[32mOK: stop_kazukiotsukacom uwsgi_kazukiotsukacom stopped\033[0m\n'
