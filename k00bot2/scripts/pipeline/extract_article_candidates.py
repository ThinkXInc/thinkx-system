from __future__ import annotations
import argparse
import json
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from ..config import load_config
from ..utils.io import ensure_dir, iter_jsonl, append_jsonl, load_jsonl_set
from ..utils.llm import LLMClient
from ..utils.text import sha1_hex, normalize_text
from ..utils.html import domain_of, clean_title

ITEM_RE = re.compile(r"\{\{(\d)\}\}")  # {{1}}..{{5}}


def parse_scored_items(raw: str) -> List[Tuple[str, int]]:
    chunks = [c.strip() for c in raw.split("---") if c.strip()]
    out: List[Tuple[str, int]] = []
    for c in chunks:
        m = ITEM_RE.search(c)
        if not m:
            continue
        score = int(m.group(1))
        text = ITEM_RE.sub("", c).strip()
        if not text:
            continue
        out.append((text, score))
    return out


def review_path_for(data_dir: Path, page: Dict[str, Any]) -> Path:
    url = page.get("final_url") or page.get("url") or ""
    dom = domain_of(url) if url else "unknown"
    return data_dir / "reviews" / "articles" / dom / f"{page['page_id']}.txt"


def format_fulltext_for_review(text: str, width: int = 110) -> str:
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not t:
        return ""

    if "\n" not in t:
        t = re.sub(r"([。！？!?])", r"\1\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t).strip()

    out_lines: List[str] = []
    for line in t.splitlines():
        line = line.rstrip()
        if not line:
            out_lines.append("")
            continue
        if len(line) <= width:
            out_lines.append(line)
        else:
            out_lines.append(
                textwrap.fill(line, width=width, break_long_words=True, break_on_hyphens=False)
            )

    joined = "\n".join(out_lines)
    joined = re.sub(r"\n{3,}", "\n\n", joined).strip()
    return joined


def write_review_file(path: Path, page: Dict[str, Any], items: List[Tuple[str, int]], template: str) -> None:
    ensure_dir(path.parent)

    page_id = page.get("page_id", "")
    url = page.get("final_url") or page.get("url") or ""
    article_title = clean_title(page.get("title", "") or page.get("title_hint", "") or "")
    media_title = (page.get("media_title") or "").strip()
    published_at = (page.get("published_at") or page.get("date_hint") or "").strip()

    fulltext = format_fulltext_for_review(page.get("text") or "")

    lines: List[str] = []
    lines.append(f"# page_id: {page_id}")
    lines.append(f"# url: {url}")
    lines.append(f"# title: {article_title}")
    lines.append(f"# media_title: {media_title}")
    lines.append(f"# published_at: {published_at}")
    lines.append("#")
    lines.append("# posting_template (settings.yaml posting.template_article):")
    tmpl = (template or "").rstrip("\n")
    if not tmpl.strip():
        tmpl = '{text}\n\n"{article_title} - {media_title}"\n{link}'
    for ln in tmpl.splitlines():
        lines.append("# " + ln)
    lines.append("")
    lines.append("## FULLTEXT")
    lines.append(fulltext)
    lines.append("")
    lines.append("## CANDIDATES")
    if items:
        for text, score in items:
            lines.append("---")
            lines.append(text.strip())
            lines.append(f"{{{{{int(score)}}}}}")
            lines.append("")
    else:
        lines.append("---")
        lines.append("（ここに候補を追加できます）")
        lines.append("{{3}}")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def refresh_review_inplace(path: Path, page: Dict[str, Any], template: str) -> bool:
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    page_id = page.get("page_id", "")
    url = page.get("final_url") or page.get("url") or ""
    article_title = clean_title(page.get("title", "") or page.get("title_hint", "") or "")
    media_title = (page.get("media_title") or "").strip()
    published_at = (page.get("published_at") or page.get("date_hint") or "").strip()
    fulltext = format_fulltext_for_review(page.get("text") or "")

    meta_updates = {
        "page_id": page_id,
        "url": url,
        "title": article_title,
        "media_title": media_title,
        "published_at": published_at,
    }
    for i, line in enumerate(lines):
        if not line.startswith("#"):
            continue
        for k, v in meta_updates.items():
            prefix = f"# {k}:"
            if line.startswith(prefix):
                lines[i] = f"# {k}: {v}"

    # template comment差し替え
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip() == "# posting_template (settings.yaml posting.template_article):":
            start = i
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "" or lines[j].startswith("##"):
                    end = j
                    break
            if end is None:
                end = len(lines)
            break

    if start is not None and end is not None:
        tmpl = (template or "").rstrip("\n")
        if not tmpl.strip():
            tmpl = '{text}\n\n"{article_title} - {media_title}"\n{link}'
        new_block = ["# posting_template (settings.yaml posting.template_article):"] + [
            "# " + ln for ln in tmpl.splitlines()
        ] + [""]
        lines = lines[:start] + new_block + lines[end:]

    # FULLTEXT置換（CANDIDATESは保持）
    idx_full = None
    idx_cand = None
    for i, line in enumerate(lines):
        if line.strip() == "## FULLTEXT":
            idx_full = i
        if line.strip() == "## CANDIDATES":
            idx_cand = i
            break
    if idx_full is None or idx_cand is None or idx_cand <= idx_full:
        return False

    new_full_lines = fulltext.splitlines() if fulltext else [""]
    new_lines = lines[: idx_full + 1] + new_full_lines + [""] + lines[idx_cand:]
    path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    return True


def parse_review_file(path: Path) -> Tuple[Dict[str, str], List[Tuple[str, int]]]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    meta: Dict[str, str] = {}
    for line in lines:
        if not line.startswith("#"):
            continue
        s = line[1:].strip()
        if ":" not in s:
            continue
        k, v = s.split(":", 1)
        meta[k.strip()] = v.strip()

    idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## CANDIDATES":
            idx = i
            break
    cand_text = "\n".join(lines[idx + 1 :]) if idx is not None else content
    items = parse_scored_items(cand_text)
    return meta, items


def load_existing_candidates(out_jsonl: Path) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str], Dict[str, List[Tuple[str, int]]]]:
    """
    既存 article_candidates.jsonl から
    - (page_id, norm_text) -> candidate_id
    - candidate_id -> created_at
    - page_id -> [(text, score)] （review未作成移行用）
    """
    id_map: Dict[Tuple[str, str], str] = {}
    created_map: Dict[str, str] = {}
    by_page: Dict[str, List[Tuple[str, int]]] = {}

    if not out_jsonl.exists():
        return id_map, created_map, by_page

    for obj in iter_jsonl(out_jsonl):
        if obj.get("source_type") != "article":
            continue
        page_id = (obj.get("page_id") or "").strip()
        text = (obj.get("text") or "").strip()
        cid = (obj.get("candidate_id") or "").strip()
        score = int(obj.get("score", 0))
        created_at = (obj.get("created_at") or "").strip()

        if page_id and text and cid:
            key = (page_id, normalize_text(text))
            id_map[key] = cid
            if created_at:
                created_map[cid] = created_at
            by_page.setdefault(page_id, []).append((text, score))

    return id_map, created_map, by_page


def rebuild_article_candidates_from_reviews(
    data_dir: Path,
    out_jsonl: Path,
    id_map: Dict[Tuple[str, str], str],
    created_map: Dict[str, str],
) -> None:
    reviews_dir = data_dir / "reviews" / "articles"
    ensure_dir(reviews_dir)

    now = datetime.utcnow().isoformat()
    tmp = out_jsonl.with_suffix(".jsonl.tmp")
    if tmp.exists():
        tmp.unlink()

    written = 0
    for review_path in sorted(reviews_dir.rglob("*.txt")):
        meta, items = parse_review_file(review_path)

        page_id = meta.get("page_id", "").strip()
        url = meta.get("url", "").strip()
        article_title = clean_title(meta.get("title", "").strip())
        media_title = meta.get("media_title", "").strip()
        published_at = meta.get("published_at", "").strip()

        if not page_id or not url:
            continue

        for text, score in items:
            if "（ここに候補を追加できます）" in text:
                continue
            norm = normalize_text(text)
            if not norm:
                continue

            key = (page_id, norm)
            candidate_id = id_map.get(key) or sha1_hex(f"article|{page_id}|{norm}")
            created_at = created_map.get(candidate_id, now)

            # ★ post_text は作らない（投稿直前にテンプレで組む）
            append_jsonl(
                tmp,
                {
                    "candidate_id": candidate_id,
                    "source_type": "article",
                    "page_id": page_id,
                    "url": url,
                    "article_title": article_title,
                    "media_title": media_title,
                    "published_at": published_at,
                    "text": text,
                    "score": int(score),
                    "created_at": created_at,
                },
            )
            written += 1

    ensure_dir(out_jsonl.parent)
    if out_jsonl.exists():
        out_jsonl.unlink()
    tmp.rename(out_jsonl)
    print(f"[ok] rebuilt article_candidates.jsonl from reviews: {out_jsonl} (records={written})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--refresh-reviews", action="store_true", help="既存reviewのメタ+テンプレ+FULLTEXTのみ更新（CANDIDATES保持）")
    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir

    pages_dir = data_dir / "pages"
    cand_dir = data_dir / "candidates"
    state_dir = data_dir / "state"
    ensure_dir(cand_dir)
    ensure_dir(state_dir)

    out_jsonl = cand_dir / "article_candidates.jsonl"
    llm_done = state_dir / "page_llm_done.jsonl"
    done_pages = load_jsonl_set(llm_done, "page_id")

    template = (cfg.settings.get("posting", {}) or {}).get("template_article", "")

    id_map, created_map, existing_by_page = load_existing_candidates(out_jsonl)

    llm_cfg = cfg.settings.get("llm", {}) or {}
    client = LLMClient(
        provider=llm_cfg.get("provider", "openai"),
        model=llm_cfg.get("model", "gpt-4o-mini"),
        temperature=float(llm_cfg.get("temperature", 0.2)),
    )
    max_chars = int(llm_cfg.get("max_input_chars", 12000))
    prompt_base = cfg.prompts["article_extract_prompt"]
    now = datetime.utcnow().isoformat()

    processed = 0

    if not args.build_only:
        for page_path in pages_dir.rglob("*.json"):
            page = json.loads(page_path.read_text(encoding="utf-8"))
            page_id = page.get("page_id", "")
            review_path = review_path_for(data_dir, page)

            if review_path.exists():
                if args.refresh_reviews:
                    ok = refresh_review_inplace(review_path, page, template=template)
                    if ok:
                        processed += 1
                        print(f"[ok] refreshed review: {review_path}")
                continue

            # 既存候補があればそれをreviewへ移植（LLM不要）
            if page_id in existing_by_page and existing_by_page[page_id]:
                write_review_file(review_path, page, existing_by_page[page_id], template=template)
                processed += 1
                print(f"[ok] created review from existing candidates: {review_path}")
                continue

            text = (page.get("text") or "").strip()
            if not text:
                write_review_file(review_path, page, [], template=template)
                processed += 1
                print(f"[ok] created empty review (no text): {review_path}")
                continue

            if page_id in done_pages:
                write_review_file(review_path, page, [], template=template)
                processed += 1
                print(f"[ok] created empty review (already done): {review_path}")
                continue

            user_prompt = (
                f"{prompt_base}\n\n"
                f"[ページ情報]\n"
                f"URL: {page.get('final_url') or page.get('url')}\n"
                f"タイトル: {page.get('title')}\n"
                f"媒体: {page.get('media_title')}\n"
                f"日付: {page.get('published_at')}\n\n"
                f"[本文]\n{(page.get('text') or '')[:max_chars]}"
            )
            try:
                res = client.chat(user=user_prompt, system="あなたは優秀なSNS編集者です。")
                items = parse_scored_items(res)
            except Exception as e:
                print(f"[fail llm] page_id={page_id} : {e}")
                continue

            write_review_file(review_path, page, items, template=template)
            append_jsonl(llm_done, {"page_id": page_id, "done_at": now})
            processed += 1
            print(f"[ok] created review from LLM: {review_path} (items={len(items)})")

    else:
        if args.refresh_reviews:
            for page_path in pages_dir.rglob("*.json"):
                page = json.loads(page_path.read_text(encoding="utf-8"))
                review_path = review_path_for(data_dir, page)
                if review_path.exists():
                    ok = refresh_review_inplace(review_path, page, template=template)
                    if ok:
                        processed += 1
                        print(f"[ok] refreshed review: {review_path}")

    rebuild_article_candidates_from_reviews(
        data_dir=data_dir,
        out_jsonl=out_jsonl,
        id_map=id_map,
        created_map=created_map,
    )

    print(f"[done] reviews_created_or_refreshed={processed}")


if __name__ == "__main__":
    main()
