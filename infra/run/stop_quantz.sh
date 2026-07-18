# stop quantz-web (supercom2)  — 起動と逆順で daemon 停止 → docker compose down

echo "== stop_quantz =="
sudo systemctl stop nginx
sudo systemctl stop process_chatdata.service
sudo systemctl stop billing_scheduler.service
sudo systemctl stop vectordb_server.service
sudo systemctl stop uwsgi.service

cd /src/quantz-web
sudo docker-compose down
sudo docker-compose ps

# verify  (5サービス全停止)
{ systemctl is-active --quiet uwsgi || systemctl is-active --quiet nginx || systemctl is-active --quiet vectordb_server || systemctl is-active --quiet billing_scheduler || systemctl is-active --quiet process_chatdata; } && printf '\033[31mFAIL: stop_quantz まだ active あり uwsgi/nginx/vectordb/billing/chatdata=%s\033[0m\n' "$(systemctl is-active uwsgi nginx vectordb_server billing_scheduler process_chatdata | tr '\n' '/')" || printf '\033[32mOK: stop_quantz 5サービス stopped\033[0m\n'
