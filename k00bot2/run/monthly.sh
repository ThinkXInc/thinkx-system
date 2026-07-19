#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source "$ROOT/venv/bin/activate"

python -m scripts.pipeline.sitemap_to_urls --all
python -m scripts.pipeline.build_page_urls
python -m scripts.pipeline.fetch_pages
python -m scripts.pipeline.extract_article_candidates
python -m scripts.pipeline.fetch_x_latest
python -m scripts.pipeline.merge_candidates

"$ROOT/run/sync_data.sh" || echo "[warn] data repository sync failed"
