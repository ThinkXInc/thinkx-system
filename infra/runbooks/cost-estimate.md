# Runbook: インフラ料金の月額概算

## 前提
- `infra/terraform` が構築する構成(VPC/EC2×2/EBS/パブリック IPv4)の on-demand 概算。
- ネットワーク・AWS 認証は不要。料金は東京(ap-northeast-1)on-demand の
  静的スナップショットをスクリプト内に持つ(2026-07 時点。変動する)。

## 手順
```bash
# env を指定(既定 staging)。24/7 で 1 ヶ月起動し続けた場合の月額とサービス別内訳。
infra/scripts/cost-estimate.sh prod
infra/scripts/cost-estimate.sh staging

# 停止が長い運用は実稼働 h を渡す(staging リハーサルは作成→試験→destroy で数時間)。
HOURS=3 infra/scripts/cost-estimate.sh staging

# 円換算も出す。
JPY_RATE=160 infra/scripts/cost-estimate.sh prod
```

## 出力の目安(2026-07 スナップショット時点)
- prod    24/7 : 約 **$73.59/月**(web t3.medium + lb t3.small が支配的)
- staging 24/7 : 約 **$40.93/月**
- staging リハーサル(3h で destroy): 約 **$3.99/月** —— EBS 満額分が支配的。
  `terraform destroy` 後は全サービス $0。

## インフラ変更のたびに再計算する
terraform 側の instance_type / volume_size / EIP を変えたら:
1. `infra/scripts/cost-estimate.sh` の「構成」ブロックを terraform に合わせて更新
   (料金表とサイズ表の唯一の同期ポイント。コメントに対応する .tf を明記済み)。
2. `infra/scripts/cost-estimate.sh <env>` を再実行して差分を確認。

### 自動発火(任意・settings 変更は各自で)
`.claude/settings.json` に PostToolUse フックを足すと、terraform の .tf を編集した直後に
自動で概算を出せる。ロジックは `infra/scripts/cost-hook.sh`(stdin の JSON から編集対象を
読み、`infra/terraform/*.tf` のときだけ概算を出す)に置き、settings からは薄く呼ぶだけにする。
settings の書き換えは Claude Code の権限外なので、`permissions` の兄弟キーとして各自で追加する
(JSON にコメントは書けない点に注意):
```json
  "hooks": {
    "PostToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [ { "type": "command",
          "command": "\"$CLAUDE_PROJECT_DIR/infra/scripts/cost-hook.sh\"" } ] }
    ]
  }
```
- 全 Edit/Write で発火するが、`cost-hook.sh` が対象を `infra/terraform/*.tf` に絞る。
- フックの stdout はトランスクリプト(Ctrl-R)に出る。

## 注意
- 料金は静的スナップショット。実費は AWS 料金ページ / Cost Explorer で確認する。
- パブリック IPv4 は 2024-02 以降、インスタンスに付いていても課金(反映済み)。
- EBS は「停止中」でも課金され、`terraform destroy` まで残る(HOURS を下げても満額)。
- データ転送(送信)は最初 100GB/月 無料。超過は $0.114/GB(本計算では無料枠内=$0 と仮定)。
