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

# data を git へ(月次候補の永続化。push 失敗でも候補生成は成立済みなので止めない)
git add data
if git diff --cached --quiet; then
  echo "[ok] data: no changes"
else
  git commit -m "data(k00bot2): monthly $(date -u +%Y-%m-%dT%H:%MZ)"
  git push || echo "[warn] data push failed (commit remains local)"
fi