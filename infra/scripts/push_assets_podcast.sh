#!/usr/bin/env bash
# thinkx-system/infra/scripts/push_assets_podcast.sh
#
# 変更系: podcast の data/(git 管理外の音源・生成物)をサーバーへ差分同期する。
# 汎用の push_assets.sh(views/video 固定)に乗らないための例外規則スクリプト。
#
#   使い方: bash infra/scripts/push_assets_podcast.sh <staging|prod> [ID...]
#   例:     bash infra/scripts/push_assets_podcast.sh staging
#
# 規則(D-52 改定・オーナー指示 2026-09-17「データはローカルを完全にコピーする。
# 同期は git の commit と連動」):
#  - 引数なし(deploy からの自動呼び出し) = **ローカル data/ 全体を完全同期**。
#    デプロイ=commit されたものを出す操作なので、これが git commit との連動点になる
#  - ID を指定したときはその ID だけ先行して送れる(絞り込み)
#  - `_` 始まりのフォルダと experiments/ は同期しない(試行・退役の置き場。
#    一覧UIが `_` 始まりを隠すのと同じ規則。オーナー指示 2026-09-17)
#  - **edit/ には触れない**(git が正。サーバー側の新しい編集をファイルコピーで
#    上書きしない)。それ以外は 直下・generated・contents・backup すべて送る
#  - **削除はしない**(サーバー上で生まれる書き出し・ジャーナルを消さないため)。
#    「完全コピー」= ローカルにある全ファイルがサーバーにも同内容で存在すること
#  - 一覧(パスとサイズ)を突き合わせ、一致する ID は何も送らない

# ファイル一覧を「パス サイズ」の行に揃える。macOS と Linux で sort の照合順序が
# 違うため、必ず LC_ALL=C で並べ直す(push_assets.sh と同じ教訓 2026-07-21)。
__norm_manifest() { awk '$2 != "total" { print $2, $1 }' | LC_ALL=C sort; }

# ID ディレクトリの中で「配る対象」= edit/ と隠しファイル以外のすべて(相対パス)。
__sync_files() {
  (cd "$1" && find . -type f ! -name ".*" ! -path "./edit/*" ! -path "./experiments/*") | sed 's|^\./||'
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

  # 送信前に源流のファイル名を NFC に正準化する(git が運ぶ形と揃える。NFD が混じると
  # Linux サーバー上で同名フォルダが NFC/NFD に分裂し、編集データと音源が別れる —
  # 2026-09-17 実測)。補正した名前はその場に表示される。別実体の衝突は人間の判断が
  # 要るので止まる
  python3 "$ws/podcast/scripts/normalize_data_names.py" --fix "$droot" ||
    { printf '%b\n' "${R}FAIL: ファイル名の NFC 正規化で衝突。上の表示を確認して統合してから再実行${Z}"; return 1; }

  if [ "$#" -ge 1 ]; then
    ids=("$@")
  else
    # 完全同期: ローカルの全 ID ディレクトリが対象
    ids=()
    while IFS= read -r id; do
      ids+=("$id")
    done < <(cd "$droot" && find . -maxdepth 1 -mindepth 1 -type d ! -name ".*" ! -name "_*" | sed 's|^\./||' | LC_ALL=C sort)
    [ "${#ids[@]}" -ge 1 ] || { echo "podcast: ローカルに ID なし(送るものなし)"; return 0; }

    # data 直下の単独ファイル(sources.json 等)も揃える
    loc="$( (cd "$droot" && find . -maxdepth 1 -type f ! -name ".*" | sed 's|^\./||' | LC_ALL=C sort | tr '\n' '\0' | xargs -0 wc -c 2>/dev/null) | __norm_manifest )"
    rem="$( ssh -o ConnectTimeout=8 "$host" "cd /src/podcast/data 2>/dev/null && find . -maxdepth 1 -type f ! -name '.*' | sed 's|^\./||' | LC_ALL=C sort | tr '\n' '\0' | xargs -0 wc -c 2>/dev/null" | __norm_manifest )"
    if [ -n "$loc" ] && [ "$loc" != "$rem" ]; then
      if (cd "$droot" && find . -maxdepth 1 -type f ! -name ".*" | sed 's|^\./||' | COPYFILE_DISABLE=1 tar --no-xattrs -czf "/tmp/podcast-data.tgz" -T -) \
        && scp -q "/tmp/podcast-data.tgz" "$host:/tmp/" \
        && ssh "$host" "sudo mkdir -p /src/podcast/data \
                        && sudo tar -xzf /tmp/podcast-data.tgz -C /src/podcast/data \
                        && sudo chown kaz:serveradmins /src/podcast/data/*.json 2>/dev/null; true"; then
        echo "podcast: data 直下のファイルを配った"
      else
        printf '%b\n' "${R}FAIL: data 直下ファイルの転送に失敗${Z}"; fail=$((fail+1))
      fi
    fi
  fi

  for id in "${ids[@]}"; do
    [ -d "$droot/$id" ] || { printf '%b\n' "${R}FAIL: ローカルに data/$id が無い${Z}"; fail=$((fail+1)); continue; }

    loc="$( (cd "$droot/$id" && __sync_files . | LC_ALL=C sort | tr '\n' '\0' | xargs -0 wc -c 2>/dev/null) | __norm_manifest )"
    rem="$( ssh -o ConnectTimeout=8 "$host" "cd '/src/podcast/data/$id' 2>/dev/null && find . -type f ! -name '.*' ! -path './edit/*' ! -path './experiments/*' | sed 's|^\./||' | LC_ALL=C sort | tr '\n' '\0' | xargs -0 wc -c 2>/dev/null" | __norm_manifest )"

    if [ -n "$loc" ] && [ "$loc" = "$rem" ]; then
      same=$((same+1))
      continue
    fi

    echo "podcast/$id: データが $host と違うので配ります"
    diff <(printf '%s\n' "$rem") <(printf '%s\n' "$loc") | sed 's/^</  箱のみ  /; s/^>/  手元のみ/' | grep -v '^---$' | head -10

    if (cd "$droot/$id" && __sync_files . | COPYFILE_DISABLE=1 tar --no-xattrs -czf "/tmp/podcast-data.tgz" -T -) \
      && scp -q "/tmp/podcast-data.tgz" "$host:/tmp/" \
      && ssh "$host" "sudo mkdir -p '/src/podcast/data/$id' \
                      && sudo tar -xzf /tmp/podcast-data.tgz -C '/src/podcast/data/$id' \
                      && sudo chown -R kaz:serveradmins '/src/podcast/data/$id'"; then
      printf '%b\n' "${G}OK: podcast/$id を $host へ配って展開した${Z}"; sent=$((sent+1))
    else
      printf '%b\n' "${R}FAIL: podcast/$id の転送または展開に失敗${Z}"; fail=$((fail+1))
    fi
  done

  echo "podcast: 配布 $sent 件・一致 $same 件・失敗 $fail 件"
  if [ "$fail" -gt 0 ]; then
    printf '%b\n' "${R}FAIL: push_assets_podcast -> $host${Z}"
  fi
  return "$fail"
}

push_assets_podcast "$@"
