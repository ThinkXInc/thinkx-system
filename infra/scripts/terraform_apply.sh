#!/usr/bin/env bash
# thinkx-system/infra/scripts/terraform_apply.sh   【分類: 変更系(インフラ作成/変更・オーナー承認つき)】
#
# 指定環境の terraform apply を定型化する(生 terraform コマンドを人間に打たせない)。
#   - workspace(state の分離面)を env から自動選択: prod=default / staging=staging。
#     workspace とは terraform の「作ったリソースの台帳」の切替で、選び間違えると
#     staging のつもりで prod の台帳に適用してしまう。人間には選ばせずここで固定対応。
#   - 先に plan の全差分を表示 → 逆環境の名前が混ざっていたら中止 → yes で apply
#   - terraform.tfvars が無ければ赤 FAIL(my_office_ips を自動補完すると SG 許可元を
#     現在地 1 個で上書きしてしまうため、apply では補完しない)
#
#   使い方: bash infra/scripts/terraform_apply.sh <staging|prod>

set -euo pipefail

terraform_apply() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local env="${1:-}" tfdir="infra/terraform"
  local ws=default other plan_out ans

  [ -n "$env" ] || { printf '%b\n' "${Y}注意: 環境の引数がありません。terraform_apply.sh <staging|prod> のように指定してください${Z}"; return 1; }
  { [ "$env" = staging ] || [ "$env" = prod ]; } || { printf '%b\n' "${Y}注意: 引数は staging か prod です(指定: $env)${Z}"; return 1; }
  [ -f "$tfdir/variables.tf" ] || { printf '%b\n' "${R}FAIL: terraform_apply $tfdir が無い(リポジトリ直下で実行する)${Z}"; return 1; }
  [ -f "$tfdir/terraform.tfvars" ] || { printf '%b\n' "${R}FAIL: terraform_apply $tfdir/terraform.tfvars が無い(my_office_ips を書いてから実行。例は terraform.tfvars.example)${Z}"; return 1; }

  terraform -chdir="$tfdir" init -input=false > /dev/null
  [ "$env" = staging ] && ws=staging
  terraform -chdir="$tfdir" workspace select -or-create "$ws" > /dev/null
  echo "env=$env / workspace=$(terraform -chdir="$tfdir" workspace show)(state の分離面。prod=default / staging=staging)"

  plan_out="$(mktemp)"
  terraform -chdir="$tfdir" plan -input=false -lock-timeout=10s -var "env=$env" | tee "$plan_out"

  other=prod; [ "$env" = prod ] && other=staging
  if grep -q "supercom-$other" "$plan_out"; then
    printf '%b\n' "${R}FAIL: terraform_apply 差分に supercom-$other(逆環境)が混入。中止${Z}"; return 1
  fi
  if grep -q "No changes." "$plan_out"; then
    printf '%b\n' "${G}OK: terraform_apply $env 差分なし(現状と一致)。何もしない${Z}"; return 0
  fi

  printf '%b' "${Y}上の差分どおり $env に apply する? [yes/N] ${Z}"
  read -r ans
  [ "$ans" = yes ] || { echo "中止(何も変更していない)"; return 1; }

  terraform -chdir="$tfdir" apply -input=false -lock-timeout=10s -auto-approve -var "env=$env" \
    || { printf '%b\n' "${R}FAIL: terraform_apply $env apply が失敗。上の出力を確認${Z}"; return 1; }
  echo
  echo "── outputs ──"
  terraform -chdir="$tfdir" output
  printf '%b\n' "${G}OK: terraform_apply $env apply 完了${Z}"
}

terraform_apply "$@"
