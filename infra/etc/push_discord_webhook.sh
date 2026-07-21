#!/usr/bin/env bash
# etc/push_discord_webhook.sh — Discord webhook URL を host の /etc/thinkx/ へ配る
#   Mac から: infra/etc/push_discord_webhook.sh supercom-web1-stg
#
# 真実は infra/.env(.gitignore)の DISCORD_WEBHOOK_DEPLOY_BOT。
# 名指しで取る(将来 .env に別ボットの webhook が増えても取り違えないため)。
#
# 配布先を checkout の外(/etc/thinkx)にする理由: deploy_tick.sh が git を動かすため、
# checkout 内に置くと消える。サーバー側は URL 単体の平文ファイル。
#
# 値は端末にも履歴にも出さない(抜き出しから scp まで、一度も echo しない)。

push_discord_webhook() {
  local host="${1:?usage: push_discord_webhook.sh <ssh-host>}"
  local key=DISCORD_WEBHOOK_DEPLOY_BOT
  local here infra src tmp

  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
  infra="$(cd "$here/.." && pwd)"
  src="$infra/.env"

  [ -f "$src" ] || { echo "FAIL: $src が無い。webhook URL を書き込んでから実行する" >&2; return 1; }

  tmp="$(mktemp)"
  # shellcheck disable=SC2064
  trap "rm -f '$tmp'" RETURN

  # $key の値だけを取り出す。前後の空白・引用符を落とし、URL の形かどうかまで検査する。
  sed -n "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*[\"']\{0,1\}\([^\"']*\)[\"']\{0,1\}[[:space:]]*$/\1/p" "$src" \
    | head -1 > "$tmp"

  [ -s "$tmp" ] || {
    echo "FAIL: $src に $key の行が無い" >&2
    echo "      形式: $key=https://discord.com/api/webhooks/..." >&2
    return 1
  }

  grep -qE '^https://discord(app)?\.com/api/webhooks/[A-Za-z0-9_/-]+$' "$tmp" || {
    echo "FAIL: $key の値が Discord webhook URL の形をしていない(値は表示しない)" >&2
    return 1
  }

  chmod 600 "$tmp"
  scp -q "$tmp" "$host:/tmp/discord_webhook" || return 1
  ssh "$host" 'sudo install -d -m 0755 /etc/thinkx && sudo install -o kaz -g serveradmins -m 0640 /tmp/discord_webhook /etc/thinkx/discord_webhook && rm -f /tmp/discord_webhook && sudo -u kaz test -r /etc/thinkx/discord_webhook' || return 1

  echo "OK: discord_webhook -> $host:/etc/thinkx/discord_webhook (kaz:serveradmins 0640・kaz で読めることを確認済み)"
}

push_discord_webhook "$@"
