#!/usr/bin/env bash
# thinkx-system/infra/scripts/destroy_env.sh   【分類: 変更系(環境を破壊する・オーナー承認前提)】
#
# 指定環境の EC2/VPC 一式を terraform で破壊する。
#   - my_office_ip(s) は現在の IP を自動検出して渡す(destroy では SG 差分にしか使われず
#     実質無関係だが、default の無い変数は tfvars が無いと terraform が対話で聞いてくるため)
#   - 先に plan -destroy の全差分を表示 → yes 入力で destroy 実行(N なら何もせず終了)
#   - 逆環境の名前(例: staging 指定時に supercom-prod)が差分に混ざっていたら中止
#   - monorepo の state は workspace で環境分離(prod=default / staging=staging)。
#     workspace "staging" が存在するディレクトリでのみ自動 select する(旧リポジトリは default のみ)
#
#   使い方: bash infra/scripts/destroy_env.sh <staging|prod> [terraformディレクトリ]
#   例:     bash infra/scripts/destroy_env.sh staging
#           bash infra/scripts/destroy_env.sh staging ~/Sources/infra/terraform

set -euo pipefail

destroy_env() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local env="${1:-}" tfdir="${2:-infra/terraform}"
  local ip other plan_out ans

  { [ "$env" = staging ] || [ "$env" = prod ]; } || { printf '%b\n' "${R}FAIL: destroy_env usage: destroy_env.sh <staging|prod> [terraformディレクトリ]${Z}"; return 1; }
  [ -f "$tfdir/variables.tf" ] || { printf '%b\n' "${R}FAIL: destroy_env $tfdir に variables.tf が無い(terraform ディレクトリを指定する)${Z}"; return 1; }

  ip="$(curl -s --max-time 10 https://checkip.amazonaws.com)"
  echo "現在のグローバル IP: $ip を my_office_ip(s) に自動指定(destroy では SG 差分にのみ関わり実質無関係。tfvars 無しでも対話プロンプトを出させないため)"

  # provider 未取得や lock 不整合で plan が止まらないよう先に init(インフラには何も触らない準備操作)
  terraform -chdir="$tfdir" init -input=false -upgrade > /dev/null

  local -a varopt=(-var "env=$env")
  if grep -q 'variable "my_office_ips"' "$tfdir/variables.tf"; then
    varopt+=(-var "my_office_ips=[\"$ip/32\"]")
  else
    varopt+=(-var "my_office_ip=$ip/32")
  fi

  if terraform -chdir="$tfdir" workspace list 2>/dev/null | tr -d '* ' | grep -qx staging; then
    if [ "$env" = staging ]; then terraform -chdir="$tfdir" workspace select staging; else terraform -chdir="$tfdir" workspace select default; fi
    echo "workspace: $(terraform -chdir="$tfdir" workspace show)"
  fi

  plan_out="$(mktemp)"
  terraform -chdir="$tfdir" plan -destroy -input=false -lock-timeout=10s "${varopt[@]}" | tee "$plan_out"

  other=prod; [ "$env" = prod ] && other=staging
  if grep -q "supercom-$other" "$plan_out"; then
    printf '%b\n' "${R}FAIL: destroy_env 差分に supercom-$other(逆環境)が混入。中止${Z}"; return 1
  fi
  if ! grep -q "to destroy" "$plan_out"; then
    printf '%b\n' "${Y}WARN: destroy_env 破壊対象 0 件(state が空か環境違い)。何もしない${Z}"; return 0
  fi

  printf '%b' "${Y}上の差分どおり $env を destroy する? [yes/N] ${Z}"
  read -r ans
  [ "$ans" = yes ] || { echo "中止(何も変更していない)"; return 1; }

  terraform -chdir="$tfdir" destroy -input=false -lock-timeout=10s -auto-approve "${varopt[@]}" \
    && printf '%b\n' "${G}OK: destroy_env $env($tfdir)を破壊完了。EIP は解放済み${Z}" \
    || { printf '%b\n' "${R}FAIL: destroy_env $env destroy が失敗。上の出力を確認${Z}"; return 1; }
}

destroy_env "$@"
