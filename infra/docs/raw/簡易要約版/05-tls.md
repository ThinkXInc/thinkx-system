# TLS 証明書(原本 / certbot manual)

オンプレは DNS-01 手動チャレンジ:
```
sudo certbot certonly --manual --preferred-challenges dns \
  --email admin@thinkxinc.com -d thinkxinc.com -d '*.thinkxinc.com'
# -> 表示された TXT 値を Route53 の _acme-challenge に手コピペ -> continue
# -> 2 つ目の値も同レコードに追加 -> 15秒待ち -> continue
sudo nginx -t && sudo systemctl reload nginx
```
対象ドメイン: thinkxinc.com / truetechjapan.com / kazukiotsuka.com /
transformism.art / nntmapp.com(いずれもワイルドカード)。
自動更新されない(--manual のため期限前に再実行が必要)。

> 移行後: runbooks/tls-renew.md。certbot --dns-route53 で全自動 + cron 自動更新。
> 手コピペ・Enter は不要になる。
