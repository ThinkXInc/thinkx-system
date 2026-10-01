#!/usr/bin/env bash
# etc/push_env.sh — 各サイトの .env(git 管理外)を host へ配る 【分類: 変更系】
#   Mac から: infra/etc/push_env.sh supercom-web thinkx kazukiotsukacom
#   真実は <site>/.env(サイト clone ルート・gitignore)。assets(動画)とは別に実行する。
#   配布後、同じ実行の中で配布結果を検証して出す(所有者・権限・行数・変数名まで。
#   値は出さない — 固定。docs/approval_cases_v2.md 事例 Q の畳み込み)。

# 配布結果の検証。/tmp 側(いま配ったもの)と /src/<site>/.env(設置済み)を並べて出す。
# 行数と変数名が揃っていれば設置済みが最新。設置は setup_<site>.sh の install が行う。
verify_env() {
  local host="$1" site="$2"
  local Y=$'\033[33m' Z=$'\033[0m'
  case "$site" in (*[!a-zA-Z0-9_-]*) printf '%b\n' "${Y}WARN: verify スキップ(site 名に英数_-以外): $site${Z}"; return 0;; esac
  ssh -o ConnectTimeout=8 -o BatchMode=yes "$host" "
    if [ -f /tmp/$site.env ]; then
      echo '--- 配布先 /tmp/$site.env'
      ls -l /tmp/$site.env
      printf '行数: '; wc -l < /tmp/$site.env
    else
      echo '--- 配布先 /tmp/$site.env なし(scp 前に単体で呼んだ場合のみ正常)'
    fi
    if sudo -n true 2>/dev/null; then
      if sudo -n test -f /src/$site/.env; then
        echo '--- 設置済み /src/$site/.env'
        sudo -n ls -l /src/$site/.env
        printf '行数: '; sudo -n wc -l /src/$site/.env
        printf '変数: '; sudo -n grep -o '^[A-Z0-9_]*=' /src/$site/.env | tr '\n' ' '; echo
      else
        echo '/src/$site/.env は未設置(setup_$site.sh が /tmp から install する)'
      fi
    else
      echo '(sudo 不可のため /src 側は未確認)'
    fi" || printf '%b\n' "${Y}WARN: verify 失敗($host に ssh できない等)${Z}"
}

push_env() {
  local host="${1:-}"; shift 2>/dev/null
  local ws site fail=0 warn=0 ok=0
  local G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
  [ -n "$host" ] && [ $# -ge 1 ] || { printf '%b\n' "${R}FAIL: push_env usage: push_env.sh <host> <site>...(host か site が欠落。手順0の変数を貼ったか?)${Z}"; return 1; }
  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
  for site in "$@"; do
    [ -f "$ws/$site/.env" ] || { printf '%b\n' "${Y}WARN: $site/.env なし(スキップ)${Z}"; warn=$((warn+1)); continue; }
    if scp -q "$ws/$site/.env" "$host:/tmp/$site.env"; then
      printf '%b\n' "${G}OK: $site/.env -> $host:/tmp/$site.env${Z}"; ok=$((ok+1))
      verify_env "$host" "$site"
    else
      printf '%b\n' "${R}FAIL: $site/.env の転送失敗${Z}"; fail=$((fail+1))
    fi
  done
  [ "$fail" -eq 0 ] && [ "$warn" -eq 0 ] && printf '%b\n' "${G}OK: push_env -> $host 全件完了($ok 件)${Z}"
  [ "$fail" -eq 0 ] && [ "$warn" -gt 0 ] && printf '%b\n' "${Y}WARN: push_env -> $host 完了 $ok 件(スキップ $warn 件)${Z}"
  [ "$fail" -gt 0 ] && printf '%b\n' "${R}FAIL: push_env -> $host 失敗 $fail 件(成功 $ok 件)${Z}"
  return "$fail"
}

push_env "$@"
