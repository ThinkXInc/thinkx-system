# restart kazukiotsukacom

echo "== restart kazukiotsukacom =="
sudo systemctl restart uwsgi_kazukiotsukacom.service

# uwsgi log  (app ロードは async のため待つ)
sleep 2
sudo journalctl -u uwsgi_kazukiotsukacom -n 15 --no-pager

# verify
code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: kazukiotsuka.com" http://localhost:8007/)
[ "$code" = 200 ] && C='\033[32mOK' || { [ "$code" = 000 ] && C='\033[31mFAIL' || C='\033[33mWARN'; }
printf "${C}: kazukiotsuka 8007 -> ${code}\033[0m\n"
