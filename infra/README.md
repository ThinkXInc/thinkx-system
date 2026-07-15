# infra — thinkx-system の AWS 移行

オンプレ(Cisco + supercom 群)を **VPC + EC2 のみ**で再現する一式。
箱=terraform、中身=AWS 非依存 bash、運用=runbooks。

## これは何か
- supercom3L(LB)+ supercom2(web)を EC2 2 台に載せ替える
- supercom3a は手元に残す(移行対象外)
- supercom3b/3c は売却(このリポジトリの対象外)

## クイックスタート(リハーサル = I-STEP1)
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # my_office_ip / key_name を埋める
terraform init
terraform apply -var="env=staging"             # staging を作る(承認制)
terraform output                                # IP と ssh コマンド

# 中身を流す
ssh ubuntu@<web_pub> 'bash -s' < ../setup/web-setup.sh
WEB_IP=<web_priv> DO_CERTBOT=no ssh ubuntu@<lb_pub> 'bash -s' < ../setup/lb-setup.sh

# 経路確認 → 壊す
terraform destroy -var="env=staging"
```
詳細は `docs/step1-rehearsal.md`。

## 月額の目安(1USD≒162円)
| | 構成 | 月額 |
|---|---|---|
| prod | LB t3.small + web t3.medium + EBS/EIP/転送 | 約1.0〜1.1万円 |
| staging | LB t3.micro + web t3.small(必要時のみ起動) | 数千円 |

Claude Code は既存の Max 5x($100)枠内(対話利用は追加課金なし)。

## ディレクトリ
```
infra/
├── CLAUDE.md              # Claude Code 用の運用規範・権限境界
├── README.md             # これ
├── .gitignore
├── terraform/            # 箱(env で prod/staging 切替)
│   ├── main.tf           #   VPC/subnet/IGW/route
│   ├── security.tf       #   Security Group(Cisco NAT/ACL 代替)
│   ├── instances.tf      #   EC2(LB/web)+ EIP
│   ├── variables.tf      #   env 変数・派生値
│   ├── outputs.tf        #   IP/ssh コマンド
│   └── terraform.tfvars.example
├── setup/                # 中身(AWS 非依存 bash)
│   ├── web-setup.sh
│   └── lb-setup.sh
├── runbooks/             # 日常運用
│   ├── restart-site.md
│   ├── deploy-site.md
│   ├── tls-renew.md
│   ├── lb-config.md
│   └── troubleshoot.md
└── docs/
    ├── step1-rehearsal.md
    └── raw/              # 弊社の生ドキュメント(オンプレ手順の原本)
```

## 重要な前提(リファクタリング作戦より)
- libcommon は vendoring 済み → デプロイに submodule 取得不要
- デプロイ ref は人間指示(既定 2026refactor→master マージ後 v2.1.0)
- transformism は S トラック未適用 → 載せる前に人間判断
- メールは SES / MongoDB は静的サイトの問い合わせに不要
- I-STEP2(本番載せ替え)は Phase 3 完了 + マージ判断が前提
