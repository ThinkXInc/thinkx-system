#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source "$ROOT/venv/bin/activate"

python -m scripts.pipeline.post_daily

"$ROOT/run/sync_data.sh" || echo "[warn] data repository sync failed"
