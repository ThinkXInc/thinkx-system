# restart LB (supercom3L: nginx)  — 先に config 検証(失敗すれば restart の前に気づける)

sudo nginx -t -c /src/loadbalancer/nginx.conf
sudo systemctl restart nginx.service
## reload(無停止)の場合:
# sudo systemctl reload nginx.service

systemctl is-active nginx
