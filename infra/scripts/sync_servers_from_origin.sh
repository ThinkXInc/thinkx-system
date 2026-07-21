#!/usr/bin/env bash
# thinkx-system/infra/scripts/sync_servers_from_origin.sh
#   【分類: 変更系(サーバーを origin に合わせる)】
#
# 指定 env の web と lb を、origin の対応 branch に合わせる。
# 「デプロイ」ではなくその一部分。**デプロイの入口は
# infra/scripts/deploy_production_from_staging.sh 1本だけ**である。
#
#   使い方: bash infra/scripts/sync_servers_from_origin.sh <staging|prod>
#
# env と branch の対応:
#   staging -> origin/develop
#   prod    -> origin/production
#
# 実体はサーバー側の infra/run/sync_from_origin.sh 1つだけで、このスクリプトは
# それを ssh で叩くだけの引き金である。systemd timer が呼ぶのも同じ実装なので、
# 手動と自動で挙動が食い違わない(食い違って本番で css が古いまま出た実例あり・2026-07-21)。
#
# サービスの選択は無い。何を再起動するかは変更パスからサーバー側が判定する
# (全サービスを足並み揃えて出す方式のため、選ぶ必要が無い)。
#
# 何も消さずに止まる場合がある(DIRTY / NON-FF / WRONG-BRANCH)。その先の判断は人間が行う。

set -euo pipefail

sync_servers_from_origin() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local env="${1:-}" web lb host fail=0

  [ -n "$env" ] || { printf '%b\n' "${Y}注意: 環境の引数がありません。sync_servers_from_origin.sh <staging|prod>${Z}"; return 1; }
  { [ "$env" = staging ] || [ "$env" = prod ]; } || { printf '%b\n' "${Y}注意: 第1引数は staging か prod です(指定: $env)${Z}"; return 1; }

  web=supercom-web1; lb=supercom-lb1
  [ "$env" = staging ] && { web=supercom-web1-stg; lb=supercom-lb1-stg; }

  echo "== Mac に全履歴を fetch(バックアップ・D-55)=="
  git fetch origin

  for host in "$web" "$lb"; do
    echo
    echo "== $host を origin に合わせる =="
    # 実行中に git がスクリプト自身を書き換えると bash が壊れるため、必ず /usr/local/bin の
    # 複製を動かす。未設置なら checkout から入れる(以後は sync_from_origin 自身が更新する)。
    ssh -o ConnectTimeout=8 "$host" '
      test -x /usr/local/bin/sync_from_origin.sh ||
        sudo install -m 0755 /src/thinkx-system/infra/run/sync_from_origin.sh /usr/local/bin/
      sudo /usr/local/bin/sync_from_origin.sh '"$env" || {
        printf '%b\n' "${R}FAIL: $host の同期が止まりました。上のメッセージに従って対処してください${Z}"
        fail=$((fail+1))
      }
  done

  [ "$fail" -eq 0 ] || return 1
  printf '%b\n' "${G}OK: $env の web と lb を origin に合わせました${Z}"
}

sync_servers_from_origin "$@"
