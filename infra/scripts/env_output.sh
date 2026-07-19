#!/usr/bin/env bash
# thinkx-system/infra/scripts/env_output.sh   【分類: 観測系(インフラ無変更。workspace の選択のみ行う)】
#
# 指定環境の terraform output を表示する(workspace を env から自動選択し、混在を防ぐ)。
#   引数 1 個なら全 output、2 個なら指定 output を raw で出す(変数代入に使える)。
#
#   使い方: bash infra/scripts/env_output.sh <staging|prod> [output名]
#   例:     LB_IP=$(bash infra/scripts/env_output.sh staging lb_public_ip)

env_output() {
  local Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
  local env="${1:-}" name="${2:-}" tfdir="infra/terraform" ws=default

  [ -n "$env" ] || { printf '%b\n' "${Y}注意: 環境の引数がありません。env_output.sh <staging|prod> [output名] のように指定してください${Z}" >&2; return 1; }
  { [ "$env" = staging ] || [ "$env" = prod ]; } || { printf '%b\n' "${Y}注意: 引数は staging か prod です(指定: $env)${Z}" >&2; return 1; }
  [ -f "$tfdir/variables.tf" ] || { printf '%b\n' "${R}FAIL: env_output $tfdir が無い(リポジトリ直下で実行する)${Z}" >&2; return 1; }

  [ "$env" = staging ] && ws=staging
  terraform -chdir="$tfdir" workspace select "$ws" > /dev/null 2>&1 || { printf '%b\n' "${R}FAIL: env_output workspace $ws が無い(先に apply_env.sh $env)${Z}" >&2; return 1; }

  if [ -n "$name" ]; then
    terraform -chdir="$tfdir" output -raw "$name"
  else
    terraform -chdir="$tfdir" output
  fi
}

env_output "$@"
