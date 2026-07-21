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
#   sudo -u kaz git -C /src/thinkx-system fetch origin
#   現在 branch が env の branch か検査                          # 違えば止める
#   sudo -u kaz git -C /src/thinkx-system diff --quiet           # 汚れていたら止める
#   sudo -u kaz git -C /src/thinkx-system merge --ff-only origin/<ref>
#   bash /src/thinkx-system/infra/run/restart_<service>.sh
#
# env と branch の対応:
#   prod    -> production
#   staging -> develop
#
# 【サービス引数が選ぶのは再起動するプロセスだけ】
#   撒かれるコードは常に全サービス分(git はリポジトリ全体を動かすため)。
#   `deploy.sh prod thinkx` は「thinkx だけ本番に出す」ではなく
#   「全サービスのコードを production に合わせ、thinkx のプロセスだけ再起動する」。
#
# 設計方針:
#   - git pull(ref 非指定)は使わない。撒く ref は env から一意に決める。
#   - reset --hard は使わない。サーバー上の変更を無言で消さない。
#   - サーバーに未コミット/未マージの変更があれば、消さずに止める。その先の判断は人間が行う。
#   - restart スクリプトはサーバー側 checkout から実行する。Mac の作業ツリーを入力にしない
#     (Mac から `bash -s <` で流すと、撒いたコードと再起動手順の出所が食い違う)。

set -euo pipefail

deploy() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local env="${1:-}" web lb svc br need_web=0 need_lb=0

  [ -n "$env" ] || { printf '%b\n' "${Y}注意: 環境の引数がありません。deploy.sh <staging|prod> <サービス...> のように指定してください${Z}"; return 1; }
  { [ "$env" = staging ] || [ "$env" = prod ]; } || { printf '%b\n' "${Y}注意: 第1引数は staging か prod です(指定: $env)${Z}"; return 1; }
  shift
  [ "$#" -ge 1 ] || { printf '%b\n' "${Y}注意: 再起動するサービスがありません。thinkx kazukiotsukacom transformism nginx-web-root loadbalancer から指定してください${Z}"; return 1; }

  web=supercom-web1; lb=supercom-lb1; br=production
  [ "$env" = staging ] && { web=supercom-web1-stg; lb=supercom-lb1-stg; br=develop; }

  for svc in "$@"; do
    case "$svc" in
      thinkx|kazukiotsukacom|transformism|nginx-web-root) need_web=1 ;;
      loadbalancer) need_lb=1 ;;
      *) printf '%b\n' "${R}FAIL: deploy 不明なサービス: $svc${Z}"; return 1 ;;
    esac
    [ -f "infra/run/restart_$svc.sh" ] || { printf '%b\n' "${R}FAIL: deploy infra/run/restart_$svc.sh が無い(リポジトリ直下で実行する)${Z}"; return 1; }
  done

  # サーバー側で「明示 branch へ ff-only で揃える」。
  # branch 違い / 汚れ / 独自コミットのいずれでも、何も消さずに非ゼロで返る。
  sync_remote() {
    local host="$1"
    ssh -o ConnectTimeout=8 "$host" "
      set -e
      G=/src/thinkx-system
      sudo -u kaz git -C \$G fetch --quiet origin

      cur=\$(sudo -u kaz git -C \$G rev-parse --abbrev-ref HEAD)
      if [ \"\$cur\" != $br ]; then
        echo 'WRONG-BRANCH: /src/thinkx-system は '\"\$cur\"' に居ます($br のはずです)。'
        echo '  → sudo -u kaz git -C /src/thinkx-system checkout -B $br origin/$br'
        exit 1
      fi

      if ! sudo -u kaz git -C \$G diff --quiet || ! sudo -u kaz git -C \$G diff --cached --quiet; then
        echo 'DIRTY: 未コミットの変更があります。何も消さずに中止しました。'
        sudo -u kaz git -C \$G status --short
        echo '  → 必要なら commit・push して $br に取り込み、きれいになってから再実行してください。'
        exit 1
      fi

      if ! sudo -u kaz git -C \$G merge --ff-only origin/$br; then
        echo 'NON-FF: origin/$br に無いコミットがあります。何も消さずに中止しました。'
        sudo -u kaz git -C \$G log --oneline origin/$br..HEAD
        echo '  → 必要なら push して $br に取り込み、早送り可能になってから再実行してください。'
        exit 1
      fi

      sudo -u kaz git -C \$G log --oneline -1
    "
  }

  echo "== deploy $env: Mac に全履歴を fetch(バックアップ・D-55)=="
  git fetch origin

  echo "== deploy $env: origin/$br へ ff-only で揃える =="
  if [ "$need_web" = 1 ]; then
    sync_remote "$web" || { printf '%b\n' "${R}FAIL: deploy $env web($web)の同期が中止されました。上のメッセージに従って対処してください${Z}"; return 1; }
  fi
  if [ "$need_lb" = 1 ]; then
    sync_remote "$lb" || { printf '%b\n' "${R}FAIL: deploy $env lb($lb)の同期が中止されました。上のメッセージに従って対処してください${Z}"; return 1; }
  fi

  for svc in "$@"; do
    # 配信物が生成物のサイトは restart の前に必ずビルドする。
    # ソース(src/less・src/js)を配っただけでは css/js に反映されず、古い配信物が出続ける
    # (2026-07-21 に本番で実際に起きた)。冪等なので毎回実行する。
    if [ -f "infra/run/build_$svc.sh" ]; then
      echo "== deploy $env: build $svc =="
      ssh -o ConnectTimeout=8 "$web" "bash /src/thinkx-system/infra/run/build_$svc.sh"
    fi
    echo "== deploy $env: restart $svc =="
    case "$svc" in
      loadbalancer) ssh -o ConnectTimeout=8 "$lb"  "bash /src/thinkx-system/infra/run/restart_$svc.sh" ;;
      *)            ssh -o ConnectTimeout=8 "$web" "bash /src/thinkx-system/infra/run/restart_$svc.sh" ;;
    esac
  done

  printf '%b\n' "${G}OK: deploy $env 反映完了(origin/$br・再起動: $*)${Z}"
}

deploy "$@"
