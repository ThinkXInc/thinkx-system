#!/usr/bin/env bash
# thinkx-system/infra/scripts/deploy_staging_from_monorepo.sh
#
# 次の2つを実行する。
#
#   bash infra/scripts/pr_and_merge_to_develop.sh monorepo
#   bash infra/scripts/deploy_staging_from.sh monorepo
#
# それだけである。中身は上の2本にある。
# monorepo 以外の branch から出すときは、上の2本を直接叩く。
#
#   使い方: bash infra/scripts/deploy_staging_from_monorepo.sh

set -euo pipefail

deploy_staging_from_monorepo() {
  bash infra/scripts/pr_and_merge_to_develop.sh monorepo || return 1
  bash infra/scripts/deploy_staging_from.sh monorepo || return 1
}

deploy_staging_from_monorepo "$@"
