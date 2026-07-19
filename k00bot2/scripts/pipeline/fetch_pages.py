from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
import json

from ..config import load_config
from ..utils.io import ensure_dir, iter_jsonl, append_jsonl, load_jsonl_set
from ..utils.html import fetch_html, extract_page, domain_of, clean_title
from ..utils.text import sha256_hex


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir

    urls_jsonl = data_dir / "urls" / "page_urls.jsonl"
    pages_dir = data_dir / "pages"
    state_dir = data_dir / "state"
    ensure_dir(pages_dir)
    ensure_dir(state_dir)

    fetched_state = state_dir / "page_fetched.jsonl"
    already = load_jsonl_set(fetched_state, "url")

    n_ok = 0
    n_skip = 0
    n_fail = 0

    for rec in iter_jsonl(urls_jsonl):
        url = rec["url"]
        page_id = rec.get("page_id") or sha256_hex(url)

        if (not args.force) and (url in already):
            n_skip += 1
            continue

        dom = domain_of(url)
        out_dir = pages_dir / dom
        ensure_dir(out_dir)
        out_path = out_dir / f"{page_id}.json"

        try:
            html, final_url = fetch_html(url)
            ex = extract_page(html, url=url, final_url=final_url)

            title_raw = (ex.title or rec.get("title_hint", "") or "").strip()
            title = clean_title(title_raw) or (rec.get("title_hint", "") or "")

            page_obj = {
                "page_id": page_id,
                "url": url,
                "final_url": ex.final_url,
                "source_type": rec.get("source_type", ""),
                "media_title": rec.get("media_title", ""),
                "title_hint": rec.get("title_hint", ""),
                "date_hint": rec.get("date_hint", ""),
                "title_raw": title_raw,
                "title": title,
                "published_at": ex.published_at or rec.get("date_hint", ""),
                "text": ex.text,
                "fetched_at": datetime.utcnow().isoformat(),
            }

            out_path.write_text(json.dumps(page_obj, ensure_ascii=False, indent=2), encoding="utf-8")

            append_jsonl(
                fetched_state,
                {"url": url, "page_id": page_id, "fetched_at": page_obj["fetched_at"]},
            )
            n_ok += 1
            print(f"[ok] fetched {url} -> {out_path}")

        except Exception as e:
            n_fail += 1
            print(f"[fail] {url} : {e}")

    print(f"[done] ok={n_ok} skip={n_skip} fail={n_fail}")


if __name__ == "__main__":
    main()
