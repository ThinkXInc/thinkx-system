#!/usr/bin/env bash
# thinkx-system/infra/run/sync_from_origin.sh
#
# このサーバーのソースを origin の指定 branch の先端に合わせる。
#
# やることは3つだけ: (1) 早送りできるか調べる (2) 早送りする
# (3) 変更されたパスから影響を受けるサービスを割り出し、build_and_restart.sh に渡す。
# コンパイルと再起動と応答確認は build_and_restart.sh だけが持つ。ここには持たない
# (同じ処理を2箇所に置いたせいで、ビルド漏れの修正を両方に当てる羽目になった。2026-07-21)。
#
# 「デプロイ」ではなくその一部分。デプロイの入口は
# infra/scripts/deploy_production_from_staging.sh 1本だけである。
#
# 呼ばれ方は2つ。どちらも同じこの実装を通る(経路を増やさないため):
#   - systemd timer(deploy-timer@<env>.timer)から60秒ごと
#   - Mac から infra/scripts/deploy_production_from_staging.sh 経由で ssh
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
#
# 通知は Discord に出る。読み手はサーバーの中を見ていないので、内部のスクリプト名や
# 変数名を出さない。「何をしたか」「なぜそう判断したか」「次に何を打てばいいか」を書く。

set -euo pipefail

REPO=/src/thinkx-system
WEBHOOK_FILE=/etc/thinkx/discord_webhook
SELF_INSTALLED=/usr/local/bin/sync_from_origin.sh
BLOCKED_STATE=/var/lib/thinkx/blocked_notified

# git は必ず kaz として実行する(root が触ると所有者が壊れる)
g() { sudo -H -u kaz git -C "$REPO" "$@"; }

# 通知に出す箱の呼び名。hostname は内部名なので、読んで分かる名前に直す。
# ssh の宛先としてはそのまま hostname が使えるので、次に打つコマンドには hostname を出す。
box_label() {
  case "$1" in
    supercom-web1-stg) echo "staging web" ;;
    supercom-lb1-stg)  echo "staging LB"  ;;
    supercom-web1)     echo "本番 web"    ;;
    supercom-lb1)      echo "本番 LB"     ;;
    *)                 echo "$1"          ;;
  esac
}

# 止まっているときの通知は1回だけにする。
# 反映を見送っている間は毎回(60秒ごと)同じ状況が続くため、素直に通知すると同じ文面が
# 延々と流れる。「何が原因で止まっているか」が変わったときだけ知らせる。
# 状況が変われば(人が commit した・別のコミットが来た)また通知される。
notify_once() {
  local key="$1" text="$2"
  mkdir -p "$(dirname "$BLOCKED_STATE")"
  [ "$(cat "$BLOCKED_STATE" 2>/dev/null)" = "$key" ] && return 0
  printf '%s' "$key" > "$BLOCKED_STATE"
  notify "$text"
}

# 止まっていた状態から抜けたら、次に止まったときは必ず通知されるようにする
clear_blocked() { rm -f "$BLOCKED_STATE"; }

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
    thinkx/*)          echo thinkx ;;
    transformism/*)    echo transformism ;;
    kazukiotsukacom/*) echo kazukiotsukacom ;;
    nginx-web-root/*)  echo nginx-web-root ;;
    loadbalancer/*)    echo loadbalancer ;;
  esac
}

sync_from_origin() {
  local env="${1:?usage: sync_from_origin.sh <staging|prod>}"
  local branch host box prev new changed subject n_changed dirs ahead svc
  local -a targets=()

  host="$(hostname)"
  box="$(box_label "$host")"

  case "$env" in
    staging) branch=develop ;;
    prod)    branch=production ;;
    *) echo "FAIL: 第1引数は staging か prod(指定: $env)" >&2; return 1 ;;
  esac

  # 反映の途中で落ちても黙って死なない(通知してから終わる)
  trap 'notify ":rotating_light: **'"$box"'** 自動反映の処理そのものが落ちました。
サイトが無事かどうかは分かりません。確認してください:
\`\`\`
ssh '"$host"' '"'"'journalctl -u deploy-timer@'"$env"' -n 50 --no-pager'"'"'
\`\`\`"' ERR

  g fetch --quiet origin

  prev="$(g rev-parse HEAD)"
  new="$(g rev-parse "origin/$branch")"

  [ "$prev" = "$new" ] && return 0

  # サーバー側に何か手が入っていたら、消さずに止めて人間に渡す(staging / prod 共通)
  if [ -n "$(g status --porcelain)" ]; then
    notify_once "dirty:$new:$(g status --porcelain | cksum)" ":warning: **$box** このサーバーの上で編集されたファイルがあるので、反映を止めました。
**編集は消していません。そのままです。**
\`\`\`
$(g status --short | head -20)
\`\`\`
続けるには、このサーバーの上で commit して push してください:
\`\`\`
ssh $host
cd /src/thinkx-system && git add -A && git commit -m '内容' && git push
\`\`\`"
    return 0
  fi

  ahead="$(g rev-list --count "origin/$branch..HEAD")"
  if [ "$ahead" != 0 ]; then
    notify_once "ahead:$new:$prev" ":warning: **$box** このサーバーの上で作られたまま、まだ送られていないコミットが $ahead 件あります。反映を止めました。
**コミットは消していません。そのままです。**
\`\`\`
$(g log --oneline "origin/$branch..HEAD" | head -20)
\`\`\`
続けるには、このサーバーの上で push してください:
\`\`\`
ssh $host 'cd /src/thinkx-system && git push'
\`\`\`"
    return 0
  fi

  changed="$(g diff --name-only "$prev" "$new")"
  subject="$(g log --format=%s -1 "$new")"
  n_changed="$(printf '%s\n' "$changed" | grep -c . || true)"
  dirs="$(printf '%s\n' "$changed" | cut -d/ -f1 | sort -u | tr '\n' ' ')"

  while read -r path; do
    [ -n "$path" ] || continue
    svc="$(services_for "$path")"
    [ -n "$svc" ] || continue
    case " ${targets[*]-} " in *" $svc "*) ;; *) targets+=("$svc") ;; esac
  done <<< "$changed"

  g merge --ff-only --quiet "$new"
  clear_blocked

  # 自分自身の入れ替え。install は同じファイルを truncate して書き直すため、実行中の
  # このスクリプトを直接上書きすると bash が読んでいる途中で中身が入れ替わる。
  # 別名で置いてから mv(rename)する。rename なら実行中の側は古い実体を読み続ける。
  install -m 0755 "$REPO/infra/run/sync_from_origin.sh" "$SELF_INSTALLED.new"
  mv -f "$SELF_INSTALLED.new" "$SELF_INSTALLED"

  # systemd のユニットは repo への symlink で置いてあるので、中身が変わっても
  # daemon-reload するまで systemd は気づかない。
  if printf '%s\n' "$changed" | grep -q '^infra/setup/.*\.\(service\|timer\)$'; then
    systemctl daemon-reload
  fi

  if [ "${#targets[@]}" -eq 0 ]; then
    notify ":page_facing_up: **$box** ソースを \`$branch\` の先端に合わせました。**サービスの再起動はしていません。**
\`${new:0:7}\` $subject
変更 $n_changed ファイル($dirs)
サイトを構成するディレクトリ(thinkx / transformism / kazukiotsukacom / nginx-web-root / loadbalancer)に変更が無いため、再起動の必要がありません。"
    return 0
  fi

  # ビルド・再起動・検証は build_and_restart.sh 1本が持つ。ここでは呼ぶだけ。
  # 対象を全部並べて渡し、向こうが直列で処理する。
  if ! bash "$REPO/infra/run/build_and_restart.sh" "${targets[@]}"; then
    # 戻しは巻き戻しなので早送りにならない。直前に clean を確認して早送りした
    # 直後なので、消えるのは今入れた分だけ。
    g reset --hard --quiet "$prev"
    bash "$REPO/infra/run/build_and_restart.sh" "${targets[@]}" || true
    notify ":rotating_light: **$box** 反映したらサイトが応答しなくなったので、**元に戻しました。**
入れようとしたもの: \`${new:0:7}\` $subject
戻した先        : \`${prev:0:7}\`(直前まで動いていたもの)
サイトは戻した状態で動いています。原因を見るには:
\`\`\`
ssh $host 'journalctl -u deploy-timer@$env -n 50 --no-pager'
\`\`\`"
    trap - ERR
    return 1
  fi

  notify ":white_check_mark: **$box** ソースを \`$branch\` の先端に合わせ、**${targets[*]} を再起動しました。**
\`${new:0:7}\` $subject
変更 $n_changed ファイル($dirs)
再起動したサービスはどれも応答 200 を返しています。"

  trap - ERR
}

sync_from_origin "$@"
