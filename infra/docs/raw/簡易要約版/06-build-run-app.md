# アプリのビルド・起動・ログ(原本)

フロントビルド(watcher):
```
cd /src/thinkx/web-server/views
. ./watchappviews.sh
```
uwsgi ログ:
```
sudo journalctl -fu uwsgi_thinkx.service --output cat -n 3000
```
uwsgi 再起動:
```
sudo systemctl restart uwsgi_thinkx.service
```
nginx reload:
```
ssh supercom2 && sudo nginx -t && sudo systemctl reload nginx
```

> 移行後: runbooks/deploy-site.md, restart-site.md。
