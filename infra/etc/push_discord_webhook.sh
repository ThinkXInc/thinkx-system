#!/usr/bin/env bash
# etc/push_discord_webhook.sh — Discord webhook URL を host の /etc/thinkx/ へ配る
#   Mac から: infra/etc/push_discord_webhook.sh supercom-web1-stg
#
# 真実は infra/.env(.gitignore)。`KEY=値` でも URL 単体でも読める
# (ファイル内から webhook URL のパターンだけを抜き出すため、形式に依存しない)。
#
# 配布先を checkout の外(/etc/thinkx)にする理由: deploy_tick.sh が git を動かすため、
# checkout 内に置くと消える。サーバー側は URL 単体の平文ファイル。
#
# 値は端末にも履歴にも出さない(抜き出しから scp まで、一度も echo しない)。

push_discord_webhook() {
  local host="${1:?usage: push_discord_webhook.sh <ssh-host>}"
  local here infra src tmp

  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
  infra="$(cd "$here/.." && pwd)"
  src="$infra/.env"

  [ -f "$src" ] || { echo "FAIL: $src が無い。webhook URL を書き込んでから実行する" >&2; return 1; }

  tmp="$(mktemp)"
  # shellcheck disable=SC2064
  trap "rm -f '$tmp'" RETURN

  grep -oEm1 'https://discord(app)?\.com/api/webhooks/[A-Za-z0-9_/-]+' "$src" > "$tmp" || {
    echo "FAIL: $src に Discord webhook URL が見つからない" >&2
    return 1
  }
  [ -s "$tmp" ] || { echo "FAIL: 抜き出した URL が空" >&2; return 1; }

  chmod 600 "$tmp"
  scp -q "$tmp" "$host:/tmp/discord_webhook" || return 1
  ssh "$host" 'sudo install -d -m 0755 /etc/thinkx && sudo install -o kaz -g serveradmins -m 0640 /tmp/discord_webhook /etc/thinkx/discord_webhook && rm -f /tmp/discord_webhook && sudo -u kaz test -r /etc/thinkx/discord_webhook' || return 1

  echo "OK: discord_webhook -> $host:/etc/thinkx/discord_webhook (kaz:serveradmins 0640・kaz で読めることを確認済み)"
}

push_discord_webhook "$@"
