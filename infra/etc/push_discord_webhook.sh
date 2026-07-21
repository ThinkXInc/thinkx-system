#!/usr/bin/env bash
# etc/push_discord_webhook.sh — Discord webhook URL を host の /etc/thinkx/ へ配る
#   Mac から: infra/etc/push_discord_webhook.sh supercom-web1-stg
#
# 真実は infra/env/discord_webhook(.gitignore)。deploy_tick.sh がここを読んで通知する。
# checkout の外(/etc/thinkx)に置く理由: deploy_tick.sh は git reset --hard するため、
# checkout 内に置くと消える。

push_discord_webhook() {
  local host="${1:?usage: push_discord_webhook.sh <ssh-host>}"
  local here infra src
  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
  infra="$(cd "$here/.." && pwd)"
  src="$infra/env/discord_webhook"

  [ -f "$src" ] || { echo "FAIL: $src が無い。先に webhook URL を書き込む" >&2; return 1; }

  scp -q "$src" "$host:/tmp/discord_webhook" || return 1
  ssh "$host" 'sudo install -d -m 0755 /etc/thinkx && sudo install -o kaz -g serveradmins -m 0640 /tmp/discord_webhook /etc/thinkx/discord_webhook && rm -f /tmp/discord_webhook && sudo -u kaz test -r /etc/thinkx/discord_webhook' || return 1

  echo "OK: discord_webhook -> $host:/etc/thinkx/discord_webhook (kaz:serveradmins 0640・kaz で読めることを確認済み)"
}

push_discord_webhook "$@"
