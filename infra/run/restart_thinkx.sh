# restart thinkx

echo "== restart thinkx =="
sudo systemctl restart uwsgi_thinkx.service

# uwsgi log  (app ロードは async のため待つ)
sleep 2
sudo journalctl -u uwsgi_thinkx -n 15 --no-pager

# verify
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: thinkxinc.com" http://localhost:8005/)
[ "$code" = 200 ] && C='\033[32mOK' || { [ "$code" = 000 ] && C='\033[31mFAIL' || C='\033[33mWARN'; }
printf "${C}: restart_thinkx 8005 -> ${code}\033[0m\n"
