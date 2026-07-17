#!/usr/bin/env bash
# etc/push_assets.sh — 各サイトの views/video(git 管理外の実データ)を host へ配る
#   Mac から: infra/etc/push_assets.sh supercom-web thinkx kazukiotsukacom
#   真実は <site>/web-server/views/video(ローカル・gitignore)。.env とは別に実行する。

push_assets() {
  local host="${1:-}"; shift 2>/dev/null
  local ws site fail=0 warn=0 ok=0
  local G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
  [ -n "$host" ] && [ $# -ge 1 ] || { printf '%b\n' "${R}FAIL: push_assets usage: push_assets.sh <host> <site>...(host か site が欠落。手順0の変数を貼ったか?)${Z}"; return 1; }
  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
  for site in "$@"; do
    [ -d "$ws/$site/web-server/views/video" ] || { printf '%b\n' "${Y}WARN: $site views/video なし(スキップ)${Z}"; warn=$((warn+1)); continue; }
    if COPYFILE_DISABLE=1 tar --no-xattrs -czf "/tmp/$site-video.tgz" -C "$ws/$site/web-server/views" video && scp "/tmp/$site-video.tgz" "$host:/tmp/"; then
      printf '%b\n' "${G}OK: $site-video.tgz -> $host:/tmp/${Z}"; ok=$((ok+1))
    else
      printf '%b\n' "${R}FAIL: $site の assets 転送失敗${Z}"; fail=$((fail+1))
    fi
  done
  [ "$fail" -eq 0 ] && [ "$warn" -eq 0 ] && printf '%b\n' "${G}OK: push_assets -> $host 全件完了($ok 件)${Z}"
  [ "$fail" -eq 0 ] && [ "$warn" -gt 0 ] && printf '%b\n' "${Y}WARN: push_assets -> $host 完了 $ok 件(スキップ $warn 件)${Z}"
  [ "$fail" -gt 0 ] && printf '%b\n' "${R}FAIL: push_assets -> $host 失敗 $fail 件(成功 $ok 件)${Z}"
  return "$fail"
}

push_assets "$@"
