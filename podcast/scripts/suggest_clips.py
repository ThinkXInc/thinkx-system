#!/usr/bin/env python3
"""切り抜き候補（セグメント参考）を生成する（CLIP_PLAN C-12・C-17 改定）。

対象の版（clip_<KEY>.json の geometry）の有効区間にある単語トークン
（文字起こし+修正オーバーレイ適用済み・元音源の絶対時刻）を LLM に渡し、
切り抜きに向く区間の候補 5〜10 件（見出し3案 + 範囲）をもらう。
返った範囲はトークン境界にスナップし、全文はトークンから合成する（LLM の引用は使わない）。
結果は generated/clip_<KEY>_suggestions.json に保存（元音源時刻。再生成で丸ごと差し替え）。

API キーは環境変数 OPENAI_API_KEY、無ければ podcast/.env から読む（単一 .env 集約の規約）。
モデルは CLIP_SUGGEST_MODEL（既定 gpt-5.5）。

usage: python scripts/suggest_clips.py <ID> --key <KEY>
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

MODEL = os.environ.get("CLIP_SUGGEST_MODEL", "gpt-5.5")
EFFORT = os.environ.get("CLIP_SUGGEST_EFFORT", "medium")
LINE_GAP = 0.8        # プロンプト行のまとまり（表示粒度ではなく入力の圧縮用）
LINE_PUNCT = "。．！？!?"


def load_api_key():
    if os.environ.get("OPENAI_API_KEY"):
        return True
    try:
        for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
                return True
    except OSError:
        pass
    return bool(os.environ.get("OPENAI_API_KEY"))


def extract_json_block(text):
    m = re.findall(r"```json\s*(.*?)```", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m[-1])
    except json.JSONDecodeError:
        return None


def tokens_in_geometry(base, geometry):
    """geometry の keep に属する修正済みトークン（元音源時刻）。
    判定は「中点が keep 内 or 重なり 0.2 秒以上」（main.py と同じ規則。
    重なりだけだと 0.2 秒未満の短い語が keep 内でも全部落ちる）。"""
    tsegments, _st = transcript_edits.corrected_segments(str(base))
    keeps = keep_ranges(float(geometry["start_sec"]), float(geometry["end_sec"]),
                        [tuple(map(float, d)) for d in geometry.get("drops") or []])
    out = []
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
            out.append({"s": st, "e": en, "t": tok})
    out.sort(key=lambda w: w["s"])
    return out


def prompt_lines(tokens):
    """トークンをフレーズ行にまとめる（LLM 入力の圧縮用。データの粒度は変えない）。"""
    lines, cur = [], None
    for w in tokens:
        if cur is not None and w["s"] - cur["e"] >= LINE_GAP:
            lines.append(cur)
            cur = None
        if cur is None:
            cur = {"s": w["s"], "e": w["e"], "t": w["t"]}
        else:
            cur["t"] += w["t"]
            cur["e"] = w["e"]
        if cur["t"] and cur["t"][-1] in LINE_PUNCT:
            lines.append(cur)
            cur = None
    if cur is not None:
        lines.append(cur)
    return lines


def snap(tokens, start, end):
    """LLM の範囲をトークン境界へ寄せる。"""
    starts = [w["s"] for w in tokens]
    ends = [w["e"] for w in tokens]
    s = min(starts, key=lambda v: abs(v - float(start)))
    e = min(ends, key=lambda v: abs(v - float(end)))
    return s, e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--key", required=True)
    args = ap.parse_args()

    paths = load_conf("config/paths.conf")
    root = os.environ.get("SITE_DATA_DIR") or paths.get("PODCAST_ROOT") or str(HERE / "data")
    base = pathlib.Path(root) / args.id

    cur = json.loads(pathlib.Path(idpaths.find(str(base), f"clip_{args.key}.json"))
                     .read_text(encoding="utf-8"))
    if "geometry" not in cur:
        sys.exit("[clipsug] この版ファイルに geometry がありません（旧形式）")
    tokens = tokens_in_geometry(base, cur["geometry"])
    if not tokens:
        sys.exit("[clipsug] 対象区間にトークンがありません")

    if not load_api_key():
        sys.exit("[clipsug] OPENAI_API_KEY がありません（podcast/.env に置いてください）")
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("[clipsug] openai SDK がありません。README の .venv-openai を作ってください"
                 "（pip install -r requirements-openai.txt）")

    lines = [f"[{ln['s']:.1f}-{ln['e']:.1f}] {ln['t']}" for ln in prompt_lines(tokens)]
    prompt = (HERE / "prompts" / "prompt_clips.txt").read_text(encoding="utf-8")
    client = OpenAI(timeout=float(os.environ.get("PODCAST_API_TIMEOUT", "900")), max_retries=1)
    print(f"[clipsug] {MODEL}(effort={EFFORT}) を1回呼び出します（{len(lines)} 行）")
    resp = client.responses.create(
        model=MODEL,
        instructions="指示に厳密に従い、最後に必ず指定の JSON ブロックを付けてください。",
        input=f"{prompt}\n\n=== 文字起こしここから ===\n" + "\n".join(lines) + "\n=== ここまで ===",
        reasoning={"effort": EFFORT},
    )
    data = extract_json_block(resp.output_text)
    if not data or not isinstance(data.get("suggestions"), list):
        sys.exit("[clipsug] 応答末尾の JSON ブロックが見つからない/壊れています")

    out = []
    for sg in data["suggestions"][:10]:
        try:
            s, e = snap(tokens, sg["start_sec"], sg["end_sec"])
        except (KeyError, TypeError, ValueError):
            continue
        if e - s < 5:
            continue
        text = "".join(w["t"] for w in tokens if w["e"] > s and w["s"] < e)
        # 見出し候補は3つ(「AはBである」形式優先。原文 L100)。旧形式 title 単数も受ける
        titles = [str(t).strip() for t in (sg.get("titles") or []) if str(t).strip()][:3]
        if not titles:
            titles = [str(sg.get("title") or "").strip() or "（無題）"]
        out.append({"titles": titles, "title": titles[0],
                    "s": round(s, 3), "e": round(e, 3), "text": text})
    if not out:
        sys.exit("[clipsug] 有効な候補が得られませんでした")

    # ハイライト(名言的・格言的・キャッチーな一言。原文 L122)。候補とは独立
    hls = []
    for h in (data.get("highlights") or [])[:20]:
        try:
            s, e = snap(tokens, h["start_sec"], h["end_sec"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (0.5 <= e - s <= 20):
            continue
        text = "".join(w["t"] for w in tokens if w["e"] > s and w["s"] < e)
        hls.append({"s": round(s, 3), "e": round(e, 3), "text": text})

    dst = pathlib.Path(idpaths.save(str(base), f"clip_{args.key}_suggestions.json"))
    tmp = dst.with_name(dst.name + ".part")
    tmp.write_text(json.dumps(
        {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
         "model": MODEL, "time_base": "source",
         "suggestions": out, "highlights": hls},
        ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(dst)   # 差し替えは原子的に
    print(f"[clipsug] done. 候補 {len(out)} 件 / ハイライト {len(hls)} 件 -> {dst}")


if __name__ == "__main__":
    main()
