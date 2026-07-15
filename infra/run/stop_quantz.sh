# stop quantz-web (supercom2)  — 起動と逆順で daemon 停止 → docker compose down

sudo systemctl stop nginx
sudo systemctl stop process_chatdata.service
sudo systemctl stop billing_scheduler.service
sudo systemctl stop vectordb_server.service
sudo systemctl stop uwsgi.service

cd /src/quantz-web
sudo docker-compose down

systemctl is-active uwsgi vectordb_server billing_scheduler process_chatdata nginx
sudo docker-compose ps
