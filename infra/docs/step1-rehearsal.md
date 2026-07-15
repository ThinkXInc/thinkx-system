# I-STEP1: 最小インフラのリハーサル

売却前に「移行手順がワークする」確信を得るための、staging での通し検証。
**前提なし・いつでも開始可。全 apply/destroy は承認制。**

## 目的
staging の VPC/EC2×2(LB+web)を terraform で作成 → 経路確認 → destroy。
これが通れば「箱 + 中身 + 経路」の手順が正しいと機械的に確認できる。

## Prerequisites
- terraformコマンドがインストールされている

```bash

echo "1.15.8" > /Users/K00TSUKA/Sources/thinkx-system/infra/terraform/.terraform-version
terraform version
```
terraform version が Terraform v1.15.8 を返せばOK

## 手順

### 現状確認
```bash
cd infra
./scripts/status.sh staging
```

### 0. 準備(初回のみ)
```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars


echo "$(dig -4 +short myip.opendns.com @resolver1.opendns.com)/32" # SSH を許可する拠点グローバル IP を /32 で取得する

# --- EC2 キーペア(EC2 への SSH 秘密鍵)を用意する (リージョンは EC2 と同じ東京 ap-northeast-1 固定|キーペアはリージョン単位) / --key-name は tfvars の key_name(既定 thinkx-key)と必ず一致させる。---
# 1) 既存キーペアを確認
aws ec2 describe-key-pairs --region ap-northeast-1 \ 
  --query 'KeyPairs[].KeyName' --output text  
# 2) 無ければ作成(秘密鍵は ~/.ssh に保存し 400。コミット禁止・紛失=再作成) ★再実行時の注意: 前回作った 400(読み取り専用)のファイルが残っているとリダイレクト `>` が "permission denied" で弾かれる。先に rm -f で消す。(sudo は使わない。sudo だと root 所有の鍵ができ SSH が読めなくなる)
aws ec2 create-key-pair \
  --region ap-northeast-1 \
  --key-name supercom \
  --query 'KeyMaterial' --output text > ~/.ssh/supercom.pem
chmod 400 ~/.ssh/supercom.pem
# 鍵種別は既定 RSA。ed25519 にしたいなら AWS CLI v2 で --key-type ed25519 を付ける。
#   (aws-cli v1 は --key-type 非対応で「Unknown option」になる。v1 のままなら RSA でよい)
# 以降の ssh は鍵を明示: ssh -i ~/.ssh/supercom.pem ubuntu@<pub>
#   (あるいは ssh-add ~/.ssh/supercom.pem で agent に載せる)

# AWSコンソール: EC2 > ネットワーク&セキュリティ > キーペア > 「キーペアを作成」
# 名前=supercom / タイプ=RSA(CLI v2 なら ED25519 でも可)/ 形式=.pem → DL した .pem を ~/.ssh/ に置き chmod 400 ※右上のリージョンが「東京」であることを確認してから作成する

vim terraform.tfvars          # ↑で出た /32 を my_office_ip に、key_name を上で作った名前に
terraform init
```

### 1. staging を作る(承認制)
```bash
terraform state list                   # 今立っているリソース(=state に載っているもの)。空なら未作成
terraform fmt -check                   # .tf の整形チェック(崩れてたら非ゼロ終了・書き換えない)
../scripts/validate.sh                  # 構文・型・参照の静的検証(AWS 接続なし)
../scripts/status.sh staging     # ← 「(何も立っていない) 合計 $0.00/月」を確認
terraform validate                     # 構文・型・参照の静的検証(AWS 接続なし)
../scripts/plan-summary.sh staging     # 構成図(plan 由来・+作成/~変更/-削除で色分け)と月額。plan もこの中で走る
terraform apply -var="env=staging"     # 承認して作成。数分で LB+web が立つ
terraform output                        # IP と ssh コマンド(-i 付き)が出る
```

### 2. 中身を流す
```bash
WEB_IP=$(terraform output -raw web_private_ip)
LB_PUB=$(terraform output -raw lb_public_ip)
WEB_PUB=$(terraform output -raw web_public_ip 2>/dev/null || echo "")

# 2a. 各 EC2 の前処理(kaz 作成 + Deploy key 生成)。実行すると公開鍵が表示される
ssh -i ~/.ssh/supercom.pem ubuntu@"${WEB_PUB}" "REPOS='thinkx kazukiotsuka' bash -s" < ../setup/user-setup.sh
ssh -i ~/.ssh/supercom.pem ubuntu@"${LB_PUB}"  "REPOS='loadbalancer' bash -s"        < ../setup/user-setup.sh

# 2b. ★手動: 上で表示された公開鍵を GitHub の各 repo > Settings > Deploy keys に登録(write access 外す)

# 2c. 中身を流す(clone → build → 起動)
ssh -i ~/.ssh/supercom.pem ubuntu@"${WEB_PUB}" 'bash -s' < ../setup/web-setup.sh
WEB_IP="${WEB_IP}" DO_CERTBOT=no ssh -i ~/.ssh/supercom.pem ubuntu@"${LB_PUB}" 'bash -s' < ../setup/lb-setup.sh
```

### 3. 経路確認(受け入れ試験)
各サイトのルートゴールデン(`web-server/tests/golden/` の (rule,status) 一覧)を
staging LB に curl で照合する。ゴールデンが無い段階では最小スモーク:
```bash
# web 単体(ssh 先で)
curl -i localhost:8005            # thinkx 200 を確認
# LB -> web の内部疎通
curl -i "${WEB_IP}:8005"
# LB 経由(Host ヘッダで振り分け確認。staging は証明書無しなので http か -k)
curl -ik -H "Host: thinkxinc.com" https://"${LB_PUB}"/
```

### 4. 壊す(課金停止)
```bash
terraform destroy -var="env=staging"   # 承認して全消し。消し忘れゼロ
```

## 合格条件
- thinkx が localhost:8005 で 200
- LB 経由で thinkxinc.com の Host 振り分けが web に到達
- destroy 後に AWS コンソールで staging リソースが残っていないこと

## 注意
- transformism(8006)は S トラック未適用。リハーサルには載せない。
- 本番反映(I-STEP2)は Phase 3 完了 + 2026refactor→master マージの人間判断が前提。
