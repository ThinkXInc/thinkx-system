#!/usr/bin/env bash
# thinkx-system/infra/scripts/deploy_production_from_staging.sh
#
# 今 staging で動いているもの(origin/develop)を、そのまま凍結して本番へ出す。
# staging で目視確認した状態と、本番に出るものが同一であることを保証する。
#
#   使い方: bash infra/scripts/deploy_production_from_staging.sh
#
# これを実行することが「承認」である。実行した瞬間の origin/develop が release として
# 凍結され、以後 develop がどう動いても本番に出るのはこの一点だけになる。
#
# 途中で止まったら、同じコマンドをもう一度実行すればよい。すでに production へ
# 取り込み済みなら release を切り直さず、サーバーへの反映だけをやり直す。

set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]:-$0}")/lib/banner.sh"

deploy_production_from_staging() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local sha day br n svc ans host fail=0
  local -a targets=()

  command -v gh >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が無い${Z}"; return 1; }
  gh auth status >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が未認証。gh auth login を実行する${Z}"; return 1; }
  [ -f infra/run/sync_from_origin.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  git fetch --quiet origin
  sha="$(git rev-parse origin/develop)"

  # すでに production が この内容を含んでいるなら、release は切らずに反映だけやり直す
  if git merge-base --is-ancestor "$sha" origin/production 2>/dev/null; then
    printf '%b\n' "${Y}production は既に staging の内容を含んでいます。反映だけをやり直します${Z}"
  else
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
    done <<< "$(git diff --name-only "origin/production...$sha")"

    banner "develop -> production(本番に出す内容)"
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

    echo
    echo "cutting release branch $br (承認の凍結)..."
    git branch "$br" "$sha"
    git push --quiet origin "$br"

    echo "creating PullRequest ($br->production)..."
    gh pr create --base production --head "$br" --title "$br" --body "承認 SHA: $sha" >/dev/null
    echo "merging ($br->production)..."
    gh pr merge "$br" --merge --delete-branch=false >/dev/null
    git fetch --quiet origin
  fi

  # サーバーを production に合わせる。実装はサーバー側の sync_from_origin.sh 1つだけで、
  # systemd timer が呼ぶのも同じもの。手動と自動で挙動が食い違わない。
  #
  # 実行する本体は origin/production から取り出して ssh の標準入力で渡す。サーバーの
  # checkout にあるファイルを使うと、そのファイル自体をこれから配る回に「まだ無い」で
  # 止まる(実際に本番と staging LB の両方で無かった。2026-07-21 実測)。
  # 渡すのは Mac の作業ツリーではなく「いま production にあるもの」なので、サーバーが
  # このあと自分で持つことになるものと同一である。
  for host in supercom-web1 supercom-lb1; do
    banner "$host -> production に合わせる"
    git show "origin/production:infra/run/sync_from_origin.sh" \
      | ssh -o ConnectTimeout=8 "$host" 'sudo bash -s prod' || fail=$((fail+1))
  done

  if [ "$fail" -ne 0 ]; then
    echo
    printf '%b\n' "${R}FAIL: サーバーへの反映が止まりました${Z}"
    printf '%b\n' "${Y}  何も壊れていません。release の凍結と production への取り込みは終わっています。${Z}"
    printf '%b\n' "${Y}  上の DIRTY / NON-FF / WRONG-BRANCH の指示に従ってサーバーを整えてから、${Z}"
    printf '%b\n' "${Y}  同じコマンドをもう一度実行してください(release は切り直しません)。${Z}"
    return 1
  fi

  # 確認は web に直接当てる。素のドメインは DNS 未切替でオンプレを指しており、
  # AWS の成否に関わらず 200 を返す(2026-07-21 実測)。
  banner "確認(AWS の web に直接)"
  ssh -o ConnectTimeout=8 supercom-web1 'for hp in "thinkxinc.com:8005" "transformism.art:8006" "kazukiotsuka.com:8007"; do
      h="${hp%%:*}"; p="${hp##*:}"
      c="$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Host: $h" "http://localhost:$p/" || true)"
      [ "$c" = 200 ] && printf "  \033[32m%-24s %s\033[0m\n" "$h" "$c" || printf "  \033[31m%-24s %s\033[0m\n" "$h" "$c"
    done'
  printf '%b\n' "${Y}  公開ドメインはまだオンプレを指しています(DNS 未切替)${Z}"

  printf '%b\n' "${G}OK: deployed to production${Z}"
}

deploy_production_from_staging "$@"
