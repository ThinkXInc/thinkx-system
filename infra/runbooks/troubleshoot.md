# Runbook: サイトが返らない時のチェック(AWS 版)

オンプレの手順(doc62)を AWS 向けに読み替えたもの。
Cisco NAT 関連は消滅し、Security Group 確認に置き換わる。

## 1. web に届いているか
```bash
ssh ubuntu@<web_ip>
# uwsgi バックエンド単体
curl -i localhost:8005            # thinkx
curl -i localhost:8006            # transformism(載せている場合)
curl -i localhost:8007            # kazukiotsuka
# 起動中サービス
systemctl list-units --type=service --state=running | grep -E 'uwsgi|nginx'
```

## 2. LB -> web の内部疎通
```bash
ssh ubuntu@<lb_ip>
curl -i <web_ip>:8005
```
届かない場合 → **Security Group** を確認(オンプレの NAT 設定確認に相当):
- web-sg の ingress 8000-8009 が lb-sg から許可されているか
- 両インスタンスが同じ VPC/サブネットにいるか

## 3. インターネットからの経路
```bash
curl -ik -H "Host: thinkxinc.com" https://<lb_public_ip>/
# DNS が LB の EIP を向いているか
dig thinkxinc.com
```

## 4. ログ
```bash
# web: uwsgi ログ
ssh ubuntu@<web_ip>
sudo journalctl -fu uwsgi_thinkx.service --output cat -n 3000
# LB: nginx ログ
ssh ubuntu@<lb_ip>
sudo journalctl -xeu nginx.service
sudo tail -f /var/log/nginx/access.log
```

## オンプレとの差分(消えた運用)
- `ip nat inside source static ...` / `write memory` → Security Group(terraform 管理)
- NAT テーブル枯渇 / `clear ip nat translation` → 発生しない(AWS のスケーラブル NAT)
- DDoS で 45.185.x.x が NAT を枯渇 → nginx の rate limit(既存) + SG で緩和
- レート制限は LB nginx の limit_req(basic/global 等)が従来通り有効
