#!/usr/bin/env bash
# thinkx-system/infra/scripts/push_assets.sh
#
# 各サイトの views/video(git 管理外の実データ)を web の箱へ配る。
#
#   使い方: bash infra/scripts/push_assets.sh <host> <site>...
#   例:     bash infra/scripts/push_assets.sh supercom-web1 thinkx
#
# 動画は .gitignore の対象なので git では運ばれない。HTML の参照だけが先に本番へ行くと、
# 存在しないファイルを指して 404 になり背景動画が消える。**デプロイのスクリプトが
# サーバーを同期する前にこれを自動で呼ぶ**ので、手で叩く必要は無い。順序を人間が
# 覚えていなくても崩れないようにするためである。
#
# 先にローカルと箱のファイル一覧(名前とサイズ)を突き合わせ、一致していれば何もしない。
# 一致しないときだけ views/video 全体を送って展開する。thinkx で 347MB あり、mp4 は
# 圧縮が効かないので実サイズがそのまま流れる。差分だけ送る形(rsync)にする改善余地が
# あるが、この環境では rsync に権限が下りていない(infra/findings.md)。
#
# /tmp/<site>-video.tgz は setup_<site>.sh が展開に使う形なので、そのまま残す。
#
# views/video を持たないサイトは黙って飛ばす(transformism / kazukiotsukacom は
# 動画を持たない。これは正常な状態なので警告を出さない)。

# ファイル一覧を「パス サイズ」の行に揃える。ローカルと箱で同じ形にして突き合わせる。
#
# 最後に LC_ALL=C で並べ直すのが要点。macOS と Linux では sort の照合順序が違うため、
# 中身が同じでも並びがずれて「不一致」と判定され、毎回 347MB を送り直していた
# (2026-07-21 実測)。突き合わせに使う一覧は、必ず両側で同じ規則で並べる。
__norm_manifest() { awk '$2 != "total" { print $2, $1 }' | LC_ALL=C sort; }

push_assets() {
  local host="${1:-}"; shift 2>/dev/null
  local ws site loc rem fail=0 sent=0 same=0 skip=0
  local G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'

  if [ -z "$host" ] || [ "$#" -lt 1 ]; then
    printf '%b\n' "${Y}host とサイトを指定してください。${Z}"
    echo "  使い方: bash infra/scripts/push_assets.sh <host> <site>..."
    echo "  例:     bash infra/scripts/push_assets.sh supercom-web1 thinkx"
    return 1
  fi

  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"

  # ssh 不達は site に依らないので、site ごとに同じ FAIL を繰り返さず最初に1回だけ判定する。
  # 不達のまま進むと箱の一覧が空に見え「全部配り直し」と誤判定する(2026-10-16 実測)。
  if ! ssh -o BatchMode=yes -o ConnectTimeout=8 "$host" true 2>/dev/null; then
    printf '%b\n' "${R}FAIL: $host へ ssh 不達。アセットは確認も配布もできない${Z}"
    echo   "  典型は IP 許可切れ。直すには: bash infra/scripts/add_current_office_ip.sh"
    return 1
  fi

  for site in "$@"; do
    [ -d "$ws/$site/web-server/views/video" ] || { skip=$((skip+1)); continue; }

    loc="$( (cd "$ws/$site/web-server/views/video" && find . -type f | sort | xargs wc -c) 2>/dev/null | __norm_manifest )"

    # 箱の一覧が「取れない」のと「空」なのは別物。取れないまま突き合わせると
    # 「箱が空=全部配り直し」に見えるため、取れないときは判定せず止める。
    rem_rc=0
    rem_raw="$( ssh -o BatchMode=yes -o ConnectTimeout=8 "$host" "cd /src/$site/web-server/views/video && find . -type f | sort | xargs wc -c" 2>/dev/null )" || rem_rc=$?
    if [ "$rem_rc" -eq 255 ]; then
      printf '%b\n' "${R}FAIL: $site: ssh が途中で切れた。配らない${Z}"
      fail=$((fail+1)); continue
    elif [ "$rem_rc" -ne 0 ]; then
      printf '%b\n' "${R}FAIL: $site: 箱 /src/$site/web-server/views/video が無いか読めない。配らない${Z}"
      fail=$((fail+1)); continue
    fi
    rem="$( printf '%s\n' "$rem_raw" | __norm_manifest )"

    if [ -n "$loc" ] && [ "$loc" = "$rem" ]; then
      echo "$site: アセットは $host と一致(送るものなし)"
      same=$((same+1))
      continue
    fi

    echo "$site: アセットが $host と違うので配ります"
    diff <(printf '%s\n' "$rem") <(printf '%s\n' "$loc") | sed 's/^</  箱のみ  /; s/^>/  手元のみ/' | grep -v '^---$' | head -20

    # /src/<site> は /src/thinkx-system/<site> への symlink。nginx の alias もこちらを指す。
    if COPYFILE_DISABLE=1 tar --no-xattrs -czf "/tmp/$site-video.tgz" -C "$ws/$site/web-server/views" video \
      && scp "/tmp/$site-video.tgz" "$host:/tmp/" \
      && ssh "$host" "sudo tar -xzf /tmp/$site-video.tgz -C /src/$site/web-server/views \
                      && sudo chown -R kaz:serveradmins /src/$site/web-server/views/video"; then
      printf '%b\n' "${G}OK: $site の video を $host へ配って展開した${Z}"; sent=$((sent+1))
    else
      printf '%b\n' "${R}FAIL: $site の assets 転送または展開に失敗${Z}"; fail=$((fail+1))
    fi
  done

  if [ "$fail" -gt 0 ]; then
    printf '%b\n' "${R}FAIL: push_assets: $host で $fail 件失敗。配布 $sent・一致 $same${Z}"
  fi
  return "$fail"
}

push_assets "$@"
