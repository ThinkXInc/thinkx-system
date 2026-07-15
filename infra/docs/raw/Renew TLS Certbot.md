# Renew TLS Certbot

_created: 20250627T104116Z / updated: 20260327T043525Z_

```
ssh supercom3L
```

check all TLS

```
sudo certbot certificates
```

AWS Route53にログイン

EXPIREDしているものについて以下のコマンドを実行

-> Route 53 の _acme- .. のvalueを置き換える (もうひとつあるのでまだ保存しない)

-> continue

-> 再び出てきたコードを先の下の行に書き保存

-> 15秒程度待ち continue 

-> nginxを再起動

```
sudo nginx -t
sudo systemctl reload nginx
```

*nginx を再起動しないと反映されないので注意

Renew

```
sudo certbot certonly --manual \
     --preferred-challenges dns \
     --email admin@thinikxinc.com \
     -d thinkxinc.com \
     -d '*.thinkxinc.com'
```

```
sudo certbot certonly --manual \
     --preferred-challenges dns \
     --email support@truetechjapan.com \
     -d truetechjapan.com \
     -d '*.truetechjapan.com'
```

```
sudo certbot certonly --manual \
     --preferred-challenges dns \
     --email otsuka.kazuki@googlemail.com \
     -d kazukiotsuka.com \
     -d '*.kazukiotsuka.com'
```

```
sudo certbot certonly --manual \
     --preferred-challenges dns \
     --email i@transformism.art \
     -d transformism.art \
     -d '*.transformism.art'
```

```
sudo certbot certonly --manual \
    --preferred-challenges dns \
    --email support@nntmapp.com \
    -d nntmapp.com \
    -d '*.nntmapp.com'
```

Trouble Shooting

期限内なのに効いていない

-> nginxが反映していないだけならリロードする

```
sudo nginx -t
sudo systemctl reload nginx
```
