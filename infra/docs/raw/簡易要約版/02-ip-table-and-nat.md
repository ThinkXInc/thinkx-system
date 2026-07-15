# IP 表・NAT トラブルシュート(原本)

## IP 表
```
192.168.1.9 7777 supercom3a (Main)
192.168.1.7 4444 supercom3b (DB)
192.168.1.6 3333 supercom3L (Loadbalancer)
192.168.1.8 6666 supercom2 (web)
```
基本的に電源が落ちても IP は変わらないが、ルーターで書き込み(write memory)を
忘れていると設定が消えることがある。Cisco の設定を変えたら write memory を忘れずに。

global IP: 123.226.234.127

## サイトのアクセス構造
1. LB で webserver にリクエストが渡される
2. webserver の nginx で FQDN により url の頭を書き換え

## トラブルシュート(サイトが返らない)
```
# 各サーバーに ssh できるか
ssh supercom3L
ssh supercom3a / ssh supercom3b / ssh supercom2

# NAT 設定確認(Cisco)
show running-config | include ip nat inside source static
# 例: supercom2 192.168.1.8 の 6666->22 が消えていた(write memory 忘れ)
ip nat inside source static tcp 192.168.1.8 22 interface Dialer1 6666

# LB の 443 が空いているか
ssh supercom3L
sudo netstat -tuln | grep 443
nc -vz 123.226.234.127 443

# web が返るか
ssh supercom2
curl -i localhost:8005      # thinkx/transformism
curl -i localhost:8000      # quantz

# LB から
curl -i 192.168.1.8:8005

# NAT テーブル枯渇(DDoS)
show ip nat statistics       # dynamic が上限
show ip nat translations     # 45.185.x.x から大量アクセス = 攻撃
clear ip nat translation *   # クリア
# 本質的対処: レート制限 / NAT タイムアウト短縮
```

> 移行後: このセクションの Cisco/NAT 運用は消滅。`runbooks/troubleshoot.md` を参照。
