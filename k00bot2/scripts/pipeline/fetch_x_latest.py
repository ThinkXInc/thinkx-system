from __future__ import annotations
import argparse
from datetime import datetime
import re

from ..config import load_config
from ..utils.io import ensure_dir, append_jsonl, iter_jsonl, load_jsonl_set
from ..utils.llm import LLMClient
from ..utils.x_api import XClient
from ..utils.dedup import is_duplicate
from ..utils.text import sha1_hex

ID_RE = re.compile(r"\[\[id:(.+?)\]\]")
SCORE_RE = re.compile(r"\{\{(\d)\}\}")


def parse_llm_output(s: str) -> list[tuple[str, str, int]]:
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
        if text:
            out.append((tid, text, score))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")
    ap.add_argument("--max-results", type=int, default=100)
    ap.add_argument("--batch-size", type=int, default=25)
    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir
    ensure_dir(data_dir / "state")
    ensure_dir(data_dir / "candidates")

    xcfg = cfg.settings.get("x", {}) or {}
    username = xcfg["username"]
    exclude = xcfg.get("exclude", ["retweets", "replies"])
    max_results = int(xcfg.get("latest_max_results", args.max_results))

    client_x = XClient.from_env()
    user_id = client_x.get_user_id(username)

    import time
    from scripts.utils.x_api import XAPIError

    def _maybe_sleep_and_retry(e: XAPIError, max_wait_seconds: int = 20 * 60) -> bool:
        """
        429 のとき、x-rate-limit-reset が近ければ少し待って再実行できるようにする。
        max_wait_seconds を超えるなら待たずにスキップ。
        """
        reset = (e.headers or {}).get("x-rate-limit-reset")
        if not reset:
            return False
        try:
            reset_epoch = int(float(reset))
        except Exception:
            return False

        wait = int(reset_epoch - time.time()) + 5
        if wait <= 0:
            return True
        if wait > max_wait_seconds:
            return False

        print(f"[rate-limit] 429 hit. sleeping ~{wait}s until reset...")
        time.sleep(wait)
        return True


    try:
        resp = client_x.get_user_tweets(user_id, max_results=max_results, exclude=exclude)
    except XAPIError as e:
        # 429: Freeだと /2/users/:id/tweets が 1req/15min など厳しいので普通に起きる :contentReference[oaicite:5]{index=5}
        if e.status_code == 429:
            print(f"[warn] X rate limited (429): {e}")
            # reset が近ければ1回だけ待ってリトライ
            if _maybe_sleep_and_retry(e):
                resp = client_x.get_user_tweets(user_id, max_results=max_results, exclude=exclude)
            else:
                # monthly.sh を止めない（set -e 対策）
                print("[skip] fetch_x_latest skipped due to rate limit. try again later.")
                return

        # 403 client-not-enrolled 等も monthly を止めたくないならここでスキップ可能
        elif e.status_code == 403 and (e.payload or {}).get("reason") == "client-not-enrolled":
            print(f"[skip] X API not enrolled for v2 reads: {e}")
            return
        else:
            raise

    # resp は dict(=APIレスポンス全体) の想定。list が返ってくる実装にも耐えるようにする。
    if isinstance(resp, dict):
        # エラー形式のレスポンスを先に弾く
        if resp.get("errors"):
            raise RuntimeError(f"X API returned errors: {resp.get('errors')}")
        tweets = resp.get("data") or []
    elif isinstance(resp, list):
        tweets = resp
    else:
        raise RuntimeError(f"Unexpected response type from get_user_tweets: {type(resp)}")

    if not isinstance(tweets, list):
        raise RuntimeError(f"Unexpected tweets container type: {type(tweets)}")

    for t in tweets:
        if not isinstance(t, dict):
            continue  # 念のため
        tid = t.get("id", "")
        # 以下、既存処理のまま（text抽出など）


    state_dir = data_dir / "state"
    processed_ids = load_jsonl_set(state_dir / "processed_tweet_ids.jsonl", "tweet_id")

    # 既存候補の重複チェック対象
    out_jsonl = data_dir / "candidates" / "xposts.jsonl"
    existing_texts = [obj.get("post_text", "") for obj in iter_jsonl(out_jsonl)]

    new_tweets = []
    for t in tweets:
        tid = t.get("id", "")
        text = t.get("text", "")
        if not tid or not text:
            continue
        if tid in processed_ids:
            continue
        new_tweets.append({"id": tid, "text": text, "created_at": t.get("created_at", "")})

    print(f"[info] latest fetched={len(tweets)} new={len(new_tweets)}")

    if not new_tweets:
        return

    llm_cfg = cfg.settings.get("llm", {}) or {}
    client_llm = LLMClient(
        provider=llm_cfg.get("provider", "openai"),
        model=llm_cfg.get("model", "gpt-4o-mini"),
        temperature=float(llm_cfg.get("temperature", 0.2)),
    )
    prompt_base = cfg.prompts["xpost_filter_prompt"]
    sim_th = float((cfg.settings.get("dedup", {}) or {}).get("similarity_threshold", 0.5))
    now = datetime.utcnow().isoformat()

    batches = [new_tweets[i:i+args.batch_size] for i in range(0, len(new_tweets), args.batch_size)]
    kept = 0

    for bi, batch in enumerate(batches, 1):
        lines = [f"[[id:{t['id']}]]\n{t['text']}" for t in batch]
        user_prompt = prompt_base + "\n\n[投稿リスト]\n" + "\n\n-----\n\n".join(lines)

        try:
            res = client_llm.chat(user=user_prompt, system="あなたはSNS運用のプロです。")
        except Exception as e:
            print(f"[fail llm] batch {bi}/{len(batches)} : {e}")
            continue

        items = parse_llm_output(res)

        # 取得したtweet_idはすべて処理済みにする（再処理防止）
        for t in batch:
            append_jsonl(state_dir / "processed_tweet_ids.jsonl", {"tweet_id": t["id"], "processed_at": now, "source": "latest"})

        for tid, text, score in items:
            if score <= 0:
                continue
            if is_duplicate(text, existing_texts, threshold=sim_th):
                continue
            existing_texts.append(text)
            candidate_id = sha1_hex(f"x|{tid}|{score}")
            append_jsonl(out_jsonl, {
                "candidate_id": candidate_id,
                "source_type": "x",
                "tweet_id": tid,
                "created_at": now,
                "published_at": "",
                "text": text,
                "score": score,
                #"post_text": text,
            })
            kept += 1

        print(f"[ok] latest batch {bi}/{len(batches)} items={len(items)}")

    print(f"[done] kept={kept}")


if __name__ == "__main__":
    main()
