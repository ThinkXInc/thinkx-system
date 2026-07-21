#!/usr/bin/env bash
# thinkx-system/infra/scripts/deploy_production_from_staging.sh
#   【分類: 変更系(本番に反映する・これが承認そのもの)】
#
# 今 staging で動いているもの(origin/develop)を、そのまま凍結して本番へ出す。
# staging で目視確認した状態と、本番に出るものが同一であることを保証する。
#
#   使い方: bash infra/scripts/deploy_production_from_staging.sh
#
# これを実行することが「承認」である。実行した瞬間の origin/develop が release として
# 凍結され、以後 develop がどう動いても本番に出るのはこの一点だけになる。
# 承認と cut を別々の操作にすると隙間ができ、隙間に編集が入る(デプロイ手順書の原則)。
#
# やること:
#   1. origin/develop を凍結して release/<日付> を切る
#   2. release -> production の PR を作ってマージする
#   3. 変更パスから再起動が要るサービスを判定し、prod へ反映する
#   4. 4サイトの応答を確認する
#
# 止まる場合は何も壊さずに止まる(deploy.sh が ff-only + dirty チェックで守る)。

set -euo pipefail

deploy_production_from_staging() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local sha day br n svc ans u code
  local -a targets=()

  command -v gh >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が無い${Z}"; return 1; }
  gh auth status >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が未認証。gh auth login を実行する${Z}"; return 1; }
  [ -f infra/scripts/deploy.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  git fetch --quiet origin
  sha="$(git rev-parse origin/develop)"

  if [ "$sha" = "$(git rev-parse origin/production)" ]; then
    printf '%b\n' "${Y}本番は既に staging と同じです。出すものがありません${Z}"
    return 0
  fi

  # 再起動が要るサービスを変更パスから判定する(deploy_tick.sh の services_for と同じ対応)
  while read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
      thinkx/*)          svc=thinkx ;;
      transformism/*)    svc=transformism ;;
      kazukiotsukacom/*) svc=kazukiotsukacom ;;
      nginx-web-root/*)  svc=nginx-web-root ;;
      loadbalancer/*)    svc=loadbalancer ;;
      *) continue ;;
    esac
    case " ${targets[*]-} " in *" $svc "*) ;; *) targets+=("$svc") ;; esac
  done <<< "$(git diff --name-only origin/production "$sha")"

  echo
  echo "== 本番に出す内容 =="
  git log --oneline origin/production.."$sha"
  echo
  echo "== 承認対象 =="
  echo "  $sha"
  echo "== 再起動するサービス =="
  if [ "${#targets[@]}" -eq 0 ]; then
    echo "  なし(配信物の変更なし)"
  else
    printf '  %s\n' "${targets[@]}"
  fi
  echo

  printf '%b' "${Y}この内容を本番に反映します。よければ yes と入力: ${Z}"
  read -r ans
  [ "$ans" = yes ] || { printf '%b\n' "${Y}中止しました(何も変更していません)${Z}"; return 0; }

  # release/<日付> を切る。同日に2回目以降は連番を付ける
  day="$(date +%Y-%m-%d)"
  br="release/$day"; n=2
  while git rev-parse --verify --quiet "origin/$br" >/dev/null; do br="release/$day-$n"; n=$((n+1)); done

  echo "== $br を切る(承認の凍結)=="
  git branch "$br" "$sha"
  git push --quiet origin "$br"

  echo "== $br -> production =="
  gh pr create --base production --head "$br" --title "$br" --body "承認 SHA: $sha" >/dev/null
  gh pr merge "$br" --merge --delete-branch=false >/dev/null

  if [ "${#targets[@]}" -gt 0 ]; then
    echo "== prod へ反映 =="
    bash infra/scripts/deploy.sh prod "${targets[@]}" || {
      echo
      printf '%b\n' "${R}FAIL: サーバーへの反映が止まりました${Z}"
      printf '%b\n' "${Y}  release の凍結と production への取り込みは完了しています($br)。${Z}"
      printf '%b\n' "${Y}  git 側はやり直す必要がありません。上の DIRTY / NON-FF / WRONG-BRANCH の${Z}"
      printf '%b\n' "${Y}  指示に従ってサーバーを整えてから、次の1行だけを再実行してください:${Z}"
      echo
      printf '%b\n' "    bash infra/scripts/deploy.sh prod ${targets[*]}"
      echo
      return 1
    }
  fi

  # 確認は web に直接当てる。素のドメイン(thinkxinc.com 等)は DNS 未切替でオンプレを
  # 指しており、AWS のデプロイが成功しようが失敗しようが 200 を返す(2026-07-21 実測)。
  # 公開ドメインでの確認は DNS 切替後に意味を持つ。
  echo "== 確認(AWS の web に直接) =="
  ssh -o ConnectTimeout=8 supercom-web1 'for hp in "thinkxinc.com:8005" "transformism.art:8006" "kazukiotsuka.com:8007"; do
      h="${hp%%:*}"; p="${hp##*:}"
      c="$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Host: $h" "http://localhost:$p/" || true)"
      [ "$c" = 200 ] && printf "  \033[32m%-24s %s\033[0m\n" "$h" "$c" || printf "  \033[31m%-24s %s\033[0m\n" "$h" "$c"
    done'
  printf '%b\n' "${Y}  公開ドメインはまだオンプレを指しています(DNS 未切替)。AWS の確認は prod.* か上記で行う${Z}"

  printf '%b\n' "${G}OK: $br を本番へ反映しました($sha)${Z}"
}

deploy_production_from_staging "$@"
