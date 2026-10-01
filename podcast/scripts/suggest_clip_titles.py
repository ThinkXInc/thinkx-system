#!/usr/bin/env python3
"""切り抜き1本分のタイトル候補を3つ生成する（CLIP_PLAN・原文 L123）。

動画作成画面のセグメントは切り抜き編集で改めて切られたものなので、セグメント参考の
候補タイトルとは別に、**このセグメントのテキスト**から見出しを作る価値がある。
結果は generated/clip_<KEY>_titles_<N>.json に保存（再生成で丸ごと差し替え）。

usage: python scripts/suggest_clip_titles.py <ID> --key <KEY> --seg <N>
"""
import os
import re
import sys
import json
import pathlib
import argparse
import datetime

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts"))
import idpaths
import transcript_edits
from render import load_conf, keep_ranges
from suggest_clips import load_api_key, extract_json_block

MODEL = os.environ.get("CLIP_SUGGEST_MODEL", "gpt-5.5")
EFFORT = os.environ.get("CLIP_SUGGEST_EFFORT", "medium")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--key", required=True)
    ap.add_argument("--seg", type=int, required=True)
    args = ap.parse_args()

    paths = load_conf("config/paths.conf")
    root = os.environ.get("SITE_DATA_DIR") or paths.get("PODCAST_ROOT") or str(HERE / "data")
    base = pathlib.Path(root) / args.id

    cur = json.loads(pathlib.Path(idpaths.find(str(base), f"clip_{args.key}.json"))
                     .read_text(encoding="utf-8"))
    if "geometry" not in cur:
        sys.exit("[cliptitle] この版ファイルに geometry がありません（旧形式）")
    g = cur["geometry"]
    clips = sorted(cur.get("clips") or [], key=lambda c: (c[0], c[1]))
    if not (0 <= args.seg < len(clips)):
        sys.exit(f"[cliptitle] 切り抜き {args.seg} がありません（{len(clips)}本）")
    row = clips[args.seg]
    cs, ce = float(row[0]), float(row[1])
    drops = ([tuple(map(float, d)) for d in g.get("drops") or []]
             + [tuple(map(float, d)) for d in (row[2] if len(row) > 2 else [])])
    keeps = keep_ranges(cs, ce, drops)
    if not keeps:
        sys.exit("[cliptitle] 有効区間がありません")

    tsegments, _st = transcript_edits.corrected_segments(str(base))
    parts = []
    for tseg in tsegments:
        for w in (tseg.get("words") or []):
            st, en = w.get("start"), w.get("end")
            if st is None or en is None:
                continue
            st, en = float(st), float(en)
            tok = (w.get("word") or "").strip()
            if not tok:
                continue
            mid = (st + en) / 2
            if not (any(ka <= mid < kb for ka, kb in keeps)
                    or sum(max(0.0, min(en, kb) - max(st, ka)) for ka, kb in keeps) >= 0.2):
                continue
            parts.append(tok)
    text = "".join(parts)
    if not text.strip():
        sys.exit("[cliptitle] このセグメントにテキストがありません")

    if not load_api_key():
        sys.exit("[cliptitle] OPENAI_API_KEY がありません（podcast/.env に置いてください）")
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("[cliptitle] openai SDK がありません（README の .venv-openai を作ってください）")

    prompt = (HERE / "prompts" / "prompt_clip_titles.txt").read_text(encoding="utf-8")
    client = OpenAI(timeout=float(os.environ.get("PODCAST_API_TIMEOUT", "600")), max_retries=1)
    print(f"[cliptitle] {MODEL}(effort={EFFORT}) を1回呼び出します（{len(text)}文字）")
    resp = client.responses.create(
        model=MODEL,
        instructions="指示に厳密に従い、最後に必ず指定の JSON ブロックを付けてください。",
        input=f"{prompt}\n\n=== 文字起こしここから ===\n{text}\n=== ここまで ===",
        reasoning={"effort": EFFORT},
    )
    data = extract_json_block(resp.output_text)
    titles = [str(t).strip() for t in ((data or {}).get("titles") or []) if str(t).strip()][:3]
    if not titles:
        sys.exit("[cliptitle] 応答からタイトル候補を取り出せませんでした")

    dst = pathlib.Path(idpaths.save(str(base), f"clip_{args.key}_titles_{args.seg}.json"))
    tmp = dst.with_name(dst.name + ".part")
    tmp.write_text(json.dumps(
        {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
         "model": MODEL, "seg": args.seg, "range": [cs, ce], "titles": titles},
        ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(dst)
    print(f"[cliptitle] done. {titles} -> {dst}")


if __name__ == "__main__":
    main()
