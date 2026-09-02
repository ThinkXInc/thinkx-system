#!/usr/bin/env bash
# thinkx-system/infra/scripts/push_assets_podcast.sh
#
# 変更系: podcast の編集用データ(git 管理外の音源・生成物)をサーバーの data/ へ配る。
# 汎用の push_assets.sh(views/video 固定)に乗らないための例外規則スクリプト(D-52)。
#
#   使い方: bash infra/scripts/push_assets_podcast.sh <staging|prod> [ID...]
#   例:     bash infra/scripts/push_assets_podcast.sh staging 民主主義の会2-5
#
# 規則(D-52):
#  - ID を明示したときだけ、その ID を新規にサーバーへ公開する
#  - ID 省略時(deploy からの自動呼び出し)は「サーバーに既にある ID だけ」を差分同期する
#    (ローカルの未公開 ID を deploy のついでに公開しない)
#  - 送るのは 直下のファイル(元音源含む — サーバー書き出しに必要) + generated/ のみ。
#    edit/ には触れない(git が運ぶ。編集中の正はサーバー側)。contents/ backup/
#    experiments/ も送らない
#  - 一覧(パスとサイズ)を突き合わせ、一致する ID は何も送らない

# ファイル一覧を「パス サイズ」の行に揃える。macOS と Linux で sort の照合順序が
# 違うため、必ず LC_ALL=C で並べ直す(push_assets.sh と同じ教訓 2026-07-21)。
__norm_manifest() { awk '$2 != "total" { print $2, $1 }' | LC_ALL=C sort; }

# ID ディレクトリの中で「配る対象」だけを列挙する(相対パス)。
# 直下のファイルと generated/ 配下。edit/ contents/ backup/ experiments/ は含めない。
__sync_files() {
  (cd "$1" && find . -maxdepth 1 -type f ! -name ".*" ; \
   find ./generated -type f 2>/dev/null) | sed 's|^\./||'
}

push_assets_podcast() {
  local env="${1:-}"; shift 2>/dev/null
  local host ws droot ids id loc rem fail=0 sent=0 same=0
  local G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'

  case "$env" in
    staging) host=supercom-web1-stg ;;
    prod)    host=supercom-web1 ;;
    *) printf '%b\n' "${Y}環境を指定してください。${Z}"
       echo "  使い方: bash infra/scripts/push_assets_podcast.sh <staging|prod> [ID...]"
       return 1 ;;
  esac

  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
  droot="$ws/podcast/data"
  [ -d "$droot" ] || { echo "podcast/data がローカルに無い(配るものなし)"; return 0; }

  if [ "$#" -ge 1 ]; then
    ids=("$@")
  else
    # サーバーに既にある ID だけを対象にする(見つからなければ何もしない)
    local listed
    listed="$(ssh -o ConnectTimeout=8 "$host" 'ls -1 /src/podcast/data 2>/dev/null' || true)"
    [ -n "$listed" ] || { echo "podcast: サーバーに公開済み ID なし(送るものなし)"; return 0; }
    ids=()
    while IFS= read -r id; do
      [ -d "$droot/$id" ] && ids+=("$id")
    done <<< "$listed"
    [ "${#ids[@]}" -ge 1 ] || { echo "podcast: サーバーの ID はローカルに無い(送るものなし)"; return 0; }
  fi

  for id in "${ids[@]}"; do
    [ -d "$droot/$id" ] || { printf '%b\n' "${R}FAIL: ローカルに data/$id が無い${Z}"; fail=$((fail+1)); continue; }

    loc="$( (cd "$droot/$id" && __sync_files . | LC_ALL=C sort | tr '\n' '\0' | xargs -0 wc -c 2>/dev/null) | __norm_manifest )"
    rem="$( ssh -o ConnectTimeout=8 "$host" "cd '/src/podcast/data/$id' 2>/dev/null && { find . -maxdepth 1 -type f ! -name '.*'; find ./generated -type f 2>/dev/null; } | sed 's|^\./||' | LC_ALL=C sort | tr '\n' '\0' | xargs -0 wc -c 2>/dev/null" | __norm_manifest )"

    if [ -n "$loc" ] && [ "$loc" = "$rem" ]; then
      echo "podcast/$id: データは $host と一致(送るものなし)"
      same=$((same+1))
      continue
    fi

    echo "podcast/$id: データが $host と違うので配ります"
    diff <(printf '%s\n' "$rem") <(printf '%s\n' "$loc") | sed 's/^</  箱のみ  /; s/^>/  手元のみ/' | grep -v '^---$' | head -20

    if (cd "$droot/$id" && __sync_files . | COPYFILE_DISABLE=1 tar --no-xattrs -czf "/tmp/podcast-data.tgz" -T -) \
      && scp "/tmp/podcast-data.tgz" "$host:/tmp/" \
      && ssh "$host" "sudo mkdir -p '/src/podcast/data/$id' \
                      && sudo tar -xzf /tmp/podcast-data.tgz -C '/src/podcast/data/$id' \
                      && sudo chown -R kaz:serveradmins '/src/podcast/data/$id'"; then
      printf '%b\n' "${G}OK: podcast/$id を $host へ配って展開した${Z}"; sent=$((sent+1))
    else
      printf '%b\n' "${R}FAIL: podcast/$id の転送または展開に失敗${Z}"; fail=$((fail+1))
    fi
  done

  if [ "$fail" -gt 0 ]; then
    printf '%b\n' "${R}FAIL: push_assets_podcast -> $host 失敗 $fail 件(配布 $sent 件・一致 $same 件)${Z}"
  fi
  return "$fail"
}

push_assets_podcast "$@"
