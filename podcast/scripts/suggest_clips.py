#!/usr/bin/env python3
"""切り抜き候補（セグメント参考）を生成する（CLIP_PLAN C-12）。

凍結版の現在の字幕ユニット（clip_<KEY>.json）を LLM に渡し、切り抜きに向く区間の
候補 5〜10 件（見出し + 範囲）をもらう。返った範囲はユニット境界にスナップし、
全文はユニットから合成する（LLM の引用は使わない）。結果は
generated/clip_<KEY>_suggestions.json に保存する（参考情報。再生成で丸ごと差し替え）。

API キーは環境変数 OPENAI_API_KEY、無ければ podcast/.env から読む（単一 .env 集約の規約）。
モデルは CLIP_SUGGEST_MODEL（既定 gpt-5.5。suggest.py の gpt-5.5-pro より軽い用途のため）。

usage: python scripts/suggest_clips.py <ID> --key <CLIPKEY>
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
from render import load_conf

MODEL = os.environ.get("CLIP_SUGGEST_MODEL", "gpt-5.5")
EFFORT = os.environ.get("CLIP_SUGGEST_EFFORT", "medium")


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


def snap(units, start, end):
    """LLM の範囲をユニット境界へ寄せる。開始 = start に最も近いユニット開始、
    終了 = end に最も近いユニット終了。"""
    starts = [float(u["s"]) for u in units]
    ends = [float(u["e"]) for u in units]
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
    units = [u for u in (cur.get("units") or []) if (u.get("t") or "").strip()]
    if not units:
        sys.exit("[clipsug] 字幕ユニットがありません")

    if not load_api_key():
        sys.exit("[clipsug] OPENAI_API_KEY がありません（podcast/.env に置いてください）")
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("[clipsug] openai SDK がありません。README の .venv-openai を作ってください"
                 "（pip install -r requirements-openai.txt）")

    lines = [f"[{float(u['s']):.1f}-{float(u['e']):.1f}] {u['t']}" for u in units]
    prompt = (HERE / "prompts" / "prompt_clips.txt").read_text(encoding="utf-8")
    client = OpenAI(timeout=float(os.environ.get("PODCAST_API_TIMEOUT", "900")), max_retries=1)
    print(f"[clipsug] {MODEL}(effort={EFFORT}) を1回呼び出します（ユニット {len(units)} 行）")
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
            s, e = snap(units, sg["start_sec"], sg["end_sec"])
        except (KeyError, TypeError, ValueError):
            continue
        if e - s < 5:
            continue
        text = "".join(u["t"] for u in units if float(u["e"]) > s and float(u["s"]) < e)
        out.append({"title": str(sg.get("title") or "").strip() or "（無題）",
                    "s": round(s, 3), "e": round(e, 3), "text": text})
    if not out:
        sys.exit("[clipsug] 有効な候補が得られませんでした")

    dst = pathlib.Path(idpaths.save(str(base), f"clip_{args.key}_suggestions.json"))
    tmp = dst.with_name(dst.name + ".part")
    tmp.write_text(json.dumps(
        {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
         "model": MODEL, "suggestions": out}, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(dst)   # 差し替えは原子的に（再生成中に古い候補が壊れて見えない）
    print(f"[clipsug] done. 候補 {len(out)} 件 -> {dst}")


if __name__ == "__main__":
    main()
