from __future__ import annotations
import argparse
import json
from datetime import datetime
from pathlib import Path
import re

from ..config import load_config
from ..utils.io import ensure_dir, append_jsonl, iter_jsonl, load_jsonl_set
from ..utils.llm import LLMClient
from ..utils.text import split_batches, sha1_hex
from ..utils.dedup import is_duplicate

ID_RE = re.compile(r"\[\[id:(.+?)\]\]")
SCORE_RE = re.compile(r"\{\{(\d)\}\}")


def find_tweet_js_files(archive_dir: Path) -> list[Path]:
    # 典型: data/tweets.js, data/tweets-part0.js, ... などを広く拾う
    patterns = ["tweets.js", "tweet.js", "tweets-part*.js", "tweets*.js"]
    files = []
    for p in patterns:
        files.extend(archive_dir.rglob(p))
    return sorted(set(files))


def parse_tweets_from_js(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="ignore").strip()
    # window.YTD.tweets.part0 = [...]
    if "=" in raw and raw.lstrip().startswith("window."):
        raw = raw.split("=", 1)[1].strip()
    # 末尾の ; を除去
    raw = raw.rstrip(";")
    data = json.loads(raw)

    tweets = []
    # フォーマットは {"tweet": {...}} の配列が多い
    for item in data:
        tw = item.get("tweet") if isinstance(item, dict) else None
        if not isinstance(tw, dict):
            continue
        tid = tw.get("id") or ""
        text = tw.get("full_text") or tw.get("text") or ""
        created_at = tw.get("created_at") or ""
        if tid and text:
            tweets.append({"id": tid, "text": text, "created_at": created_at})
    return tweets


def parse_llm_output(s: str) -> list[tuple[str, str, int]]:
    """
    ---
    [[id:...]]
    text
    {{3}}
    ---
    """
    chunks = [c.strip() for c in s.split("---") if c.strip()]
    out = []
    for c in chunks:
        mid = ID_RE.search(c)
        ms = SCORE_RE.search(c)
        if not mid or not ms:
            continue
        tid = mid.group(1).strip()
        score = int(ms.group(1))
        text = ID_RE.sub("", c)
        text = SCORE_RE.sub("", text).strip()
        if not text:
            continue
        out.append((tid, text, score))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")
    ap.add_argument("--force", action="store_true", help="markerがあっても実行")
    ap.add_argument("--batch-size", type=int, default=25)
    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir

    xcfg = cfg.settings.get("x", {}) or {}
    archive_dir = Path(xcfg.get("archive_dir", "data/x_archive"))

    state_dir = data_dir / "state"
    cand_dir = data_dir / "candidates"
    markers = state_dir / "markers"
    ensure_dir(state_dir)
    ensure_dir(cand_dir)
    ensure_dir(markers)

    marker = markers / "x_archive_import_done.txt"
    if marker.exists() and not args.force:
        print(f"[skip] archive already imported: {marker}")
        return

    processed_ids = load_jsonl_set(state_dir / "processed_tweet_ids.jsonl", "tweet_id")
    out_jsonl = cand_dir / "xposts.jsonl"

    # 既存テキスト（重複防止用）
    existing_texts = [obj.get("post_text", "") for obj in iter_jsonl(out_jsonl)]

    files = find_tweet_js_files(archive_dir)
    if not files:
        raise SystemExit(f"tweet js files not found under: {archive_dir}")

    all_tweets = []
    for f in files:
        all_tweets.extend(parse_tweets_from_js(f))

    # 未処理のみ
    tweets = [t for t in all_tweets if t["id"] not in processed_ids]
    print(f"[info] archive tweets total={len(all_tweets)} new={len(tweets)}")

    llm_cfg = cfg.settings.get("llm", {}) or {}
    client = LLMClient(
        provider=llm_cfg.get("provider", "openai"),
        model=llm_cfg.get("model", "gpt-4o-mini"),
        temperature=float(llm_cfg.get("temperature", 0.2)),
    )
    prompt_base = cfg.prompts["xpost_filter_prompt"]
    sim_th = float((cfg.settings.get("dedup", {}) or {}).get("similarity_threshold", 0.5))

    now = datetime.utcnow().isoformat()

    batches = [tweets[i:i+args.batch_size] for i in range(0, len(tweets), args.batch_size)]
    kept = 0

    for bi, batch in enumerate(batches, 1):
        # LLMへID付きで渡す
        lines = []
        for t in batch:
            lines.append(f"[[id:{t['id']}]]\n{t['text']}")
        user_prompt = prompt_base + "\n\n[投稿リスト]\n" + "\n\n-----\n\n".join(lines)

        try:
            res = client.chat(user=user_prompt, system="あなたはSNS運用のプロです。")
        except Exception as e:
            print(f"[fail llm] batch {bi}/{len(batches)} : {e}")
            continue

        items = parse_llm_output(res)

        # batch内のtweet_idは全て「処理済み」として記録（再処理防止）
        for t in batch:
            append_jsonl(state_dir / "processed_tweet_ids.jsonl", {"tweet_id": t["id"], "processed_at": now, "source": "archive"})

        for tid, text, score in items:
            if score <= 0:
                continue

            # 重複チェック（50%一致以上）
            if is_duplicate(text, existing_texts, threshold=sim_th):
                continue

            existing_texts.append(text)
            candidate_id = sha1_hex(f"x|{tid}|{score}")
            append_jsonl(out_jsonl, {
                "candidate_id": candidate_id,
                "source_type": "x",
                "tweet_id": tid,
                "created_at": now,
                "published_at": "",  # 元ツイ日時が必要なら追加で持てる
                "text": text,
                "score": score,
                #"post_text": text,  # 仕様：そのまま再投稿（付加情報なし）
            })
            kept += 1

        print(f"[ok] archive batch {bi}/{len(batches)} kept +{len(items)} (raw)")

    marker.write_text(f"done_at={now}\n", encoding="utf-8")
    print(f"[done] kept={kept} marker={marker}")


if __name__ == "__main__":
    main()
