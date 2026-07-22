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

  for site in "$@"; do
    [ -d "$ws/$site/web-server/views/video" ] || { skip=$((skip+1)); continue; }

    loc="$( (cd "$ws/$site/web-server/views/video" && find . -type f | sort | xargs wc -c) 2>/dev/null | __norm_manifest )"
    rem="$( ssh -o ConnectTimeout=8 "$host" "cd /src/$site/web-server/views/video && find . -type f | sort | xargs wc -c" 2>/dev/null | __norm_manifest )"

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
    printf '%b\n' "${R}FAIL: push_assets -> $host 失敗 $fail 件(配布 $sent 件・一致 $same 件)${Z}"
  fi
  return "$fail"
}

push_assets "$@"
