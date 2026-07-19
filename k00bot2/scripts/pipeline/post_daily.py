from __future__ import annotations

import argparse
from datetime import datetime, date
import os
import random
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..config import load_config
from ..utils.io import ensure_dir, iter_jsonl, append_jsonl, load_jsonl_set
from ..utils.text import count_x_chars, trim_plaintext
from ..utils.html import clean_title
from ..utils.x_api import XClient, XAPIError


def load_overrides(path: Path) -> Dict[str, Dict[str, Any]]:
    overrides: Dict[str, Dict[str, Any]] = {}
    for o in iter_jsonl(path):
        cid = o.get("candidate_id")
        if cid:
            overrides[cid] = o
    return overrides


def acquire_lock(lock_path: Path) -> int:
    ensure_dir(lock_path.parent)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
    os.write(fd, f"pid={os.getpid()}\n".encode("utf-8"))
    return fd


def release_lock(fd: int, lock_path: Path) -> None:
    try:
        os.close(fd)
    finally:
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            pass


def apply_template(template: str, mapping: Dict[str, str]) -> str:
    out = template
    for k, v in mapping.items():
        out = out.replace("{" + k + "}", v)
    return out


def get_article_template(cfg) -> str:
    # settings.yaml を優先
    tmpl = (((cfg.settings.get("posting") or {}).get("templates") or {}).get("article") or "").strip()
    if tmpl:
        return tmpl
    # 後方互換（旧：prompts.yaml）
    return (cfg.prompts.get("post_template_article") or "").strip()


def render_article_post(candidate: Dict[str, Any], template: str, limit: int = 280) -> str:
    tmpl = (template or "").strip()
    if not tmpl:
        assert False, "no template found."

    quote = (candidate.get("text") or "").strip()
    article_title = clean_title(candidate.get("article_title") or "")
    media_title = (candidate.get("media_title") or "").strip()
    link = (candidate.get("url") or candidate.get("link") or "").strip()

    base = {
        "article_title": article_title,
        "media_title": media_title,
        "link": link,
    }

    fixed = apply_template(tmpl, {**base, "text": ""}).strip()
    allow = max(0, limit - count_x_chars(fixed))

    q = trim_plaintext(quote, allow)
    rendered = apply_template(tmpl, {**base, "text": q}).strip()
    return rendered


def render_final_post_text(candidate: Dict[str, Any], cfg) -> str:
    st = (candidate.get("source_type") or "").strip()
    if st.startswith("article"):
        tmpl = get_article_template(cfg)
        return render_article_post(candidate, template=tmpl, limit=280)

    # X再投稿：そのまま（post_text には依存しない）
    return (candidate.get("text") or "").strip()


def weighted_choice(rnd: random.Random, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not candidates:
        return None
    weights = [max(1, int(c.get("final_score", 1))) for c in candidates]
    total = sum(weights)
    r = rnd.uniform(0, total)
    acc = 0.0
    for c, w in zip(candidates, weights):
        acc += w
        if r <= acc:
            return c
    return candidates[-1]


def pick_many(
    candidates: List[Dict[str, Any]],
    n: int,
    strategy: str,
    min_score: int,
    seed: Optional[int],
) -> List[Dict[str, Any]]:
    pool = [c for c in candidates if int(c.get("final_score", 0)) >= min_score]
    if not pool or n <= 0:
        return []

    if strategy == "highest":
        pool.sort(key=lambda c: int(c.get("final_score", 0)), reverse=True)
        return pool[:n]

    if seed is None:
        seed = int(date.today().strftime("%Y%m%d"))
    rnd = random.Random(seed)

    chosen: List[Dict[str, Any]] = []
    for _ in range(min(n, len(pool))):
        c = weighted_choice(rnd, pool)
        if not c:
            break
        chosen.append(c)
        pool.remove(c)
    return chosen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-posts", type=int, default=0)
    ap.add_argument("--interval-seconds", type=int, default=-1)
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--random", action="store_true")
    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir

    state_dir = data_dir / "state"
    ensure_dir(state_dir)

    lock_path = state_dir / "post_daily.lock"
    try:
        lock_fd = acquire_lock(lock_path)
    except FileExistsError:
        print("[skip] another post_daily is running (lock exists).")
        return

    try:
        posted_state = state_dir / "posted_candidate_ids.jsonl"
        posted_ids = load_jsonl_set(posted_state, "candidate_id")

        overrides_path = state_dir / "overrides.jsonl"
        overrides = load_overrides(overrides_path) if overrides_path.exists() else {}

        cand_path = data_dir / "candidates" / "candidates.jsonl"
        if not cand_path.exists():
            raise SystemExit("candidates.jsonl not found. Run merge_candidates first.")

        post_cfg = cfg.settings.get("posting", {}) or {}
        min_score = int(post_cfg.get("min_score", 2))
        strategy = post_cfg.get("pick_strategy", "weighted_random")
        daily_post_limit = int(post_cfg.get("daily_post_limit", 1))
        interval_seconds = int(post_cfg.get("interval_seconds", 0))

        if args.max_posts > 0:
            daily_post_limit = args.max_posts
        if args.interval_seconds >= 0:
            interval_seconds = args.interval_seconds

        seed: Optional[int] = None
        if args.random:
            seed = int(time.time())
        elif args.seed >= 0:
            seed = args.seed
        else:
            seed = None  # 日付seed

        candidates: List[Dict[str, Any]] = []
        for c in iter_jsonl(cand_path):
            cid = c.get("candidate_id")
            if not cid or cid in posted_ids:
                continue

            o = overrides.get(cid, {})
            if o.get("status", "") == "disabled":
                continue

            base_score = int(c.get("score", 0))
            final_score = int(o.get("manual_score", base_score))
            c["final_score"] = final_score
            candidates.append(c)

        chosen_list = pick_many(
            candidates=candidates,
            n=daily_post_limit,
            strategy=strategy,
            min_score=min_score,
            seed=seed,
        )
        if not chosen_list:
            print("[skip] no candidate to post")
            return

        rendered: List[tuple[Dict[str, Any], str]] = []
        for ch in chosen_list:
            text = render_final_post_text(ch, cfg=cfg)
            if count_x_chars(text) > 280:
                print(f"[warn] rendered text exceeds 280, skipped. candidate_id={ch.get('candidate_id')}")
                continue
            rendered.append((ch, text))

        if not rendered:
            print("[skip] chosen candidates were invalid after rendering")
            return

        if args.dry_run:
            print("----- DRY RUN -----")
            print(f"(seed={seed if seed is not None else 'date-seed'})")
            for i, (ch, text) in enumerate(rendered, 1):
                print(f"\n=== POST {i}/{len(rendered)} ===")
                print(f"# candidate_id: {ch.get('candidate_id')}")
                print(text)
            return

        x = XClient.from_env()

        # 任意：ここで auth 健全性チェック（失敗したら原因が出る）
        try:
            me = x.get_me()
            uid = (me.get("data") or {}).get("id")
            print(f"[ok] authenticated as user_id={uid}")
        except Exception as e:
            print(f"[warn] could not verify /2/users/me: {e}")

        for i, (ch, text) in enumerate(rendered, 1):
            try:
                tweet_id = x.create_tweet(text)
            except XAPIError as e:
                # 403でも detail/reason を含めて出る
                print(f"[fail] could not post candidate_id={ch.get('candidate_id')} : {e}")
                # ここで止める（権限/プラン問題なら継続しても全滅するため）
                raise

            append_jsonl(
                posted_state,
                {
                    "candidate_id": ch.get("candidate_id"),
                    "posted_at": datetime.utcnow().isoformat(),
                    "x_post_id": tweet_id,
                    "source_type": ch.get("source_type"),
                },
            )
            print(f"[ok] posted {i}/{len(rendered)} candidate_id={ch.get('candidate_id')} x_post_id={tweet_id}")

            if i < len(rendered) and interval_seconds > 0:
                print(f"[wait] sleeping {interval_seconds}s before next post...")
                time.sleep(interval_seconds)

    finally:
        release_lock(lock_fd, lock_path)


if __name__ == "__main__":
    main()
