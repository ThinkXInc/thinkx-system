#!/usr/bin/env bash
# thinkx-system/infra/scripts/deploy_staging.sh
#
# staging の web と LB を、いま origin/develop にあるものに合わせる。
#
#   使い方: bash infra/scripts/deploy_staging.sh
#
# 引数は取らない。staging へ出す経路は1本しかなく、出るものは常に origin/develop で
# ある。**手元の作業ツリーや branch からは出さない**(D-58「ローカルの Git 履歴とは
# 独立してデプロイできる」)。手元の作業を staging に出したいなら、先に
# pr_and_merge_to_develop.sh <branch> で develop に入れる。
#
# ここでやるのはサーバーへの反映だけである。git には触らない。
#
# timer が入っていれば60秒以内に勝手に追いつくが、ここで実行して結果をその場で見せる。
# timer が先に引いていれば「既に一致」で即座に何もせず返るので、二重に走っても衝突しない。

set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]:-$0}")/lib/banner.sh"

deploy_staging() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local host fail=0

  [ -f infra/run/sync_from_origin.sh ] || { printf '%b\n' "${R}FAIL: リポジトリ直下で実行する${Z}"; return 1; }

  git fetch --quiet origin
  # 動画などの git 管理外アセットを先に配る。HTML の参照だけが先に行くと、存在しない
  # ファイルを指して 404 になる。変更が無ければ何も送らないので、毎回呼んで差し支えない。
  banner "アセット(views/video)を確かめる"
  bash infra/scripts/push_assets.sh supercom-web1-stg thinkx transformism kazukiotsukacom ||
    { printf '%b\n' "${R}FAIL: アセットの配布に失敗しました。サーバーには触れていません${Z}"; return 1; }

  # 実行する本体は origin/develop から取り出して ssh の標準入力で渡す。サーバーの
  # checkout にあるファイルを使うと、そのファイル自体をこれから配る回に「まだ無い」で止まる
  # (実際に本番と staging LB の両方で無かった。2026-07-21 実測)。
  for host in supercom-web1-stg supercom-lb1-stg; do
    banner "$host -> develop に合わせる"
    git show "origin/develop:infra/run/sync_from_origin.sh" \
      | ssh -o ConnectTimeout=8 "$host" 'sudo bash -s staging' || fail=$((fail+1))
  done

  if [ "$fail" -ne 0 ]; then
    echo
    printf '%b\n' "${R}FAIL: staging への反映が止まりました${Z}"
    printf '%b\n' "${Y}  git 側は終わっています。develop を merge し直す必要はありません。${Z}"
    printf '%b\n' "${Y}  上に出ている理由を解消してから、同じコマンドをもう一度実行してください。${Z}"
    return 1
  fi

  banner "確認(staging の web に直接)"
  ssh -o ConnectTimeout=8 supercom-web1-stg 'for hp in "thinkxinc.com:8005" "truetechjapan.com:8005" "transformism.art:8006" "kazukiotsuka.com:8007"; do
      h="${hp%%:*}"; p="${hp##*:}"
      c="$(curl -s -o /dev/null -w "%{http_code}" -m 10 -H "Host: $h" "http://localhost:$p/" || true)"
      [ "$c" = 200 ] && printf "  \033[32m%-24s %s\033[0m\n" "$h" "$c" || printf "  \033[31m%-24s %s\033[0m\n" "$h" "$c"
    done'

  printf '%b\n' "${G}OK: deployed to staging${Z}"
  echo
  echo "If you deploy to production, run:"
  echo "bash infra/scripts/deploy_production_from_staging.sh"
}

deploy_staging "$@"
