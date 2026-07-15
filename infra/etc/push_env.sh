#!/usr/bin/env bash
# etc/push_env.sh — 各サイトの .env(git 管理外)を host へ配る
#   Mac から: infra/etc/push_env.sh supercom-web thinkx kazukiotsukacom
#   真実は <site>/.env(サイト clone ルート・gitignore)。assets(動画)とは別に実行する。

push_env() {
  local host="${1:?usage: push_env.sh <host> <site>...}"; shift
  local ws site
  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
  for site in "$@"; do
    [ -f "$ws/$site/.env" ] || { echo "skip $site: .env なし"; continue; }
    scp "$ws/$site/.env" "$host:/tmp/$site.env" || return 1
    echo "pushed: $site/.env -> $host:/tmp/$site.env"
  done
}

push_env "$@"
