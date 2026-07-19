#!/usr/bin/env bash
# thinkx-system/infra/scripts/terraform_output.sh   【分類: 観測系(見るだけ・状態を変えない)】
#
# 指定環境の terraform output を表示する(環境ごとの envs/<env> ディレクトリを見る。切替なし)。
#   引数 1 個なら全 output、2 個なら指定 output を raw で出す(変数代入に使える)。
#
#   使い方: bash infra/scripts/terraform_output.sh <staging|prod> [output名]
#   例:     LB_IP=$(bash infra/scripts/terraform_output.sh staging lb_public_ip)

terraform_output() {
  local Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
  local env="${1:-}" name="${2:-}" tfdir
  tfdir="infra/terraform/envs/${1:-}"

  [ -n "$env" ] || { printf '%b\n' "${Y}注意: 環境の引数がありません。terraform_output.sh <staging|prod|eips> [output名] のように指定してください${Z}" >&2; return 1; }
  { [ "$env" = staging ] || [ "$env" = prod ] || [ "$env" = eips ]; } || { printf '%b\n' "${Y}注意: 引数は staging / prod / eips です(指定: $env)${Z}" >&2; return 1; }
  [ "$env" = eips ] && tfdir="infra/terraform/eips"
  [ -f "$tfdir/variables.tf" ] || { printf '%b\n' "${R}FAIL: terraform_output $tfdir が無い(リポジトリ直下で実行する)${Z}" >&2; return 1; }
  [ -f "$tfdir/terraform.tfstate" ] || { printf '%b\n' "${R}FAIL: terraform_output $env の state が無い(先に terraform_apply.sh $env)${Z}" >&2; return 1; }

  if [ -n "$name" ]; then
    terraform -chdir="$tfdir" output -raw "$name"
  else
    terraform -chdir="$tfdir" output
  fi
}

terraform_output "$@"
