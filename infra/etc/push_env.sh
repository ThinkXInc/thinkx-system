#!/usr/bin/env bash
# etc/push_env.sh — 各サイトの .env(git 管理外)を host へ配る
#   Mac から: infra/etc/push_env.sh supercom-web thinkx kazukiotsukacom
#   真実は <site>/.env(サイト clone ルート・gitignore)。assets(動画)とは別に実行する。

push_env() {
  local host="${1:?usage: push_env.sh <host> <site>...}"; shift
  local ws site fail=0 warn=0
  local G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
  for site in "$@"; do
    [ -f "$ws/$site/.env" ] || { printf '%b\n' "${Y}WARN: $site/.env なし(スキップ)${Z}"; warn=$((warn+1)); continue; }
    if scp -q "$ws/$site/.env" "$host:/tmp/$site.env"; then
      printf '%b\n' "${G}OK: $site/.env -> $host:/tmp/$site.env${Z}"
    else
      printf '%b\n' "${R}FAIL: $site/.env の転送失敗${Z}"; fail=$((fail+1))
    fi
  done
  [ "$fail" -eq 0 ] && [ "$warn" -eq 0 ] && printf '%b\n' "${G}OK: push_env 全件完了${Z}"
  [ "$fail" -eq 0 ] && [ "$warn" -gt 0 ] && printf '%b\n' "${Y}WARN: push_env 完了(スキップ $warn 件)${Z}"
  [ "$fail" -gt 0 ] && printf '%b\n' "${R}FAIL: push_env 失敗 $fail 件${Z}"
  return "$fail"
}

push_env "$@"
