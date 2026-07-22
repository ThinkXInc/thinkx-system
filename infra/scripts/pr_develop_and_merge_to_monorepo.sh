#!/usr/bin/env bash
# thinkx-system/infra/scripts/pr_develop_and_merge_to_monorepo.sh
#
# develop から monorepo への PR を作り、merge し、手元の monorepo を ff で追従させる。
# pr_and_merge_to_develop.sh(monorepo -> develop)の対照。
#
#   使い方: bash infra/scripts/pr_develop_and_merge_to_monorepo.sh
#
# staging の上で直接編集したものは develop に入る(D-61)。それを monorepo に戻すのがこれ。
# 実体の merge は GitHub 側(リモート)で行うので、手元の作業ツリーには触れない。手元は ff で
# monorepo のポインタを進めるだけ(commit を作らない)なので、他セッションの編集中(未コミット)
# を巻き込まない(D-68)。**手元で `git merge origin/develop` を実行しない。**
#
# 引数は取らない。戻す方向は develop -> monorepo の1つしかない(D-64)。

set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]:-$0}")/lib/banner.sh"

# 手元の monorepo を origin/monorepo に ff で合わせる。commit を作らないので、他セッションの
# 編集中(未コミット)には触れない。手元に未 push のコミットがあって分岐している場合だけ ff
# できないので、その事実だけ告げて止まる(リモートの取り込み自体は済んでいる)。
ff_follow() {
  local G=$'\033[32m' Y=$'\033[33m' Z=$'\033[0m' cur
  cur="$(git rev-parse --abbrev-ref HEAD)"
  if [ "$cur" != monorepo ]; then
    printf '%b\n' "${Y}skip: 手元は $cur(monorepo でない)。branch は切り替えない(D-49)。monorepo で 'git merge --ff-only origin/monorepo' を実行してください${Z}"
    return 0
  fi
  if git merge --ff-only origin/monorepo 2>/dev/null; then
    printf '%b\n' "${G}OK: 手元の monorepo を origin/monorepo に追従(ff・commit なし)${Z}"
  else
    printf '%b\n' "${Y}注意: 手元 monorepo に未 push のコミットがあり ff できません。'git push origin monorepo' してから 'git merge --ff-only origin/monorepo' を実行してください(リモートの取り込みは完了しています)${Z}"
  fi
}

pr_develop_and_merge_to_monorepo() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local sha back ans

  command -v gh >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が無い${Z}"; return 1; }
  gh auth status >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が未認証。gh auth login を実行する${Z}"; return 1; }
  [ -f infra/run/sync_from_origin.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  git fetch --quiet origin
  git rev-parse --verify --quiet origin/develop >/dev/null ||
    { printf '%b\n' "${R}FAIL: origin/develop が無い${Z}"; return 1; }

  sha="$(git rev-parse origin/develop)"

  if git merge-base --is-ancestor "$sha" origin/monorepo 2>/dev/null; then
    printf '%b\n' "${G}monorepo は既に develop の内容を含んでいます${Z}"
    ff_follow
    return 0
  fi

  # merge commit は中身を持たないので数えない(PR の履歴が並ぶだけで読めなくなる)
  back="$(git rev-list --count --no-merges "origin/monorepo..$sha")"
  banner "develop -> monorepo に入るコミット($back 件)"
  git --no-pager log --oneline --no-merges "origin/monorepo..$sha"
  echo

  printf '%b' "${Y}continue? (yes/no): ${Z}"
  read -r ans
  [ "$ans" = yes ] || { printf '%b\n' "${Y}中止しました(何も変更していません)${Z}"; return 0; }

  echo
  echo "creating PullRequest (develop->monorepo)..."
  gh pr create --base monorepo --head develop --title "monorepo: develop の内容を取り込む" --body "" >/dev/null

  echo "merging (develop->monorepo)..."
  gh pr merge develop --merge --delete-branch=false >/dev/null

  git fetch --quiet origin
  printf '%b\n' "${G}OK: merged to monorepo (remote)${Z}"

  ff_follow
}

pr_develop_and_merge_to_monorepo "$@"
