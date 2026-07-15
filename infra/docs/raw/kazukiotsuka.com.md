# kazukiotsuka.com

_created: 20250516T075919Z / updated: 20250516T212959Z_

5/16 立ち上げ

5/17 サイトデザインと実装

TLS

TLS transformism.art certbot letsencrypt

```
ssh supercom3L
```

```
sudo certbot certonly --manual \
     --preferred-challenges dns \
     --email otsuka.kazuki@googlemail.com \
     -d kazukiotsuka.com \
     -d '*.kazukiotsuka.com'
```

Requesting a certificate for kazukiotsuka.com and *.kazukiotsuka.com

Please deploy a DNS TXT record under the name:

_acme-challenge.kazukiotsuka.com.

with the following value:

XRUoJdTmjSKE66NBhbImAwwoZxMxD5GPvuv6xj5Yi8Y

Press Enter to Continue

-> Route 53のTXTに追加

Please deploy a DNS TXT record under the name:

_acme-challenge.kazukiotsuka.com.

with the following value:

VpDV9UgjxE_bYhpHHZWgCcFtS-cjRZKBtDL7cLJEytA

(This must be set up in addition to the previous challenges; do not remove,
replace, or undo the previous challenge tasks yet. Note that you might be
asked to create multiple distinct TXT records with the same name. This is
permitted by DNS standards.)

Before continuing, verify the TXT record has been deployed. Depending on the DNS
provider, this may take some time, from a few seconds to multiple minutes. You can
check if it has finished deploying with aid of online tools, such as the Google
Admin Toolbox: https://toolbox.googleapps.com/apps/dig/#TXT/_acme-challenge.kazukiotsuka.com.
Look for one or more bolded line(s) below the line ';ANSWER'. It should show the
value(s) you've just added.

Press Enter to Continue

-> Route 53の
同じキーのTXTの次の行にさらに追加

Press Enter to Continue

Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/kazukiotsuka.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/kazukiotsuka.com/privkey.pem
This certificate expires on 2025-08-14.
These files will be updated when the certificate renews.

NEXT STEPS:

This certificate will not be renewed automatically. Autorenewal of --manual certificates requires the use of an authentication hook script (--manual-auth-hook) but one was not provided. To renew this certificate, repeat this same certbot command before the certificate's expiry date.

If you like Certbot, please consider supporting our work by:

Donating to ISRG / Let's Encrypt: https://letsencrypt.org/donate
Donating to EFF: https://eff.org/donate-le

Loadbalancer

```
ssh supercom3L
cd /src/loadbalancer
```

proxy.conf

```

server {
    listen 443 ssl;
    server_name kazukiotsuka.com *.kazukiotsuka.com;  # if wildcard

    ssl_certificate     /etc/letsencrypt/live/kazukiotsuka.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kazukiotsuka.com/privkey.pem;

    location / {
        proxy_pass http://192.168.1.8:8006; 
    }
}
```

```
sudo nginx -t
sudo systemctl reload nginx
```

DNS

DNSを変更

Aレコード

```
123.226.234.127
```

クラスターのWIP    <- before 18.176.99.8

Website

init

```
cp -R /src/transformism/web-server /src/kazukiotsukacom/
cp -R /src/transformism/local /src/kazukiotsukacom/
...
```

```
 cd /src/kazukiotsukacom
cd web-server
git submodule add git@github.com:ThinkXInc/libcommon.git
python3.9 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

uwsgi_kazukiotsukacom.service

```
[Unit]
Description=uWSGI(kazukiotsukacom)
After=network.target

[Service]
Type=simple
WorkingDirectory=/src/kazukiotsukacom/web-server
ExecStart=/src/kazukiotsukacom/web-server/venv/bin/uwsgi --ini /src/kazukiotsukacom/web-server/uwsgi/uwsgi.ini
User=kaz
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

uwsgiサービスを起動する

```
sudo ln -s /src/kazukiotsukacom/web-server/uwsgi/uwsgi_kazukiotsukacom.service /etc/systemd/system/uwsgi_kazukiotsukacom.service
sudo systemctl daemon-reload
```

```
sudo systemctl enable uwsgi_kazukiotsukacom.service
sudo systemctl start uwsgi_kazukiotsukacom.service
```

⌘ Log

```
sudo journalctl -fu uwsgi_kazukiotsukacom.service --output cat -n 1000 -f
```

/src/quantz/web-server/nginx/conf.d/kazukiotsukacom.conf

```
upstream kazukiotsukacom_uwsgi {
    server unix:/tmp/uwsgi_kazukiotsukacom.sock;
}

server {
    listen 8007;
    server_name kazukiotsukacom.com; # or any domain(s) you have

    charset utf-8;
    client_max_body_size 75M;

    location / {
        include uwsgi_params;
        uwsgi_pass kazukiotsukacom_uwsgi;
    }
...
```

```
sudo nginx -t
sudo systemctl reload nginx
```

on supercom2 test site

```
curl -i localhost:8007
```

npm installとファイルのコンパイル

```
cd /src/kazukiotsukacom/web-server/views

npm install
. ./watchappviews.sh
```

views/css/main.cssが生成されていること

.comにアクセスするとプロキシーサーバーにつながるのを確認

```
ssh supercom3L
cd /src/loadbalancer
. ./logs.sh
tail -f /var/log/nginx/access.log
```

インターネット上からloadbalancerにリクエストを投げてサイトが帰るか

帰らなければログを確認

```
curl -i -k --resolve kazukiotsuka.com:443:123.226.234.127 https://kazukiotsuka.com/
```

```
curl -i -k --resolve kazukiotsuka.com:443:123.226.234.127 https://kazukiotsuka.com/sitemap.xml
```
