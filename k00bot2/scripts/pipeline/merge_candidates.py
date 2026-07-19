from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

from ..config import load_config
from ..utils.io import ensure_dir, iter_jsonl, append_jsonl
from ..utils.dedup import is_duplicate


def load_with_priority(path: Path, priority: int) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    for obj in iter_jsonl(path):
        obj["_merge_priority"] = priority
        out.append(obj)
    return out


def core_text(obj: Dict[str, Any]) -> str:
    """
    dedup判定用の中核テキスト。
    - article: text（引用）
    - x: text（原文）※古いデータは post_text しか無い場合があるのでfallback
    """
    t = (obj.get("text") or "").strip()
    if t:
        return t
    return (obj.get("post_text") or "").strip()


def normalize_output(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    candidates.jsonl には post_text を持たせない（テンプレは投稿直前に適用するため）。
    ただし古いデータ互換のため、text が空で post_text がある場合は text に移す。
    """
    o = dict(obj)

    if not (o.get("text") or "").strip():
        pt = (o.get("post_text") or "").strip()
        if pt:
            o["text"] = pt

    # キャッシュ系は落とす
    o.pop("post_text", None)
    o.pop("text_hash", None)
    o.pop("_merge_priority", None)

    return o


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")
    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir
    cand_dir = data_dir / "candidates"
    ensure_dir(cand_dir)

    # manual候補を使っていないならファイルは存在しなくてOK
    manual_path = cand_dir / "manual_candidates.jsonl"
    article_path = cand_dir / "article_candidates.jsonl"
    xposts_path = cand_dir / "xposts.jsonl"
    out_path = cand_dir / "candidates.jsonl"

    if out_path.exists():
        out_path.unlink()

    # priority: manual(0) > article(1) > x(2)
    merged: List[Dict[str, Any]] = []
    merged += load_with_priority(manual_path, 0)
    merged += load_with_priority(article_path, 1)
    merged += load_with_priority(xposts_path, 2)

    def sort_key(o: Dict[str, Any]) -> Tuple[int, int]:
        pri = int(o.get("_merge_priority", 9))
        score = int(o.get("score", 0))
        return (pri, -score)

    merged.sort(key=sort_key)

    kept_texts: List[str] = []
    kept = 0

    for obj in merged:
        t = core_text(obj)
        if not t:
            continue

        # 中核テキストで重複判定（テンプレ変更に引きずられない）
        if is_duplicate(t, kept_texts, threshold=0.8):
            continue
        kept_texts.append(t)

        out_obj = normalize_output(obj)
        append_jsonl(out_path, out_obj)
        kept += 1

    print(f"[ok] merged -> {out_path} kept={kept} total_in={len(merged)}")


if __name__ == "__main__":
    main()
