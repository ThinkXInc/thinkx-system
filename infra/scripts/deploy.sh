#!/usr/bin/env bash
# thinkx-system/infra/scripts/deploy.sh   【分類: 変更系(サーバーへ反映する・本番は承認ゲートそのもの)】
# 
# usage:
#   bash infra/scripts/deploy.sh <staging|prod> <thinkx|kazukiotsukacom|transformism|nginx-web-root|loadbalancer|...>
#
# example:
#   bash infra/scripts/deploy.sh prod thinkx
#   bash infra/scripts/deploy.sh staging thinkx nginx-web-root loadbalancer
#
# 実行されること:
#   sudo -u kaz git -C /src/thinkx-system pull
#   run/restart_<service>.sh

set -euo pipefail

deploy() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local env="${1:-}" web lb svc need_web=0 need_lb=0

  [ -n "$env" ] || { printf '%b\n' "${Y}注意: 環境の引数がありません。deploy.sh <staging|prod> <サービス...> のように指定してください${Z}"; return 1; }
  { [ "$env" = staging ] || [ "$env" = prod ]; } || { printf '%b\n' "${Y}注意: 第1引数は staging か prod です(指定: $env)${Z}"; return 1; }
  shift
  [ "$#" -ge 1 ] || { printf '%b\n' "${Y}注意: 反映するサービスがありません。thinkx kazukiotsukacom transformism nginx-web-root loadbalancer から指定してください${Z}"; return 1; }

  web=supercom-web1; lb=supercom-lb1
  [ "$env" = staging ] && web=supercom-web1-stg && lb=supercom-lb1-stg

  for svc in "$@"; do
    case "$svc" in
      thinkx|kazukiotsukacom|transformism|nginx-web-root) need_web=1 ;;
      loadbalancer) need_lb=1 ;;
      *) printf '%b\n' "${R}FAIL: deploy 不明なサービス: $svc${Z}"; return 1 ;;
    esac
    [ -f "infra/run/restart_$svc.sh" ] || { printf '%b\n' "${R}FAIL: deploy infra/run/restart_$svc.sh が無い(リポジトリ直下で実行する)${Z}"; return 1; }
  done

  echo "== deploy $env: git pull =="
  [ "$need_web" = 1 ] && ssh -o ConnectTimeout=8 "$web" 'sudo -u kaz git -C /src/thinkx-system pull'
  [ "$need_lb" = 1 ] && ssh -o ConnectTimeout=8 "$lb" 'sudo -u kaz git -C /src/thinkx-system pull'

  for svc in "$@"; do
    echo "== deploy $env: restart $svc =="
    case "$svc" in
      loadbalancer) ssh -o ConnectTimeout=8 "$lb" 'bash -s' < "infra/run/restart_$svc.sh" ;;
      *)            ssh -o ConnectTimeout=8 "$web" 'bash -s' < "infra/run/restart_$svc.sh" ;;
    esac
  done

  printf '%b\n' "${G}OK: deploy $env 反映完了($*)${Z}"
}

deploy "$@"
