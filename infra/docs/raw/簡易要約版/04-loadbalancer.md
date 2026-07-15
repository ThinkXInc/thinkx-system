# LB(supercom3L)nginx 運用(原本)

Routing: quantz.sixths.ai -> 192.168.1.x:8000, quantz-stream -> :8001 等。
conf.d/proxy.conf で server_name 別に proxy_pass。

無停止リロード(推奨):
```
sudo nginx -t -c /src/loadbalancer/nginx.conf
sudo systemctl reload nginx
```
restart(サービス停止するので注意):
```
cd /src/loadbalancer && . ./restart.sh   # または systemctl restart nginx
```
ログ:
```
journalctl -xeu nginx.service
cd /src/loadbalancer && . ./logs.sh
```
疎通確認: curl -Iv https://quantz.sixths.ai / openssl s_client -connect sixths.ai:443
DNS: nslookup / dig / dnschecker.org

nginx.conf: レート制限(basic/static/api/fs/stream/global 30r/s)、ltsv ログ、
proxy_cache(video 7d)、include conf.d/*conf。

> 移行後: runbooks/lb-config.md。proxy_pass 先は 192.168.1.11(web)。
