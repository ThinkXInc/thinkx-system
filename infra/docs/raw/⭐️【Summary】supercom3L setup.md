# ⭐️【Summary】supercom3L setup

_created: 20240411T061531Z / updated: 20241113T021049Z_

⭐️【Summary】supercom3: setup & installation を参照 以下その後に実行

```
sudo apt install iftop sysstat nload traceroute
```

TLS

```
ssh supercom3L
sudo mv custom.key /etc/ssl/private/thinkxinc.com.key
sudo mv thinkxinc.com.crt /etc/ssl/certs/
```

```
sudo groupadd sslgroup
sudo usermod -a -G sslgroup kaz
```

```
sudo chown root:sslgroup /etc/ssl/private/thinkxinc.com.key
sudo chown root:sslgroup /etc/ssl/certs/thinkxinc.com.crt
sudo chmod 644 /etc/ssl/certs/thinkxinc.com.crt
sudo chmod 640 /etc/ssl/private/thinkxinc.com.key
```

install nginx

```
sudo apt update
sudo apt install nginx
```

kaz@loadbalancer:~$ systemctl status nginx

● nginx.service - A high performance web server and a reverse proxy server

     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor pre>

     Active: active (running) since Thu 2024-04-11 15:17:46 JST; 1min 1s ago

       Docs: man:nginx(8)

    Process: 374316 ExecStartPre=/usr/sbin/nginx -t -q -g daemon on; master>

    Process: 374317 ExecStart=/usr/sbin/nginx -g daemon on; master_process >

   Main PID: 374422 (nginx)

      Tasks: 17 (limit: 38277)

     Memory: 14.4M

        CPU: 74ms

     CGroup: /system.slice/nginx.service

permissions

```
sudo chown www-data:www-data /var/log/nginx/access.log
sudo chown www-data:www-data /var/log/nginx/error.log
sudo chmod 664 /var/log/nginx/access.log
sudo chmod 664 /var/log/nginx/error.log
sudo mkdir -p /run/nginx
sudo chown www-data:www-data /run/nginx
```

make run group

```
sudo groupadd serveradmins
sudo usermod -a -G serveradmins kaz
```

make source directory

```
sudo mkdir /src
cd /src
sudo chown kaz:serveradmins /src
```

clone repo

```
cd /src
git clone git@github.com:ThinkXInc/loadbalancer.git
```

symlink

```
sudo ln -s /src/loadbalancer/nginx.service /etc/systemd/system/nginx.service
sudo systemctl daemon-reload
```

install screen

```
sudo apt install screen
```

install multitail

```
sudo apt-get install multitail
```

(TSL 
sixths.ai
)

TLS

まず/etc/ssl/private/custom.key と /etc/ssl/certs/sixthsai.crt を転送

```
ssh supercom3a
cd /etc/ssl
/etc/ssl$ scp private/custom.key 
/etc/ssl$ scp certs/sixthsai.crt  supercom3L:~/
```

```
ssh supercom3L
sudo mv custom.key /etc/ssl/private/
sudo mv sixthsai.crt /etc/ssl/certs/
```

```
sudo groupadd sslgroup
sudo usermod -a -G sslgroup kaz
```

```
sudo chown root:sslgroup /etc/ssl/private/custom.key
sudo chown root:sslgroup /etc/ssl/certs/sixthsai.crt
sudo chmod 644 /etc/ssl/certs/sixthsai.crt
sudo chmod 640 /etc/ssl/private/custom.key
```
