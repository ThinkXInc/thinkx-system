from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from ..config import load_config
from ..utils.io import ensure_dir, read_lines, append_jsonl, write_lines, load_jsonl_set
from ..utils.html import domain_of
from ..utils.text import sha256_hex


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")
    ap.add_argument("--include-processed", action="store_true", help="処理済みURLも出力に含める")
    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir
    urls_dir = data_dir / "urls"
    sitemap_dir = urls_dir / "sitemap"
    ensure_dir(urls_dir)

    state_dir = data_dir / "state"
    ensure_dir(state_dir)
    fetched_state = state_dir / "page_fetched.jsonl"
    processed_urls = load_jsonl_set(fetched_state, "url")  # fetch済みを「収集済み」とみなす

    page_urls_jsonl = urls_dir / "page_urls.jsonl"
    page_urls_txt = urls_dir / "page_urls.txt"

    # 既存のpage_urls.jsonlをリセットしたい場合は手動で削除してください
    # ここでは「今回分（新規のみ）」を出す設計
    now = datetime.utcnow().isoformat()

    out_records: List[Dict[str, Any]] = []
    out_url_list: List[str] = []

    # blogs: sitemap抽出済みtxtを読む
    for b in (cfg.settings.get("blogs", []) or []):
        sitemap_url = b["sitemap_url"]
        dom = domain_of(sitemap_url)
        src_file = sitemap_dir / f"page_urls_{dom}.txt"
        urls = read_lines(src_file)
        for u in urls:
            if (not args.include_processed) and (u in processed_urls):
                continue
            rec = {
                "url": u,
                "source_type": "blog",
                "media_title": b.get("media_title", ""),
                "date_hint": "",
                "title_hint": "",
                "created_at": now,
                "page_id": sha256_hex(u),
            }
            out_records.append(rec)
            out_url_list.append(u)

    # interviews: settings.yamlから直接
    for it in (cfg.settings.get("interviews", []) or []):
        u = it["url"]
        if (not args.include_processed) and (u in processed_urls):
            continue
        rec = {
            "url": u,
            "source_type": "interview",
            "media_title": it.get("media_title", ""),
            "date_hint": it.get("date_hint", "") or "",
            "title_hint": it.get("title_hint", "") or "",
            "created_at": now,
            "page_id": sha256_hex(u),
        }
        out_records.append(rec)
        out_url_list.append(u)

    # 重複排除
    seen = set()
    uniq_records = []
    for r in out_records:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        uniq_records.append(r)

    # 出力
    # jsonl
    if page_urls_jsonl.exists():
        page_urls_jsonl.unlink()
    for r in uniq_records:
        append_jsonl(page_urls_jsonl, r)

    # txt
    out_url_list = sorted(set(out_url_list))
    write_lines(page_urls_txt, out_url_list)

    print(f"[ok] wrote: {page_urls_jsonl} ({len(uniq_records)} records)")
    print(f"[ok] wrote: {page_urls_txt} ({len(out_url_list)} urls)")


if __name__ == "__main__":
    main()
