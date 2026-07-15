#!/usr/bin/env bash
# ============================================================
# infra/scripts/cost-hook.sh
#   Claude Code の PostToolUse フック本体。
#   Edit/Write された対象が infra/terraform/*.tf のときだけ、月額概算を出力する。
#   settings.json からはこのスクリプトを呼ぶだけにして、settings を薄く・壊れにくく保つ。
#
#   Claude Code は PostToolUse で JSON を stdin に渡す(.tool_input.file_path に編集対象)。
# ============================================================
set -euo pipefail

payload="$(cat)"
file="$(
  printf '%s' "$payload" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' \
    2>/dev/null || true
)"

case "$file" in
  *infra/terraform/*.tf)
    here="$(dirname "${BASH_SOURCE[0]}")"
    echo "== インフラ変更を検知: ${file} → 月額概算(prod / staging)=="
    "$here/cost-estimate.sh" staging
    "$here/cost-estimate.sh" prod
    ;;
  *)
    : # 対象外(terraform 以外の編集)は何もしない
    ;;
esac
