# SECURITY — IAM と秘密情報の方針 (infra/docs/SECURITY.md)

このドキュメントが infra のセキュリティ方針の正。変更は必ずここに反映する。
★要確認 とある項目は未決定。決定したら本文に昇格させ、マークを消す。

## 原則

- 最小権限。使う操作だけを許可し、リージョンも ap-northeast-1 に限定する
- 権限昇格の防止。terraform に無制限の iam:* は与えない。IAM 操作は supercom-* リソースに限定したスコープ付きでのみ許可し、ユーザー作成・自分自身への権限付与はできない状態を保つ
- 実害の大きい破壊操作には明示 Deny(タグ条件)を置く。明示 Deny は後から Allow が足されても常に勝つ
- 秘密情報(鍵・トークン・証明書)は repo・setup スクリプト・Evernote に平文で置かない。設定値は repo にコミットし「clone してそのまま動く」を保つが、秘密だけは例外として手動配置する
- AWS 非依存を保つ。ログインは SSH(普遍的)を基本とし、AWS 固有機構(SSM 等)は採用条件を満たすまで使わない

## 命名 (supercom 統一)

- インフラのプロジェクトキーは supercom に統一(terraform リソース接頭辞・タグ Project=supercom・キーペア名等)
- terraform 実行用 IAM ユーザー: `supercom`(確定・作成済み。arn:aws:iam::027421896362:user/supercom)
- AWS キーペア名: `supercom-key` / ローカル秘密鍵ファイル: `~/.ssh/supercom.pem`。この 2 つは別物(AWS 上の登録名とローカルのファイル名)
- EC2 用 IAM ロール: `supercom-<env>-lb` 等、supercom- 接頭辞で作る(下記ポリシーのスコープと一致させるため必須)

## IAM ユーザー: supercom (Mac から terraform を実行する主体)

管理ポリシー(FullAccess 系)は付けない。inline policy 2 本のみ。

### inline 1: supercom-terraform-ec2

- Allow `ec2:*` を **ap-northeast-1 限定**(Condition: aws:RequestedRegion)
- 明示 Deny: TerminateInstances / DeleteVpc / DeleteSubnet / DeleteSecurityGroup を **Project=supercom タグの無いリソースに対して拒否**(Condition: StringNotEquals ec2:ResourceTag/Project)。アカウント内に残る他の EC2(旧 scraper 等)を terraform や誤操作から守る。terraform 管理リソースは全て Project=supercom タグ付きなので正常な destroy は通る
- なぜ名前スコープ(supercom-* のみ)にしないか: Describe 系は AWS 仕様で Resource 指定不可(terraform は毎回 Describe から始まる)、作成系は作成前に名前が無い、タグ条件の全面適用は tag 非対応リソースや RunInstances の複合認可で 403 デバッグ地獄になるため。region 限定 + 破壊系の明示 Deny が現実解。タグ条件による完全スコープ化は STEP2 ハードニング候補

### inline 2: supercom-terraform-iam

- Allow: iam:CreateRole / DeleteRole / GetRole / TagRole / PutRolePolicy / ListRolePolicies / InstanceProfile 系 — **Resource を role/supercom-* と instance-profile/supercom-* に限定**
- Allow: iam:PassRole — role/supercom-* 限定・渡し先 EC2 サービス限定(Condition: iam:PassedToService)
- 与えていないもの: ユーザー・グループ・ポリシーの作成/変更、自分自身への権限付与、supercom-* 以外のロール操作。terraform が作れるのは supercom-* のロールだけで、それを assume できるのは EC2 のみ。これが権限昇格の防止線

### 旧ユーザー transcript-deployer の廃止

- 調査結果: .env の平文キー 2 つは transcript-deployer のものではない(別ユーザー由来)→ 削除してもオンプレの SES/メールは壊れない。利用実態は Mac の terraform のみ(S3 は 904 日前=scraper 残骸、ELB/CW/ASG は未使用)。付与されていた AmazonS3FullAccess / AmazonEC2FullAccess は広すぎた
- 移行手順(順序厳守): supercom 作成 → inline 2 本付与 → Mac の ~/.aws 差し替え → sts get-caller-identity で user/supercom 確認 → terraform plan 完走確認(済) → apply → **transcript-deployer を削除**。旧 role/transcript(PassRole 先の残骸)も削除候補
- 現在地: plan 完走まで確認済み(3 to add, 1 to change, 0 to destroy)。apply → 削除は実行待ち

## EC2 の IAM ロール

- **LB: `supercom-<env>-lb` ロールを付ける(採用決定)**。inline policy `certbot-dns-route53` のみ:
  - route53:ListHostedZones / GetChange (Resource: *)
  - route53:ChangeResourceRecordSets (Resource: hostedzone/* 限定)
  - 用途は certbot の DNS-01 検証だけ。これ以外の AWS 権限は持たない
- **web: ロールなし**。AWS 認証情報を一切持たない(現状維持)
- 将来オプション(提案済み・未採用): GitHub PAT を SSM Parameter Store に SecureString (/supercom/github_token) で預け、EC2 ロールに ssm:GetParameter (/supercom/* 限定) + kms:Decrypt を付与して Deploy key 登録を自動化。同ロールに ses:SendEmail を足せば .env の平文 AWS キー(send_mail 用)も廃止できる。採用トリガー: Deploy key の手動登録が負担になった時・EC2 再作成の頻度が高い時

## TLS 証明書: certbot --dns-route53 で EC2 上で取得 (採用決定)

- LB ロール(上記)+ certbot dns-route53 プラグインで、DNS-01 により LB 上で発行・更新する。証明書・秘密鍵をローカルに置かない
- リハーサル(staging)は `--test-cert` で行い、Let's Encrypt のレート制限(同一ドメイン 5 回/週)を消費しない。prod は --test-cert を外すだけ
- 実行例: `sudo certbot certonly --dns-route53 --test-cert --agree-tos -m admin@thinkxinc.com -d thinkxinc.com -d '*.thinkxinc.com'`
- 旧方式(オンプレ実物を infra/certs/lb-certs.tgz で持ち込み)は移行期の暫定であり、certbot チェーンの実証が済んだら廃止する。★廃止時に infra/certs/ の tgz をローカルから削除すること(「秘密をローカルに置かない」原則への回帰)。それまでの間 infra/certs/ は .gitignore 必須・コミット禁止
- ★要確認: sixths.ai・jessicas.online 等の他ドメインも certbot 管理へ寄せるか(thinkxinc.com で実証後に決定)

## EC2 へのログイン: SSH のみ (SSM Session Manager は不採用と決定済み)

- キーペア supercom-key (ローカルは ~/.ssh/supercom.pem) + Security Group で 22 番を拠点 IP に限定
- PasswordAuthentication は AWS の既定で no、authorized_keys は cloud-init が設置。setup スクリプトでの sshd 変更は行わない
- SSM Session Manager は利便(22 閉鎖・鍵レス・操作ログ)と引き換えに AWS ロックインのため見送り。採用する場合も SSM 用ロールは supercom-* 接頭辞で作り、supercom-terraform-iam のスコープ内で扱う

## GitHub 認証: repo 単位 read-only Deploy key

- アカウント鍵(全 repo read/write)は EC2 に置かない。repo ごとに deploy_<repo> 鍵を EC2 上で生成し、公開鍵のみ GitHub に登録(write access は外す)。秘密鍵は EC2 から出ない
- ~/.ssh/config の Host 別名 (github-<repo>) で鍵を使い分ける。submodule のように .gitmodules が素の github.com URL を持つ場合は、kaz の git 設定の url.insteadOf で別名へ透過変換する(repo はパッチしない)
- Deploy key が必要なのは「EC2 が実際に clone する repo」だけ。数は構成に依存する:
  - quantz-web を EC2 で動かす現構成(staging リハーサル実績): web = quantz-web + submodule 3 (libcommon / llm / simplicity) + thinkx / kazukiotsuka、lb = loadbalancer で計 7
  - ★要確認: 別途の設計レビューでは libcommon / simplicity は vendoring 済みで clone 不要・quantz-web の搭載自体が未定として 3〜4 repo と見積もられている。vendoring を採用すれば鍵数は削減できる。本番構成の確定時に整合させること
- 詳細と経緯は github_deploy_key.md

## 秘密情報の配置 (現行運用)

- .env (AWS / Stripe の平文キー): repo・setup に置かない。手元から scp → /src/quantz-web/.env (chown kaz:serveradmins, chmod 640)。★.env 内の AWS キーの発行元ユーザーを特定し、ローテーション/廃止(SES を EC2 ロール化)を検討すること
- tfstate: IP・リソース ID が平文で入るため公開厳禁。S3 backend にする場合は専用バケット(バージョニング有効 + パブリックアクセス全ブロック)を使い、他用途と混ぜない

## 再検討トリガー (この文書を見直すタイミング)

- apply 完了 → transcript-deployer と旧 role/transcript を削除し、本文の「実行待ち」を消す
- certbot チェーン実証(staging --test-cert 成功)→ tgz 持ち込み方式を廃止し infra/certs/ を削除。他ドメインの certbot 化を決定
- Deploy key の手動登録が負担になった → EC2 ロール + SSM Parameter Store 方式へ移行
- 本番構成の確定 → repo/vendoring の整合(鍵数)を確定
- STEP2 ハードニング → EC2 のタグ条件による完全スコープ化、22 番閉鎖(SSM 再検討)を評価
- terraform で権限不足(UnauthorizedOperation)が出た → 足りないアクションを 1 つずつポリシーに追加(ワイルドカードで広げない)