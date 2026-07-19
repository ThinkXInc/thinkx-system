#!/usr/bin/env bash
# thinkx-system/k00bot2/run/sync_data.sh
#
# Mirror runtime data to /src/k00bot2 and push only that repository. 変更系。

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_REPO="${K00BOT2_DATA_REPO:-/src/k00bot2}"
EXPECTED_REPOSITORY="kazukiotsuka/k00bot2.git"

[ -d "$DATA_REPO/.git" ] || { echo "[error] data repository is not a Git clone: $DATA_REPO"; exit 1; }
REMOTE_URL="$(git -C "$DATA_REPO" remote get-url origin)"
case "$REMOTE_URL" in
  *"$EXPECTED_REPOSITORY") ;;
  *) echo "[error] unexpected data repository remote: $REMOTE_URL"; exit 1 ;;
esac

"$ROOT/venv/bin/python" -m scripts.sync_data_repo "$ROOT/data" "$DATA_REPO/data"
git -C "$DATA_REPO" add -f -A -- data

if git -C "$DATA_REPO" diff --cached --quiet; then
  echo "[ok] data repository: no changes"
else
  git -C "$DATA_REPO" commit -m "data(k00bot2): sync $(date -u +%Y-%m-%dT%H:%MZ)"
  git -C "$DATA_REPO" push origin HEAD
  echo "[ok] data repository: pushed"
fi
