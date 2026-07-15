# start quantz-web (supercom2)  — docker compose → daemon 群(raw「Run Web App Server (Quantz Web) ver.2」準拠)

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

systemctl is-active uwsgi vectordb_server billing_scheduler process_chatdata nginx
