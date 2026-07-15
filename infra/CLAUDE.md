# infra — AWS 移行(I トラック)

thinkx-system の I トラック。オンプレ(Cisco + supercom 群)を AWS の
**VPC + EC2 のみ**(マネージド最小)で再現する。箱=terraform、中身=AWS 非依存 bash、
運用=runbooks。

## 構成
- **LB**(supercom3L 相当): nginx で TLS 終端・ドメイン振り分け。固定 IP `192.168.x.10`
- **web**(supercom2 相当): nginx(静的配信) + uwsgi(thinkx/transformism/kazukiotsuka)。固定 IP `192.168.x.11`
- **3a は手元実機**(クラウド外・重い計算)。移行対象外
- prod=`192.168.1.0/24` / staging=`192.168.2.0/24` を `env` で作り分け

## ディレクトリ
- `terraform/` — 箱(VPC/subnet/IGW/SG/EC2/EIP)。env で prod/staging 切替
- `setup/` — 中身(`web-setup.sh` / `lb-setup.sh`)。AWS 非依存 bash。ssh で流す
- `runbooks/` — 日常運用(再起動/デプロイ/TLS/LB 設定/障害対応)
- `docs/` — `step1-rehearsal.md`(I-STEP1)ほか

## 箱の操作(terraform/)
```bash
terraform plan  -var="env=staging"     # 差分提示(自由)
terraform apply -var="env=staging"     # 承認制
terraform destroy -var="env=staging"   # 承認制
```

## 中身の構築(setup/)
```bash
ssh ubuntu@<web_pub> 'bash -s' < setup/web-setup.sh
WEB_IP=<web_priv> DO_CERTBOT=no ssh ubuntu@<lb_pub> 'bash -s' < setup/lb-setup.sh
```

## 構築の指針(D-32)

1. **production の新設は monorepo 前提の再現性検証を兼ねる。**
   手順は terraform apply → setup/*.sh → monorepo clone → run → 全ゴールデン sweep。
   構築中に判明したドキュメント・スクリプトの抜けは、手作業で埋めて先に進むことを
   禁止する。setup / runbooks / terraform に反映してから次の手順へ進む。
   修正の完了指標は「同じ手順をもう一度流せば素通りすること」。
   抜けの露出は失敗ではなく本工程の成果である。
2. **既存 staging はカットオーバーまで変更禁止。**
   prod 構築で詰まったときの「正解の参照」として維持する。
   staging の再構築はカットオーバー後(I-STEP3)に prod と同一手順で行う。

## リファクタリング作戦からの制約(必読・仮定禁止)
1. **libcommon は vendoring 済み(v2 系)**。デプロイに `git submodule update` は**不要**
   (thinkx の playbooks submodule のみ従来通り)。setup に libcommon submodule 取得を
   書かない・残っていたら削除する。
2. **デプロイするブランチ/タグは人間が指示**(既定: 2026refactor → master マージ後に
   v2.1.0 一括)。**勝手に master を前提にしない**。setup は `DEPLOY_REF` で受ける。
3. **受け入れ試験は機械化**: 各サイトの `web-server/tests/golden/` のルートゴールデン
   ((rule,status) 全 GET)を入力に、ステージング LB へ curl で全ルート照合。
   quantz を載せる場合は Q-2 スイート(route sweep + API 3 型)が受け入れ試験を兼ねる。
4. **transformism(uwsgi 8006)は S2 カットオーバー完遂済み(2026-07・オーナー裁定 2026-07-15)**。
   thinkx / kazukiotsukacom と同型で 2026refactor からデプロイ可(vendored libcommon v2.1.0・golden あり・
   libcommon submodule 除去済み)。`setup_transformism.sh` で起動。受け入れ = ルートゴールデン(/→200・/static→404)。
5. メールは **SES**(移行で変化なし)。EC2 に IAM ロールを付ければ `.env` 平文アクセスキーを
   廃止できる(改善候補・人間判断)。**MongoDB は静的サイト群の問い合わせには不要**(実測済み)。
6. TLS は `--manual` から **`--dns-route53`** に変更(対話廃止・自動更新)。Route53 権限は
   EC2 の IAM ロールで付与。

## 検証コマンド(変更時)
- `terraform fmt -check` / `terraform validate` / `terraform plan`(差分全件提示)
- setup の変更は shellcheck(あれば)+ **staging での実流し**で検証。**本番に直接流さない**。
- **bash を書く前に `docs/coding_guides/bash.md` を読む(規範)**。特に観測系(status/plan-summary 等)は `exit`・`set -e` 禁止・`cd` はサブシェル ── source されると呼び出し元シェルを壊すため。

## 禁止事項(settings と二重で強制)
- settings・本ファイル・ワークスペース制御文書の書き換え
- `terraform apply/destroy` の無承認実行、`aws iam` 操作、`ec2 terminate-instances`
- `*.tfstate` / `*.tfvars` / `*.pem` / credentials の読み書き
- staging で未検証の setup 変更を本番へ適用すること
- 他リポジトリ(simplicity/libcommon/各サイト)のコード変更
  (デプロイはコードを「取得して流す」だけ。修正が必要なら findings として報告し停止)

## 承認点(人間)
- terraform apply/destroy
- 本番デプロイの ref 指定
- transformism を載せるか / quantz を載せるか
- I-STEP2 の開始(前提: Phase 3 完了 + 2026refactor→master マージ)
