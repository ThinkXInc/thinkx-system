from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..config import load_config
from ..utils.io import ensure_dir, append_jsonl, iter_jsonl
from ..utils.html import domain_of
from ..utils.text import sha256_hex, trim_plaintext, count_x_chars
from ..utils.dedup import text_hash


def locate_page_json(data_dir: Path, url: str) -> Optional[Path]:
    """
    fetch_pages.py の仕様に合わせて
    data/pages/<domain>/<sha256(url)>.json を探す
    """
    dom = domain_of(url)
    page_id = sha256_hex(url)
    p = data_dir / "pages" / dom / f"{page_id}.json"
    return p if p.exists() else None


def build_post_text(quote: str, article_title: str, media_title: str, link: str) -> str:
    fixed = f'\n\n"{article_title} - {media_title}"\n{link}'
    fixed_len = count_x_chars(fixed)
    allow = max(0, 280 - fixed_len)
    q = trim_plaintext(quote.strip(), allow)
    return (q + fixed).strip()


def read_quote(args) -> str:
    if args.quote:
        return args.quote
    if args.quote_file:
        return Path(args.quote_file).read_text(encoding="utf-8")
    # stdin
    import sys
    data = sys.stdin.read()
    return data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")

    # 入力方法
    ap.add_argument("--url", default="", help="対象ページURL（推奨）")
    ap.add_argument("--page-json", default="", help="data/pages/... のjsonを直接指定（URLが無いとき）")

    ap.add_argument("--score", type=int, default=5)
    ap.add_argument("--quote", default="", help="引用文（短い場合）")
    ap.add_argument("--quote-file", default="", help="引用文をファイルから読む（長い/改行ありに推奨）")

    # page jsonが無い場合の手動補助
    ap.add_argument("--article-title", default="")
    ap.add_argument("--media-title", default="")
    ap.add_argument("--link", default="")
    ap.add_argument("--published-at", default="")

    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir
    cand_dir = data_dir / "candidates"
    ensure_dir(cand_dir)

    manual_path = cand_dir / "manual_candidates.jsonl"

    quote = read_quote(args).strip()
    if not quote:
        raise SystemExit("quote is empty. Use --quote / --quote-file / stdin.")

    page = None
    url = args.url.strip()

    if args.page_json:
        page_path = Path(args.page_json)
        if not page_path.exists():
            raise SystemExit(f"page json not found: {page_path}")
        page = json.loads(page_path.read_text(encoding="utf-8"))
        if not url:
            url = page.get("url", "") or page.get("final_url", "")
    else:
        if not url:
            raise SystemExit("Specify --url or --page-json")
        page_path = locate_page_json(data_dir, url)
        if page_path and page_path.exists():
            page = json.loads(page_path.read_text(encoding="utf-8"))

    # ページ情報を決定（page jsonがあれば優先、なければ引数）
    article_title = (page.get("title") if page else "") or args.article_title
    media_title = (page.get("media_title") if page else "") or args.media_title
    link = (page.get("final_url") if page else "") or (page.get("url") if page else "") or args.link or url
    published_at = (page.get("published_at") if page else "") or args.published_at

    if not article_title:
        article_title = "(untitled)"
    if not media_title:
        media_title = "(unknown)"

    post_text = build_post_text(quote, article_title, media_title, link)

    if count_x_chars(post_text) > 280:
        raise SystemExit("post_text still exceeds 280 (should not happen). Please shorten quote.")

    # 既存manualと重複しないように candidate_id を安定生成
    th = text_hash(post_text)
    candidate_id = f"manual-{th}"

    # 既に同じcandidate_idが存在するなら二重追加しない
    for obj in iter_jsonl(manual_path):
        if obj.get("candidate_id") == candidate_id:
            print(f"[skip] already exists: {candidate_id}")
            return

    now = datetime.now(timezone.utc).isoformat()

    append_jsonl(
        manual_path,
        {
            "candidate_id": candidate_id,
            "source_type": "article_manual",
            "url": link,
            "article_title": article_title,
            "media_title": media_title,
            "published_at": published_at,
            "text": quote,
            "score": int(args.score),
            "post_text": post_text,
            "created_at": now,
        },
    )

    print(f"[ok] added manual candidate: {candidate_id}")
    print("Next: python -m scripts.pipeline.merge_candidates")


if __name__ == "__main__":
    main()
