# 💧【Summary】Run Supercom3L (loadbalancer)

_created: 20240411T070121Z / updated: 20250105T013254Z_

Routing summary

quantz.sixths.ai
 -> 
192.168.1.10:8000
 (supercom2)

quantz-
stream.sixths.ai
 -> 
192.168.1.6:8000
 (supercom3a)

loadbalancer/conf.d/proxy.conf

```
        # Determine the destination based on the subdomain
        if ($host ~* "^quantz-stream\.sixths\.ai$") {
            proxy_pass http://192.168.1.6:8001;
        }
        if ($host ~* "^quantz\.sixths\.ai$") {
            proxy_pass http://192.168.1.10:8000;
        }
```

-> その後 -stream.でなく/stream/に変更

*supercom3a上のgateway-serverは8001番ポート，supercom2上のwebサーバーは8000番ポートでListenする

これは両方を一台で動かす場面で設定を変えなくて良いようにするため

Logs

nginx service log

```
journalctl -xeu nginx.service
```

nginx process log

```
cd /src/loadbalancer
screen -c .screenrc_nginx
```

access & error log

```
cd /src/loadbalancer
. ./logs.sh
```

Restart nginx

*this stop services サービスを止めるので注意

```
cd /src/loadbalancer
. ./restart.sh
```

これはサービスを止めるので 
sudo systemctl reload nginx
 で無停止で設定を差し替えたい

```
sudo nginx -t -c /src/loadbalancer/nginx.conf
```

```
sudo systemctl reload nginx
```

Edit config

*まず編集しているconfigがloadbalancer内のものかを確認 (別のサーバーのファイルを編集していないか)

test config

```
sudo nginx -t -c /src/loadbalancer/nginx.conf
```

Reload config

```
sudo systemctl reload nginx
```

Restart nginx

```
sudo systemctl restart nginx
```

or

```
cd /src/loadbalancer
. ./restart.sh
```

Run without deamon

```
sudo nginx -c /src/loadbalancer/nginx.conf
```

Check config link

```
ls -l /etc/systemd/system/nginx.service
lrwxrwxrwx 1 root root 31  4月 11 16:28 /etc/systemd/system/nginx.service -> /src/loadbalancer/nginx.service
```

Check daemon config

```
vim /etc/systemd/system/nginx.service
```

Check forwarding

check if a backend server is listening

```
curl -k https://192.168.1.6:8001/api/request-token -H "Host: quantz-stream.sixths.ai"
```

Test Connection

test ssl

```
openssl s_client -connect sixths.ai:443
```

test connection

```
curl -Iv https://quantz-stream.sixths.ai
curl -Iv https://quantz.sixths.ai
```

-> if not healthy

DNS check

```
nslookup quantz-stream.sixths.ai
dig quantz-stream.sixths.ai
```

https://dnschecker.org/#A/quantz-stream.sixths.ai

DNS Aレコードにルーティングが設定されているかどうか

(設定してから反映まで数分~数時間かかる)

Maintanance Mode

Ref

【Summary】Maintenance Mode
