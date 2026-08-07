#!/usr/bin/env bash
# thinkx-system/infra/scripts/pr_and_merge_to_develop.sh
#
# 指定した branch から develop への PR を作り、merge するところまでやる。
#
#   使い方: bash infra/scripts/pr_and_merge_to_develop.sh <branch>
#   例:     bash infra/scripts/pr_and_merge_to_develop.sh monorepo
#
# ここでやるのは git だけである。サーバーには触らない。
# staging のサーバーに出すのは deploy_staging.sh。
#
# branch は必ず指定する。既定値を置かない。手元の作業 branch が何かは、そのときの
# 作業によって変わる(monorepo とは限らない)。

set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]:-$0}")/lib/banner.sh"

pr_and_merge_to_develop() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local src sha back svc ans unpushed dirty
  local -a targets=()

  if [ "$#" -eq 0 ]; then
    printf '%b\n' "${Y}branch を指定してください。${Z}"
    echo "  使い方: bash infra/scripts/pr_and_merge_to_develop.sh <branch>"
    echo "  例:     bash infra/scripts/pr_and_merge_to_develop.sh monorepo"
    return 1
  fi
  src="$1"

  command -v gh >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が無い${Z}"; return 1; }
  gh auth status >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が未認証。gh auth login を実行する${Z}"; return 1; }
  [ -f infra/run/sync_from_origin.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  git fetch --quiet origin
  git rev-parse --verify --quiet "origin/$src" >/dev/null ||
    { printf '%b\n' "${R}FAIL: origin/$src が無い${Z}"; return 1; }

  sha="$(git rev-parse "origin/$src")"

  # 出るのは origin/$src であって手元の HEAD ではない(D-58)。push を忘れていると
  # この先が全部緑で完走したうえで古い内容が staging に出る。ここで止める。
  if git show-ref --verify --quiet "refs/heads/$src"; then
    unpushed="$(git rev-list --count "origin/$src..$src")"
    if [ "$unpushed" != 0 ]; then
      banner "手元の $src に origin へ出していないコミット($unpushed 件)"
      git --no-pager log --oneline "origin/$src..$src"
      echo
      printf '%b\n' "${R}FAIL: これらは push しない限り staging にも production にも出ません${Z}"
      echo "To publish them, run:"
      echo "git push origin $src"
      return 1
    fi
  fi

  # 未コミットは止めない。他トラックの WIP が手元にあるのは通常であり、それを
  # 巻き込まないのが D-68 の趣旨。ただし「直したはずのものが出ない」を防ぐため見せる。
  dirty="$(git status --porcelain --untracked-files=no | wc -l | tr -d ' ')"
  if [ "$dirty" != 0 ]; then
    banner "未コミットの変更($dirty 件・これらは出ません)"
    git --no-pager status --porcelain --untracked-files=no
    echo
  fi

  if git merge-base --is-ancestor "$sha" origin/develop 2>/dev/null; then
    printf '%b\n' "${G}develop は既に $src の内容を含んでいます。やることはありません${Z}"
    echo
    echo "If you deploy, run:"
    echo "bash infra/scripts/deploy_staging.sh"
    return 0
  fi

  # staging の上で直接編集されたものが develop に入っていて、手元の branch に無い場合。
  # 止めはしないが、放っておくと手元と staging が食い違ったまま離れていく。
  # merge commit は中身を持たないので数えない(PR の履歴が並ぶだけで読めなくなる)
  back="$(git rev-list --count --no-merges "origin/$src..origin/develop")"
  if [ "$back" != 0 ]; then
    banner "注意: develop にあって $src に無いコミット($back 件)"
    git --no-pager log --oneline --no-merges "origin/$src..origin/develop"
    echo
    printf '%b\n' "${Y}  staging の上で直接編集されたものが手元に戻っていない可能性があります。${Z}"
    echo "To bring them back, run:"
    echo "bash infra/scripts/pr_develop_and_merge_to_monorepo.sh"
    echo
  fi

  # 何が再起動されるかを事前に見せるためだけの判定(実際の判定はサーバー側が行う)
  while read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
      thinkx/*)          svc=thinkx ;;
      transformism/*)    svc=transformism ;;
      kazukiotsukacom/*) svc=kazukiotsukacom ;;
      nginx-web-root/*)  svc=nginx ;;
      loadbalancer/*)    svc=nginx ;;
      *) continue ;;
    esac
    case " ${targets[*]-} " in *" $svc "*) ;; *) targets+=("$svc") ;; esac
  done <<< "$(git diff --name-only "origin/develop...$sha")"

  banner "$src -> develop"
  git --no-pager log --oneline origin/develop.."$sha"

  banner "再起動(変更)されるサービス"
  if [ "${#targets[@]}" -eq 0 ]; then echo "  なし(配信物の変更なし)"; else printf '  %s\n' "${targets[@]}"; fi
  echo

  printf '%b' "${Y}continue? (yes/no): ${Z}"
  read -r ans
  [ "$ans" = yes ] || { printf '%b\n' "${Y}中止しました(何も変更していません)${Z}"; return 0; }

  echo
  echo "creating PullRequest ($src->develop)..."
  gh pr create --base develop --head "$src" --title "develop: $src の内容を取り込む" --body "" >/dev/null

  echo "merging ($src->develop)..."
  gh pr merge "$src" --merge --delete-branch=false >/dev/null

  git fetch --quiet origin
  printf '%b\n' "${G}OK: merged to develop${Z}"
  echo
  echo "If you deploy, run:"
  echo "bash infra/scripts/deploy_staging.sh"
}

pr_and_merge_to_develop "$@"
