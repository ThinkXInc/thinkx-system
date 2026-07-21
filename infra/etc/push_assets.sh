#!/usr/bin/env bash
# etc/push_assets.sh — 各サイトの views/video(git 管理外の実データ)を host へ配って展開する
#   Mac から: infra/etc/push_assets.sh supercom-web1 thinkx kazukiotsukacom
#   真実は <site>/web-server/views/video(ローカル・gitignore)。.env とは別に実行する。
#
# 動画は .gitignore の対象なので git では運ばれない。デプロイでコミットが本番へ行っても
# 動画本体は行かないため、HTML だけが新しいファイル名を指して 404 になる。**動画を
# 差し替えたときは、デプロイの前にこれを実行する。**
#
# 送るだけでなく展開まで行う。以前は /tmp に置くだけで、展開は setup_<site>.sh の役目
# だった(D-40)。それだと既に動いている箱では「送ったのに反映されない」で終わる
# (2026-07-21 に実際に「staging に置いた動画を本番へ運ぶ経路が無い」として露出した)。
# /tmp の tgz は setup_<site>.sh が期待する形なので、そのまま残す。
#
# 転送量は views/video 全体。mp4 は圧縮が効かないので、1サイトで数百MBになる。
# 差分だけ送る形(rsync)にする改善余地がある(infra/findings.md)。

push_assets() {
  local host="${1:-}"; shift 2>/dev/null
  local ws site fail=0 warn=0 ok=0
  local G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
  [ -n "$host" ] && [ $# -ge 1 ] || { printf '%b\n' "${R}FAIL: push_assets usage: push_assets.sh <host> <site>...(host か site が欠落。手順0の変数を貼ったか?)${Z}"; return 1; }
  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
  for site in "$@"; do
    [ -d "$ws/$site/web-server/views/video" ] || { printf '%b\n' "${Y}WARN: $site views/video なし(スキップ)${Z}"; warn=$((warn+1)); continue; }
    # /src/<site> は /src/thinkx-system/<site> への symlink。nginx の alias もこちらを指す。
    if COPYFILE_DISABLE=1 tar --no-xattrs -czf "/tmp/$site-video.tgz" -C "$ws/$site/web-server/views" video \
      && scp "/tmp/$site-video.tgz" "$host:/tmp/" \
      && ssh "$host" "sudo tar -xzf /tmp/$site-video.tgz -C /src/$site/web-server/views \
                      && sudo chown -R kaz:serveradmins /src/$site/web-server/views/video"; then
      printf '%b\n' "${G}OK: $site の video を $host へ配って展開した${Z}"; ok=$((ok+1))
    else
      printf '%b\n' "${R}FAIL: $site の assets 転送または展開に失敗${Z}"; fail=$((fail+1))
    fi
  done
  [ "$fail" -eq 0 ] && [ "$warn" -eq 0 ] && printf '%b\n' "${G}OK: push_assets -> $host 全件完了($ok 件)${Z}"
  [ "$fail" -eq 0 ] && [ "$warn" -gt 0 ] && printf '%b\n' "${Y}WARN: push_assets -> $host 完了 $ok 件(スキップ $warn 件)${Z}"
  [ "$fail" -gt 0 ] && printf '%b\n' "${R}FAIL: push_assets -> $host 失敗 $fail 件(成功 $ok 件)${Z}"
  return "$fail"
}

push_assets "$@"
