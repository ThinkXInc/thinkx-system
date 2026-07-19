#!/usr/bin/env bash
# thinkx-system/infra/etc/push_ref.sh   【分類: 変更系(素材ファイルをサーバーへ送るだけ)】
#
# 画像・資料などの素材を staging web の受け渡しディレクトリ(/home/kaz/inbox/)へ送る。
# サーバー上の Claude Code セッションには「/home/kaz/inbox/<ファイル名> を見て」と指示する。
#
#   使い方: bash infra/etc/push_ref.sh <ファイル...>
#   例:     bash infra/etc/push_ref.sh ~/Downloads/layout.png ~/Downloads/company_logo.jpg

set -euo pipefail

G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
HOST=supercom-web1-stg

[ "$#" -ge 1 ] || { printf '%b\n' "${Y}注意: 送るファイルの引数がありません。push_ref.sh <ファイル...> のように指定してください${Z}"; exit 1; }

ssh "$HOST" 'sudo -u kaz mkdir -p /home/kaz/inbox'
scp "$@" "$HOST:/tmp/"
for f in "$@"; do
  b="$(basename "$f")"
  ssh "$HOST" "sudo mv /tmp/$(printf '%q' "$b") /home/kaz/inbox/ && sudo chown kaz:kaz /home/kaz/inbox/$(printf '%q' "$b")"
done

ssh "$HOST" 'ls -la /home/kaz/inbox/ | tail -5'
printf '%b\n' "${G}OK: push_ref $# 件を $HOST:/home/kaz/inbox/ へ送付。セッションで「/home/kaz/inbox/<名前> を見て」と指示${Z}"
