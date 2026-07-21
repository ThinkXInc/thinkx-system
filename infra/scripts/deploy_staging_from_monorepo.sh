#!/usr/bin/env bash
# thinkx-system/infra/scripts/deploy_staging_from_monorepo.sh
#
# 手元で作ったもの(origin/monorepo)を staging に出す。
#
#   使い方: bash infra/scripts/deploy_staging_from_monorepo.sh [branch]
#           branch を省略すると monorepo。別の編集ブランチから出したいときだけ指定する。
#
# staging が追っているのは origin/develop なので、monorepo に push しただけでは
# staging は何も反応しない。このスクリプトが develop へ取り込むところまでやる。
#
# あわせて、staging の上で直接編集して develop に push されたものを monorepo へ
# 戻す(D-61)。戻しを先に済ませてから出すので、手元と staging が食い違ったまま
# 進むことがない。
#
# 本番へ出すのは deploy_production_from_staging.sh。こちらは staging まで。
# 対称に作ってあるので、順に読めば同じ形をしている。

set -euo pipefail

deploy_staging_from_monorepo() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local src="${1:-monorepo}"
  local sha back svc ans host fail=0
  local -a targets=()

  command -v gh >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が無い${Z}"; return 1; }
  gh auth status >/dev/null 2>&1 || { printf '%b\n' "${R}FAIL: gh が未認証。gh auth login を実行する${Z}"; return 1; }
  [ -f infra/run/sync_from_origin.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  git fetch --quiet origin
  git rev-parse --verify --quiet "origin/$src" >/dev/null ||
    { printf '%b\n' "${R}FAIL: origin/$src が無い${Z}"; return 1; }

  # 1. staging 由来のコミットを手元へ戻す(D-61)
  back="$(git rev-list --count "origin/$src..origin/develop")"
  if [ "$back" != 0 ]; then
    echo
    echo "== staging で作られて、まだ手元に無いコミット($back 件)=="
    git log --oneline "origin/$src..origin/develop"
    echo
    printf '%b\n' "${Y}先にこれを $src へ取り込みます${Z}"
    # branch は切り替えない(D-49: 単一ディレクトリを全セッションが共有しているため、
    # 切替は他セッションの作業ツリーを壊す)。今いる branch へ取り込むだけにする。
    [ "$(git rev-parse --abbrev-ref HEAD)" = "$src" ] ||
      { printf '%b\n' "${R}FAIL: 今 $src に居ません(現在: $(git rev-parse --abbrev-ref HEAD))。branch は切り替えないので、$src で実行してください${Z}"; return 1; }
    git merge --quiet --no-edit "origin/develop"
    git push --quiet origin "$src"
    git fetch --quiet origin
    printf '%b\n' "${G}OK: $src に取り込みました${Z}"
  fi

  sha="$(git rev-parse "origin/$src")"

  if git merge-base --is-ancestor "$sha" origin/develop 2>/dev/null; then
    printf '%b\n' "${Y}develop は既に $src の内容を含んでいます。staging への反映だけをやり直します${Z}"
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
    done <<< "$(git diff --name-only origin/develop "$sha")"

    echo
    echo "== staging に出す内容 =="
    git log --oneline origin/develop.."$sha"
    echo
    echo "== 再起動されるもの =="
    if [ "${#targets[@]}" -eq 0 ]; then echo "  なし(配信物の変更なし)"; else printf '  %s\n' "${targets[@]}"; fi
    echo

    printf '%b' "${Y}この内容を staging に出します。よければ yes と入力: ${Z}"
    read -r ans
    [ "$ans" = yes ] || { printf '%b\n' "${Y}中止しました(何も変更していません)${Z}"; return 0; }

    echo "== $src を develop へ =="
    gh pr create --base develop --head "$src" --title "staging: $src の内容を出す" --body "" >/dev/null
    gh pr merge "$src" --merge --delete-branch=false >/dev/null
    git fetch --quiet origin
  fi

  # 2. staging のサーバーを develop に合わせる。
  # timer が入っていれば60秒以内に勝手に追いつくが、ここで実行して結果をその場で見せる。
  # timer が先に引いていれば「既に一致」で即座に何もせず返るので、二重に走っても衝突しない。
  #
  # 実行する本体は origin/develop から取り出して ssh の標準入力で渡す。サーバーの
  # checkout にあるファイルを使うと、そのファイル自体をこれから配る回に「まだ無い」で止まる。
  for host in supercom-web1-stg supercom-lb1-stg; do
    echo
    echo "== $host を develop に合わせる =="
    git show "origin/develop:infra/run/sync_from_origin.sh" \
      | ssh -o ConnectTimeout=8 "$host" 'sudo bash -s staging' || fail=$((fail+1))
  done

  if [ "$fail" -ne 0 ]; then
    echo
    printf '%b\n' "${R}FAIL: staging への反映が止まりました${Z}"
    printf '%b\n' "${Y}  git 側(develop への取り込み)は終わっています。やり直す必要はありません。${Z}"
    printf '%b\n' "${Y}  上に出ている理由を解消してから、同じコマンドをもう一度実行してください。${Z}"
    return 1
  fi

  echo
  echo "== 確認(staging の web に直接) =="
  ssh -o ConnectTimeout=8 supercom-web1-stg 'for hp in "thinkxinc.com:8005" "truetechjapan.com:8005" "transformism.art:8006" "kazukiotsuka.com:8007"; do
      h="${hp%%:*}"; p="${hp##*:}"
      c="$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Host: $h" "http://localhost:$p/" || true)"
      [ "$c" = 200 ] && printf "  \033[32m%-24s %s\033[0m\n" "$h" "$c" || printf "  \033[31m%-24s %s\033[0m\n" "$h" "$c"
    done'

  printf '%b\n' "${G}OK: staging へ反映しました${Z}"
  printf '%b\n' "${Y}  本番へ出すのは: bash infra/scripts/deploy_production_from_staging.sh${Z}"
}

deploy_staging_from_monorepo "$@"
