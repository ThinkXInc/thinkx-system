# restart quantz-web (supercom2)

echo "== restart_quantz =="
sudo nginx -t -c /src/quantz-web/web-server/nginx/nginx.conf
sudo systemctl restart uwsgi.service
sudo systemctl restart nginx
sudo systemctl restart vectordb_server.service
sudo systemctl restart billing_scheduler.service
sudo systemctl restart process_chatdata.service

# verify  (5サービス全 active)
systemctl is-active --quiet uwsgi && systemctl is-active --quiet nginx && systemctl is-active --quiet vectordb_server && systemctl is-active --quiet billing_scheduler && systemctl is-active --quiet process_chatdata && printf '\033[32mOK: restart_quantz 5サービス active\033[0m\n' || printf '\033[31mFAIL: restart_quantz 不稼働あり uwsgi/nginx/vectordb/billing/chatdata=%s\033[0m\n' "$(systemctl is-active uwsgi nginx vectordb_server billing_scheduler process_chatdata | tr '\n' '/')"
