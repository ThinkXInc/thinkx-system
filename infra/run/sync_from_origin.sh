#!/usr/bin/env bash
# thinkx-system/infra/run/sync_from_origin.sh   【分類: 変更系(この箱を origin に合わせる)】
#
# このサーバーを origin の指定 branch に合わせ、必要なものを作り直して再起動する。
# 「デプロイ」ではなくその一部分。デプロイの入口は
# infra/scripts/deploy_production_from_staging.sh 1本だけである。
#
# 呼ばれ方は2つ。どちらも同じこの実装を通る(経路を増やさないため):
#   - systemd timer(deploy-timer@<env>.timer)から60秒ごと
#   - Mac から infra/scripts/sync_servers_from_origin.sh 経由で ssh
# 直接実行前提(source しない)。実体は setup_deploy_timer.sh が /usr/local/bin へ複製する
# (実行中に git がスクリプト自身を書き換えると bash が壊れるため、必ず複製側を動かす)。
#
# root で動く。git だけ `sudo -u kaz` で実行する(リポジトリの所有者が kaz のため)。
# kaz は sudoers に入っていないので、User=kaz では systemctl も install も動かない(実測)。
#
#   使い方: sync_from_origin.sh <staging|prod>
#
#   staging -> origin/develop を追う
#   prod    -> origin/production を追う
#
# どちらも「きれいなときだけ早送り(merge --ff-only)、何か手が入っていたら消さずに止めて通知」。
# reset --hard は使わない。サーバー上の直接変更を無言で消すのを避けるため(オーナー裁定 2026-07-21)。
# 止まった先の判断は人間が行う(その変更を commit して origin に取り込み、きれいにしてから再開)。
#
# 反映後に検証し、落ちていたら直前の ref へ戻して通知する。

set -euo pipefail

REPO=/src/thinkx-system
WEBHOOK_FILE=/etc/thinkx/discord_webhook
SELF_INSTALLED=/usr/local/bin/sync_from_origin.sh

# git は必ず kaz として実行する(root が触ると所有者が壊れる)
g() { sudo -H -u kaz git -C "$REPO" "$@"; }

notify() {
  local text="$1" url
  [ -r "$WEBHOOK_FILE" ] || return 0
  url="$(cat "$WEBHOOK_FILE")"
  [ -n "$url" ] || return 0
  python3 -c 'import json,sys;print(json.dumps({"content":sys.argv[1]}))' "$text" \
    | curl -s -m 10 -X POST -H 'Content-Type: application/json' -d @- "$url" >/dev/null 2>&1 || true
}

services_for() {
  case "$1" in
    thinkx/*)          echo uwsgi_thinkx ;;
    transformism/*)    echo uwsgi_transformism ;;
    kazukiotsukacom/*) echo uwsgi_kazukiotsukacom ;;
    nginx-web-root/*)  echo nginx ;;
    loadbalancer/*)    echo nginx ;;
  esac
}

verify_service() {
  local code
  case "$1" in
    uwsgi_thinkx)          code="$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: thinkxinc.com'    http://localhost:8005/ || true)" ;;
    uwsgi_transformism)    code="$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: transformism.art' http://localhost:8006/ || true)" ;;
    uwsgi_kazukiotsukacom) code="$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: kazukiotsuka.com' http://localhost:8007/ || true)" ;;
    nginx)                 code="$(systemctl is-active nginx >/dev/null 2>&1 && echo 200 || echo 000)" ;;
    *)                     code=200 ;;
  esac
  [ "$code" = 200 ]
}

restart_all() {
  local s
  for s in "$@"; do
    systemctl restart "$s" 2>/dev/null || systemctl restart "$s.service" || true
  done
}

sync_from_origin() {
  local env="${1:?usage: sync_from_origin.sh <staging|prod>}"
  local branch host prev new changed ahead svc
  local -a targets=()

  host="$(hostname)"

  case "$env" in
    staging) branch=develop ;;
    prod)    branch=production ;;
    *) echo "FAIL: 第1引数は staging か prod(指定: $env)" >&2; return 1 ;;
  esac

  # 反映の途中で落ちても黙って死なない(通知してから終わる)
  trap 'notify ":rotating_light: **'"$host"'** sync_from_origin が異常終了しました。journalctl -u deploy-timer@'"$env"' を確認してください。"' ERR

  g fetch --quiet origin

  prev="$(g rev-parse HEAD)"
  new="$(g rev-parse "origin/$branch")"

  [ "$prev" = "$new" ] && return 0

  # サーバー側に何か手が入っていたら、消さずに止めて人間に渡す(staging / prod 共通)
  if [ -n "$(g status --porcelain)" ]; then
    notify ":warning: **$host** 未コミットの変更があるため反映を見送りました。消していません。commit + push してください。
\`\`\`
$(g status --short | head -20)
\`\`\`"
    return 0
  fi

  ahead="$(g rev-list --count "origin/$branch..HEAD")"
  if [ "$ahead" != 0 ]; then
    notify ":warning: **$host** \`origin/$branch\` に無いコミットが $ahead 件あるため早送りできません。消していません。push して \`$branch\` に取り込んでください。
\`\`\`
$(g log --oneline "origin/$branch..HEAD" | head -20)
\`\`\`"
    return 0
  fi

  changed="$(g diff --name-only "$prev" "$new")"

  while read -r path; do
    [ -n "$path" ] || continue
    svc="$(services_for "$path")"
    [ -n "$svc" ] || continue
    case " ${targets[*]-} " in *" $svc "*) ;; *) targets+=("$svc") ;; esac
  done <<< "$changed"

  g merge --ff-only --quiet "$new"

  install -m 0755 "$REPO/infra/run/sync_from_origin.sh" "$SELF_INSTALLED"

  if [ "${#targets[@]}" -eq 0 ]; then
    notify ":page_facing_up: **$host** \`$branch\` を \`${new:0:7}\` へ更新(再起動が要るサービスの変更なし)"
    return 0
  fi

  # 配信物が生成物のサイトは restart の前にビルドする(ソースを配っただけでは css/js に出ないため)
  for svc in "${targets[@]}"; do
    case "$svc" in
      uwsgi_thinkx) [ -f "$REPO/infra/run/build_thinkx.sh" ] && bash "$REPO/infra/run/build_thinkx.sh" ;;
    esac
  done

  restart_all "${targets[@]}"
  sleep 3

  for svc in "${targets[@]}"; do
    if ! verify_service "$svc"; then
      # ここだけ reset --hard を使う。戻しは巻き戻しなので早送りにならない。
      # 直前に clean を確認して早送りした直後なので、消えるのは今入れた分だけ。
      g reset --hard --quiet "$prev"
      restart_all "${targets[@]}"
      notify ":rotating_light: **$host** \`${new:0:7}\` の反映で **$svc** が応答しません。\`${prev:0:7}\` へ戻しました。"
      trap - ERR
      return 1
    fi
  done

  notify ":white_check_mark: **$host** \`$branch\` を \`${new:0:7}\` へ反映しました。
再起動: ${targets[*]}
$(g log --oneline -1 "$new")"

  trap - ERR
}

sync_from_origin "$@"
