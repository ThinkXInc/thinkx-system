# Runbook: TLS 証明書の更新

オンプレの `certbot --manual`(DNS TXT 手コピペ)は廃止。
AWS では `--dns-route53` で全自動。人間のコピペも Enter も不要。

## 状態確認
```bash
ssh ubuntu@<lb_ip>
sudo certbot certificates          # 各ドメインの期限一覧
```

## 更新(自動)
```bash
# 全ドメイン一括更新 + nginx リロード
sudo certbot renew --dns-route53 --quiet && sudo systemctl reload nginx
```

## 新規ドメイン取得
```bash
sudo certbot certonly --dns-route53 --non-interactive --agree-tos \
  -m admin@thinkxinc.com \
  -d example.com -d '*.example.com'
sudo systemctl reload nginx
```

## 自動更新(cron。setup で設置済み)
```
/etc/cron.d/certbot-renew:
0 3 * * * root certbot renew --dns-route53 --quiet && systemctl reload nginx
```

## 前提
- EC2 に Route53 の IAM ロールが付いていること(アクセスキー平文は使わない)。
- transformism.art は S トラック未適用。載せる判断後に取得する。

## 確認
```bash
openssl s_client -connect thinkxinc.com:443 </dev/null 2>/dev/null | openssl x509 -noout -dates
```
