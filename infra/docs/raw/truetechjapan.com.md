# truetechjapan.com

_created: 20250701T061757Z / updated: 20250701T062347Z_

Build & Run App

build watcher - front end app　🪐 

```
cd /src/thinkx/web-server
cd views
. ./watchappviews.sh
```

uwsgi log 
🌃【Summary】UWSGI Commands
 🪐 

```
sudo journalctl -fu uwsgi_thinkx.service --output cat -n 3000
```

restart uwsgi 🪐 

```
sudo systemctl restart uwsgi_thinkx.service
```

reload nginx

```
ssh supercom2
sudo nginx -t
sudo systemctl reload nginx
```

Logs

サイトのアクセス構造

1 loadbalancerで webserver にそのままリクエストが渡される

```

server {
    listen 80;
    server_name truetechjapan.com www.truetechjapan.com;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name truetechjapan.com www.truetechjapan.com;  # Include www if needed

    # SSL certificate paths (update these based on Certbot output)
    ssl_certificate /etc/letsencrypt/live/truetechjapan.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/truetechjapan.com/privkey.pem;

    client_max_body_size 75M;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;

        proxy_pass http://192.168.1.8:8005;  # Adjust to your backend server
    }
}
```

2 webserverのnginxの設定によりFQDN (truetechjapan.com)の場合，urlの頭を /truetechjapan/  にする

```

# New server block for truetechjapan.com (with /nntm rewrite)
server {
    listen 8005;
    server_name truetechjapan.com;

    charset utf-8;
    client_max_body_size 75M;

    location / {
        rewrite ^/(?!truetechjapan)(.*)$ /truetechjapan/$1 last;
        include uwsgi_params;
        uwsgi_pass unix:/tmp/uwsgi_thinkx.sock;
    }
```
