# 🌃【Summary】Redis Commands

_created: 20240331T043140Z / updated: 20240331T065730Z_

Summary

log

```
cd /src/quantz
cd web-server/mongodb
screen -c .screenrc_mongodb
```

restart

```
cd /src/quantz/web-server
cd mongodb
. ./restart.sh
```

Setting files

systemctl

```
/etc/systemd/system/nginx.service -> /src/quantz/web-server/nginx/nginx.service
```

-> 編集したら 
sudo systemctl daemon-reload
 を実行

conf

```
/src/quantz/web-server/mongodb/mongodb.conf
```

Run

start

```
cd /src/quantz/web-server
cd mongodb
. ./start.sh
```

restart

```
cd /src/quantz/web-server
cd mongodb
. ./restart.sh
```

stop

```
cd /src/quantz/web-server
cd mongodb
. ./stop.sh
```

status

```
cd /src/quantz/web-server
cd mongodb
. ./status.sh
```

Log & Status (
status.sh
 includes all)

```
sudo systemctl status uwsgi
```

● uwsgi.service - uWSGI Neuravoice Control Center

     Loaded: loaded (/etc/systemd/system/uwsgi.service; linked; ven>

     Active: active (running) since Thu 2023-12-28 12:17:47 JST; 3 >

   Main PID: 2307922 (uwsgi)

      Tasks: 99 (limit: 618891)

     Memory: 194.8M

```
systemctl list-units --type=service | grep uwsgi
```

uwsgi.service                                         loaded active     running            uWSGI

```
ps aux | grep uwsgi
```

root     2319574  0.0  0.0  10232  6144 ?        Ss   16:09   0:00 /usr/sbin/nginx -c /src/quantz/web-server/nginx/nginx.conf

```
journalctl -u uwsgi.service --no-pager | tail -n 3000
```

or

```
cd /src/quantz/web-server/uwsgi
screen -c .screenrc_log
```

Enable starts on boot

```
sudo systemctl enable mongodb
```

To disable the services from starting on boot:

```
sudo systemctl disable mongodb
```

Reload .service

```
sudo systemctl daemon-reload
```

Set admin user

add user & add to ops group

```
sudo groupadd ops
sudo usermod -a -G ops {your name here}
```

add permission to ops

```
sudo chown -R :ops /var/log/nginx
sudo chmod -R 775 /var/log/nginx
```

```
sudo chown -R :ops /etc/nginx
sudo find /etc/nginx -type d -exec chmod 775 {} \;
sudo find /etc/nginx -type f -exec chmod 664 {} \;
```

Trouble shooting

nginxが起動しない

nginx.conのアドレスが解決できるか

```
ping {address}
```

nginx.confのポートが空いているか (他と被ってないか)

```
sudo lsof -i :8001
```

Others

link systemctl conf

```
sudo ln -sf /src/quantz/web-server/redis_session/redis_session.service /etc/systemd/system/redis_session.service
sudo systemctl daemon-reload
```
