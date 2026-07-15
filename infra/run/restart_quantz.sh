# restart quantz-web (supercom2)

sudo nginx -t -c /src/quantz-web/web-server/nginx/nginx.conf
sudo systemctl restart uwsgi.service
sudo systemctl restart nginx
sudo systemctl restart vectordb_server.service
sudo systemctl restart billing_scheduler.service
sudo systemctl restart process_chatdata.service

systemctl is-active uwsgi nginx vectordb_server billing_scheduler process_chatdata
