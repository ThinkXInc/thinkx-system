#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source "$ROOT/venv/bin/activate"

python -m scripts.pipeline.post_daily

# data を git へ(投稿状態の永続化。push 失敗でも投稿は成立済みなので止めない)
git add data
if git diff --cached --quiet; then
  echo "[ok] data: no changes"
else
  git commit -m "data(k00bot2): daily $(date -u +%Y-%m-%dT%H:%MZ)"
  git push || echo "[warn] data push failed (commit remains local)"
fi
