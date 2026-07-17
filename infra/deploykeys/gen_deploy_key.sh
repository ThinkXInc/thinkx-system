#!/usr/bin/env bash
# thinkx-system/infra/deploykeys/gen_deploy_key.sh
#
# GitHub Deploy key(read-only)を infra/deploykeys/ に生成する(Mac 側で実行)。
#
#   使い方: infra/deploykeys/gen_deploy_key.sh <repo>...
#   例:     infra/deploykeys/gen_deploy_key.sh simplicity thinkx-system
#
# 既に鍵があるときは上書きするか確認し、yes なら生成、それ以外は何もしない。
# 生成後、登録用の pbcopy コマンドと GitHub URL を表示する(Allow write access は付けない)。

gen_deploy_key() {
  local ws repo key ans
  local G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
  ws="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
  [ $# -ge 1 ] || { echo "usage: gen_deploy_key.sh <repo>...   例: gen_deploy_key.sh simplicity thinkx-system" >&2; return 1; }

  for repo in "$@"; do
    key="$ws/infra/deploykeys/deploy_$repo"
    if [ -f "$key" ]; then
      printf '%s は既にある。上書きする? [yes/N]: ' "deploy_$repo"
      read -r ans
      [ "$ans" = "yes" ] || { printf '%b\n' "${Y}skip: $repo(既存を維持)${Z}"; continue; }
      rm -f "$key" "$key.pub"
    fi
    ssh-keygen -t ed25519 -N '' -C "supercom:kaz:$repo" -f "$key" -q || { printf '%b\n' "${R}FAIL: $repo の鍵生成失敗${Z}"; return 1; }
    printf '%b\n' "${G}OK: generated infra/deploykeys/deploy_$repo${Z}"
    echo "  登録: pbcopy < $key.pub"
    echo "  URL : https://github.com/ThinkXInc/$repo/settings/keys  (Allow write access は付けない)"
  done
}

gen_deploy_key "$@"
