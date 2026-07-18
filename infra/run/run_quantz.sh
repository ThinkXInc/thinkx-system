# start quantz-web (supercom2)  — docker compose → daemon 群(raw「Run Web App Server (Quantz Web) ver.2」準拠)

echo "== run_quantz =="
# docker compose (web: mongodb, redis, rabbitmq)
cd /src/quantz-web
sudo docker-compose up -d
sudo docker-compose ps

# daemons
sudo systemctl start uwsgi.service
sudo systemctl start vectordb_server.service
sudo systemctl start billing_scheduler.service
sudo systemctl start process_chatdata.service
sudo systemctl start nginx

# verify  (5サービス全 active)
systemctl is-active --quiet uwsgi && systemctl is-active --quiet nginx && systemctl is-active --quiet vectordb_server && systemctl is-active --quiet billing_scheduler && systemctl is-active --quiet process_chatdata && printf '\033[32mOK: run_quantz 5サービス active\033[0m\n' || printf '\033[31mFAIL: run_quantz 不稼働あり uwsgi/nginx/vectordb/billing/chatdata=%s\033[0m\n' "$(systemctl is-active uwsgi nginx vectordb_server billing_scheduler process_chatdata | tr '\n' '/')"
