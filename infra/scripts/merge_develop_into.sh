#!/usr/bin/env bash
# thinkx-system/infra/scripts/merge_develop_into.sh
#
# develop を、手元の指定 branch に取り込む。
#
#   使い方: bash infra/scripts/merge_develop_into.sh <branch>
#   例:     bash infra/scripts/merge_develop_into.sh monorepo
#
# staging のサーバーの上で直接編集して commit・push したものは develop に入る。
# それを手元へ戻すのがこのスクリプトである(D-61)。戻さないまま作業を続けると、
# 手元と staging が食い違ったまま離れていく。
#
# branch は切り替えない(D-49: 単一ディレクトリを全セッションが共有しているため、
# 切替は他セッションの作業ツリーを壊す)。今いる branch と指定が違えば止める。

set -euo pipefail

merge_develop_into() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local dst cur back ans

  if [ "$#" -eq 0 ]; then
    printf '%b\n' "${Y}取り込み先の branch を指定してください。${Z}"
    echo "  使い方: bash infra/scripts/merge_develop_into.sh <branch>"
    echo "  例:     bash infra/scripts/merge_develop_into.sh monorepo"
    return 1
  fi
  dst="$1"

  [ -f infra/run/sync_from_origin.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  cur="$(git rev-parse --abbrev-ref HEAD)"
  [ "$cur" = "$dst" ] ||
    { printf '%b\n' "${R}FAIL: 今 $dst に居ません(現在: $cur)。branch は切り替えないので、$dst で実行してください${Z}"; return 1; }

  [ -z "$(git status --porcelain)" ] ||
    { printf '%b\n' "${R}FAIL: 手元に未コミットの変更があります。先に commit してください${Z}"; git status --short; return 1; }

  git fetch --quiet origin

  back="$(git rev-list --count "HEAD..origin/develop")"
  if [ "$back" = 0 ]; then
    printf '%b\n' "${G}$dst は既に develop の内容を含んでいます。やることはありません${Z}"
    return 0
  fi

  echo "== develop にあって $dst に無いコミット($back 件)=="
  git log --oneline "HEAD..origin/develop"
  echo

  printf '%b' "${Y}これを $dst に取り込みます。よければ yes と入力: ${Z}"
  read -r ans
  [ "$ans" = yes ] || { printf '%b\n' "${Y}中止しました(何も変更していません)${Z}"; return 0; }

  git merge --no-edit origin/develop
  git push origin "$dst"

  printf '%b\n' "${G}OK: $dst に取り込んで push しました${Z}"
}

merge_develop_into "$@"
