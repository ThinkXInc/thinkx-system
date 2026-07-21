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
#   git fetch origin && git diff --quiet && git diff --cached --quiet && git merge --ff-only origin/<ref>
#   bash /src/thinkx-system/infra/run/restart_<service>.sh
#
#   staging -> origin/develop に合わせる
#   prod    -> origin/production に合わせる
#
# 【重要】サービス引数が選ぶのは「再起動するプロセス」だけである。
#   撒かれるコードは常に全サービス分(git はリポジトリ全体を動かすため)。
#   `deploy.sh prod thinkx` は「thinkx だけ本番に出す」ではなく
#   「全サービスのコードを本番に合わせ、thinkx のプロセスだけ再起動する」。
#   サービスを選んで出す仕組みは持っていない(足並みを揃える方式・デプロイ手順書の原則)。
#
# 【なぜ merge --ff-only か】
#   pull(ref 非指定)はサーバーが今 checkout しているブランチに依存するため、
#   「prod は常に production」が保証されない。かといって reset --hard は
#   サーバー上の直接変更を無言で消す。ff-only + dirty チェックなら、
#   きれいなときだけ早送りし、何か手が入っていれば消さずに止めて人間に渡す。

set -euo pipefail

deploy() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local env="${1:-}" web lb svc ref need_web=0 need_lb=0

  [ -n "$env" ] || { printf '%b\n' "${Y}注意: 環境の引数がありません。deploy.sh <staging|prod> <サービス...> のように指定してください${Z}"; return 1; }
  { [ "$env" = staging ] || [ "$env" = prod ]; } || { printf '%b\n' "${Y}注意: 第1引数は staging か prod です(指定: $env)${Z}"; return 1; }
  shift
  [ "$#" -ge 1 ] || { printf '%b\n' "${Y}注意: 再起動するサービスがありません。thinkx kazukiotsukacom transformism nginx-web-root loadbalancer から指定してください${Z}"; return 1; }

  web=supercom-web1; lb=supercom-lb1; ref=production
  [ "$env" = staging ] && web=supercom-web1-stg && lb=supercom-lb1-stg && ref=develop

  for svc in "$@"; do
    case "$svc" in
      thinkx|kazukiotsukacom|transformism|nginx-web-root) need_web=1 ;;
      loadbalancer) need_lb=1 ;;
      *) printf '%b\n' "${R}FAIL: deploy 不明なサービス: $svc${Z}"; return 1 ;;
    esac
    [ -f "infra/run/restart_$svc.sh" ] || { printf '%b\n' "${R}FAIL: deploy infra/run/restart_$svc.sh が無い(リポジトリ直下で実行する)${Z}"; return 1; }
  done

  echo "== deploy $env: Mac に全履歴を fetch(バックアップ・D-55)=="
  git fetch origin

  echo "== deploy $env: origin/$ref へ早送り(汚れていたら止める)=="
  for host in $([ "$need_web" = 1 ] && echo "$web"; [ "$need_lb" = 1 ] && echo "$lb"); do
    ssh -o ConnectTimeout=8 "$host" "
      sudo -u kaz git -C /src/thinkx-system fetch --quiet origin || exit 1
      sudo -u kaz git -C /src/thinkx-system diff --quiet || { echo 'FAIL: 未コミットの変更がある'; sudo -u kaz git -C /src/thinkx-system status --short; exit 2; }
      sudo -u kaz git -C /src/thinkx-system diff --cached --quiet || { echo 'FAIL: ステージ済みの変更がある'; sudo -u kaz git -C /src/thinkx-system status --short; exit 2; }
      sudo -u kaz git -C /src/thinkx-system merge --ff-only origin/$ref || { echo 'FAIL: 早送りできない(サーバー側に origin/$ref に無いコミットがある)'; sudo -u kaz git -C /src/thinkx-system log --oneline origin/$ref..HEAD; exit 3; }
      sudo -u kaz git -C /src/thinkx-system log --oneline -1
    " || {
      printf '%b\n' "${R}FAIL: deploy $env $host の更新で止まりました。サーバー側に手が入っています。${Z}"
      printf '%b\n' "${Y}消さずに止めています。その変更を commit して origin/$ref に取り込み、$ref がきれいになってから再実行してください。${Z}"
      return 1
    }
  done

  for svc in "$@"; do
    echo "== deploy $env: restart $svc =="
    case "$svc" in
      loadbalancer) ssh -o ConnectTimeout=8 "$lb"  "bash /src/thinkx-system/infra/run/restart_$svc.sh" ;;
      *)            ssh -o ConnectTimeout=8 "$web" "bash /src/thinkx-system/infra/run/restart_$svc.sh" ;;
    esac
  done

  printf '%b\n' "${G}OK: deploy $env 反映完了(origin/$ref・再起動: $*)${Z}"
}

deploy "$@"
