#!/usr/bin/env bash
# thinkx-system/infra/scripts/request_production_release.sh
#
# 変更系。staging で確認済みの origin/develop から release を切って push し、
# production への PullRequest を作り、マージ用 URL を提示して終わる。**マージはしない。**
# マージするのはオーナー(GitHub 上・スマホ可)で、そのマージが承認である(D-50 L2b)。
# マージ後は本番の deploy-timer が 60 秒以内に反映する。
#
#   使い方: bash infra/scripts/request_production_release.sh
#
# オーナー機から本番反映まで一気に完走させる経路は、これではなく
# deploy_production_from_staging.sh を使う(実行そのものが承認で、マージまで行う)。
# 2つの経路は独立した別スクリプトである(オーナー指示 2026-08-12)。
#
# 注意: この経路で本番に出るのは git 管理物だけである。views/video などの
# git 管理外アセットを含む変更は、オーナー機から deploy_production_from_staging.sh で
# 出す(staging から本番 web へは名前解決できず届かない。2026-08-07 実測)。

set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]:-$0}")/lib/banner.sh"

request_production_release() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local sha day br n svc ans rel pr_url
  local -a targets=()

  command -v gh >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が無い${Z}"; return 1; }
  gh auth status >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が未認証。gh auth login を実行する${Z}"; return 1; }
  [ -f infra/run/sync_from_origin.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  git fetch --quiet origin
  sha="$(git rev-parse origin/develop)"

  # すでに production の中身がこれと同一なら、出すものが無い。
  # 比較は祖先関係でなく tree で行う(squash merge されても同一内容を検出できる)。
  if [ "$(git rev-parse "$sha^{tree}")" = "$(git rev-parse "origin/production^{tree}")" ]; then
    printf '%b\n' "${Y}production は既に staging と同一の中身です。出すものはありません${Z}"
    return 0
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
  done <<< "$(git diff --name-only origin/production "$sha")"

  banner "develop -> production(マージされると本番に出る内容)"
  git --no-pager log --oneline origin/production.."$sha"
  echo
  echo "承認対象: $sha"

  banner "再起動(変更)されるサービス"
  if [ "${#targets[@]}" -eq 0 ]; then echo "  なし(配信物の変更なし)"; else printf '  %s\n' "${targets[@]}"; fi
  echo

  printf '%b' "${Y}continue? (yes/no): ${Z}"
  read -r ans
  [ "$ans" = yes ] || { printf '%b\n' "${Y}中止しました(何も変更していません)${Z}"; return 0; }

  day="$(date +%Y-%m-%d)"
  br="release/$day"; n=2
  while git rev-parse --verify --quiet "origin/$br" >/dev/null; do br="release/$day-$n"; n=$((n+1)); done

  # release が squash merge されると production の履歴が develop から切れ、次の PR が
  # CONFLICTING になって merge できない(2026-08-12 PR #37 実測)。切れている場合は
  # release の先頭に production を第2親に持つ merge commit を作って履歴を繋ぐ。
  # tree は $sha と同一なので、staging で確認した中身は 1 bit も変わらない。
  rel="$sha"
  if ! git merge-base --is-ancestor origin/production "$sha"; then
    echo "tying production history into $br (中身は origin/develop のまま)..."
    rel="$(git commit-tree "$sha^{tree}" -p "$sha" -p "$(git rev-parse origin/production)" \
      -m "release: production の履歴を繋ぐ(tree は origin/develop $sha と同一)")"
  fi

  echo
  echo "cutting release branch $br (マージ待ちの凍結)..."
  git branch "$br" "$rel"
  git push --quiet origin "$br"

  echo "creating PullRequest ($br->production)..."
  pr_url="$(gh pr create --base production --head "$br" --title "$br" --body "承認 SHA: $sha")"

  banner "オーナーの承認待ち"
  echo "マージ用 URL(マージ = 承認):"
  echo "  $pr_url"
  echo
  echo "マージ後は本番の deploy-timer が 60 秒以内に反映します。確認:"
  echo "  https://thinkxinc.com/"
  echo "  https://truetechjapan.com/"
  echo "  https://transformism.art/"
  echo "  https://kazukiotsuka.com/"
  printf '%b\n' "${G}OK: release を作りました。マージはオーナーが行います(このスクリプトはマージしません)${Z}"
}

request_production_release "$@"
