# 現行システム構成(オンプレ)と移行後の対応

生ドキュメント(`docs/raw/`)を統合し、移行の判断に必要な形にまとめたもの。

## オンプレの物理構成
| ホスト | 機器 | 役割 | ローカル IP | 移行 |
|---|---|---|---|---|
| supercom3a | Supermicro 4124GS-TNR (EPYC 7313 ×2 / 512GB) | main(重い計算) | 192.168.1.9 | **手元に残す** |
| supercom3b | Supermicro 4124GS-TNR (+ A5000 / 15TB×2) | main/DB/file | 192.168.1.7 | **売却** |
| supercom3c | Supermicro SYS-220GP-TNR | DB | 192.168.1.5 系 | **売却** |
| supercom3L | Supermicro SYS-510T-WTR | LB(nginx) | 192.168.1.6 | **クラウド** |
| supercom2  | tower (Xeon 4208 / 64GB) | web/app | 192.168.1.8 | **クラウド** |
| Cisco C1111-8P | ルーター | NAT/PPPoE | 192.168.1.1 | **VPC で代替** |
| — | — | グローバル IP | 123.226.234.127 | **EIP で代替** |

## アプリと配信(supercom2 上)
LB(supercom3L)が TLS 終端して、ドメインごとに supercom2 のポートへ振り分け。

| ドメイン | バックエンド | uwsgi サービス |
|---|---|---|
| thinkxinc.com | :8005 | uwsgi_thinkx |
| truetechjapan.com | :8005 | uwsgi_thinkx(同一 app 内) |
| nntmapp.com | :8005 | uwsgi_thinkx |
| nntm.thinkxinc.com | :8005(/nntm/ へ rewrite) | uwsgi_thinkx |
| transformism.art | :8006 | uwsgi_transformism |
| kazukiotsuka.com | :8007 | uwsgi_kazukiotsuka |
| quantz.thinkxinc.com | :8000 ほか(stream:8001=3a, files:8009=3b) | uwsgi_quantz |

**実プロセスは 4 つ**(thinkx/transformism/kazukiotsuka/quantz)。5 ドメインでもアプリは thinkx 1 本が捌く。

web 側も nginx が動いており、静的ファイル(img/js/css/video/fonts/documents)を
`root .../views/` から直接配信、動的は uwsgi へプロキシ(unix socket)。

## リクエスト経路
```
[インターネット] --443--> [LB nginx (TLS 終端/振り分け)]
                              --192.168.1.8:8005--> [web nginx (静的配信/rewrite)]
                              --unix socket--> [uwsgi (Flask)]
```

## 外部依存
- **メール**: AWS SES(`libcommon.mail.Mail`)。問い合わせ確認メール。移行で変化なし
- **問い合わせ通知**: Discord webhook(apply/inquiry で別 webhook)
- **決済**: Stripe(quantz)
- **問い合わせは DB 保存しない** → 静的サイト群に MongoDB は不要(実測)

## オンプレ → AWS 対応
| オンプレ | AWS |
|---|---|
| Cisco ルーター本体 | VPC + Internet Gateway |
| LAN 192.168.1.0/24 | subnet 192.168.1.0/24(prod) |
| グローバル IP 123.226.234.127 | Elastic IP |
| `ip nat inside source static ... 443` | LB SG ingress 443 + EIP |
| `ip nat ... 22 ... 6666`(SSH ポートフォワード) | SG ingress 22(拠点 IP 限定) |
| バックエンド 192.168.1.8:8005 への内部到達 | web SG が LB SG からのみ許可 |
| DHCP pool | private_ip 固定指定 |
| 動的 NAT overload(外向き) | route table + IGW |
| `write memory` 忘れで設定消失 | terraform(コード管理・保存し忘れ不可) |
| NAT テーブル枯渇 / DDoS(45.185.x.x) | スケーラブル NAT + nginx rate limit + SG |
| certbot --manual(手コピペ) | certbot --dns-route53(全自動 + 自動更新) |
| supercom2 の 192.168.1.8 | web EC2 の 192.168.1.11(固定) |
| supercom3L の 192.168.1.6 | LB EC2 の 192.168.1.10(固定) |

## コスト(参考。1USD≒162円)
- データセンター実機: 4000W 月22万 / 15000W 月48万(オンプレ)
- AWS 移行後: prod 2 台で月1.0〜1.1万円 + Claude Code は既存 $100 枠内
- 重い計算(3a 相当)を仮に AWS 化すると i4i.32xlarge 月150万 → **3a を手元に残す判断が正しい**
