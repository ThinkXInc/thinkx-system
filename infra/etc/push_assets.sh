#!/usr/bin/env bash
# etc/push_assets.sh — 各サイトの views/video(git 管理外の実データ)を host へ配る
#   Mac から: infra/etc/push_assets.sh supercom-web thinkx kazukiotsukacom
#   真実は <site>/web-server/views/video(ローカル・gitignore)。.env とは別に実行する。

push_assets() {
  local host="${1:?usage: push_assets.sh <host> <site>...}"; shift
  local ws site
  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
  for site in "$@"; do
    [ -d "$ws/$site/web-server/views/video" ] || { echo "skip $site: views/video なし"; continue; }
    COPYFILE_DISABLE=1 tar czf "/tmp/$site-video.tgz" -C "$ws/$site/web-server/views" video || return 1
    scp "/tmp/$site-video.tgz" "$host:/tmp/" || return 1
    echo "pushed: $site-video.tgz -> $host:/tmp/"
  done
}

push_assets "$@"
