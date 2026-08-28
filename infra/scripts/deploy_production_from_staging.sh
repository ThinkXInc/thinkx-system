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
  local sha day br n svc ans host rel pr_url fail=0
  local -a targets=()

  command -v gh >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が無い${Z}"; return 1; }
  gh auth status >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が未認証。gh auth login を実行する${Z}"; return 1; }
  [ -f infra/run/sync_from_origin.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  git fetch --quiet origin
  sha="$(git rev-parse origin/develop)"

  # すでに production の中身がこれと同一なら、release は切らずに反映だけやり直す。
  # 比較は祖先関係でなく tree で行う。release が squash merge されると production の
  # sha が変わり、--is-ancestor では同一内容を検出できない(2026-08-07 findings)。
  if [ "$(git rev-parse "$sha^{tree}")" = "$(git rev-parse "origin/production^{tree}")" ]; then
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
    done <<< "$(git diff --name-only origin/production "$sha")"

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
    echo "cutting release branch $br (承認の凍結)..."
    git branch "$br" "$rel"
    git push --quiet origin "$br"

    echo "creating PullRequest ($br->production)..."
    pr_url="$(gh pr create --base production --head "$br" --title "$br" --body "承認 SHA: $sha")"
    echo "  $pr_url"
    echo "merging ($br->production)..."
    if ! gh pr merge "$br" --merge --delete-branch=false; then
      printf '%b\n' "${R}FAIL: PullRequest を merge できませんでした${Z}"
      printf '%b\n' "${Y}  release の凍結までは終わっています。サーバーにはまだ触れていません。${Z}"
      printf '%b\n' "${Y}  上のエラーと PR 画面で原因を確認してください: $pr_url${Z}"
      return 1
    fi
    git fetch --quiet origin
  fi

  # 動画などの git 管理外アセットを先に配る。HTML の参照だけが先に行くと、存在しない
  # ファイルを指して 404 になる(2026-07-21 に背景動画の差し替えで実際に問題になった)。
  # 変更が無ければ何も送らないので、毎回呼んで差し支えない。
  banner "アセット(views/video)を確かめる"
  if ! bash infra/scripts/push_assets.sh supercom-web1 thinkx transformism kazukiotsukacom; then
    printf '%b\n' "${R}FAIL: アセットの配布に失敗しました${Z}"
    printf '%b\n' "${Y}  release の凍結と production への取り込みは終わっています。${Z}"
    printf '%b\n' "${Y}  サーバーにはまだ触れていません。原因を直して同じコマンドをもう一度実行してください。${Z}"
    return 1
  fi

  # podcast の編集用データは例外規則の別スクリプトで配る(D-52。汎用規則に混ぜない)。
  # 引数なし = 本番に公開済みの ID だけ差分同期(本番に podcast が居ない間は素通り)
  banner "アセット(podcast データ)を確かめる"
  if ! bash infra/scripts/push_assets_podcast.sh prod; then
    printf '%b\n' "${R}FAIL: podcast データの配布に失敗しました${Z}"
    printf '%b\n' "${Y}  release の凍結と production への取り込みは終わっています。${Z}"
    printf '%b\n' "${Y}  サーバーにはまだ触れていません。原因を直して同じコマンドをもう一度実行してください。${Z}"
    return 1
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
  ssh -o ConnectTimeout=8 supercom-web1 'for hp in "thinkxinc.com:8005" "truetechjapan.com:8005" "transformism.art:8006" "kazukiotsuka.com:8007"; do
      h="${hp%%:*}"; p="${hp##*:}"
      c="$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Host: $h" "http://localhost:$p/" || true)"
      [ "$c" = 200 ] && printf "  \033[32m%-24s %s\033[0m\n" "$h" "$c" || printf "  \033[31m%-24s %s\033[0m\n" "$h" "$c"
    done'
  printf '%b\n' "${Y}  公開ドメインはまだオンプレを指しています(DNS 未切替)${Z}"

  printf '%b\n' "${G}OK: deployed to production${Z}"
}

deploy_production_from_staging "$@"
