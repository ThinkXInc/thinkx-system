#!/usr/bin/env python3
"""文字起こし修正のオーバーレイ（CLIP_PLAN C-16）。

transcript.json（機械出力・generated・git外）は不変のまま、人の修正だけを
edit/transcript_edits.json（git追跡）に差分で持ち、読むときに重ねる。

ファイル形式:
  { "transcript_sha256": "…transcript.json の指紋…",
    "edits": [
      {"op": "replace", "s": 923.41, "orig": "てくる", "text": "出てくる"},
      {"op": "delete",  "s": 951.02, "orig": "ゴゴゴ"},
      {"op": "insert",  "t": 980.5,  "text": "（笑）", "dur": 1.5}
    ] }

- キーはトークンの開始秒（replace/delete）。orig は誤適用防止の照合用。
- 指紋が現在の transcript.json と一致しないとき（再文字起こし後）は適用しない。
  黙って時刻ズレのまま重ねる事故を構造的に防ぐ。
"""
import os
import json
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _sys
_sys.path.insert(0, HERE)
import idpaths

EDITS_NAME = "transcript_edits.json"
KEY_EPS = 0.005   # 開始秒キーの照合誤差


def fingerprint(base):
    """transcript.json の sha256。無ければ None。"""
    p = idpaths.find(base, "transcript.json")
    if not os.path.isfile(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(base):
    """edits ファイルを読む。無ければ空の形。"""
    p = idpaths.find(base, EDITS_NAME)
    if not os.path.isfile(p):
        return {"transcript_sha256": None, "edits": []}
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"transcript_sha256": None, "edits": []}
    d.setdefault("edits", [])
    return d


def status(base, edits_doc=None):
    """'ok'（適用可）/ 'stale'（指紋不一致・適用停止）/ 'none'（修正なし）。"""
    d = edits_doc if edits_doc is not None else load(base)
    if not d.get("edits"):
        return "none"
    return "ok" if d.get("transcript_sha256") == fingerprint(base) else "stale"


def apply_to_segments(tsegments, edits_doc):
    """transcript.json の segments（words 付き）へ修正を重ねた**コピー**を返す。
    元の構造は変更しない。返り値の word には "edited": True が付く（表示用）。"""
    edits = (edits_doc or {}).get("edits") or []
    if not edits:
        return tsegments
    by_key = {}
    inserts = []
    for e in edits:
        if e.get("op") in ("replace", "delete"):
            by_key[round(float(e["s"]), 3)] = e
        elif e.get("op") == "insert":
            inserts.append(e)

    def match(ws):
        k = round(float(ws), 3)
        if k in by_key:
            return by_key[k]
        for dk in (k - 0.001, k + 0.001):   # 丸め差の救済
            if dk in by_key:
                return by_key[dk]
        return None

    out = []
    for seg in tsegments:
        words = []
        for w in (seg.get("words") or []):
            st = w.get("start")
            e = match(st) if st is not None else None
            if e is None:
                words.append(w)
                continue
            orig = (w.get("word") or "").strip()
            if e.get("orig") is not None and e["orig"] != orig:
                words.append(w)          # 照合不一致 → 触らない（安全側）
                continue
            w2 = dict(w)
            w2["edited"] = True
            w2["orig_word"] = orig   # 再修正時の照合キー(機械出力の原文)を失わない
            if e["op"] == "delete":
                # 位置は空白プレースホルダとして残す(原文 L112)。表示側はクリックで
                # 再入力でき、出力側(字幕・候補・全文)は空テキストとして自然に除外される
                w2["word"] = ""
                w2["deleted"] = True
            else:
                w2["word"] = e.get("text") or ""
            words.append(w2)
        seg2 = dict(seg)
        seg2["words"] = words
        out.append(seg2)

    # 挿入。時刻が入るセグメント（無ければ最後）へ、開始秒順の位置に差し込む
    for e in sorted(inserts, key=lambda x: float(x["t"])):
        t = float(e["t"])
        dur = float(e.get("dur") or 1.5)
        nw = {"word": e.get("text") or "", "start": round(t, 3),
              "end": round(t + dur, 3), "edited": True, "inserted": True}
        host = None
        for seg2 in out:
            ws = seg2.get("words") or []
            if ws and float(ws[0].get("start") or 0) <= t <= float(ws[-1].get("end") or 0):
                host = seg2
                break
        if host is None and out:
            host = min(out, key=lambda s: abs(
                float((s.get("words") or [{}])[0].get("start") or 0) - t))
        if host is None:
            continue
        ws = host.setdefault("words", [])
        pos = next((i for i, w in enumerate(ws)
                    if float(w.get("start") or 0) > t), len(ws))
        ws.insert(pos, nw)
    return out


def corrected_segments(base):
    """(修正済み tsegments, status) を返す。stale のときは修正を適用しない。"""
    try:
        with open(idpaths.find(base, "transcript.json"), encoding="utf-8") as f:
            tsegments = json.load(f).get("segments", [])
    except (OSError, json.JSONDecodeError):
        return [], "none"
    d = load(base)
    st = status(base, d)
    if st != "ok":
        return tsegments, st
    return apply_to_segments(tsegments, d), st


def upsert(base, op):
    """1件の修正を取り込み、正規化した edits ドキュメントを返す（書き込みは呼び出し側）。
    - 同じキーへの replace は上書き（差分をためない）
    - delete は同キーの replace を置き換える
    - 元に戻す系: replace の text が orig と同じなら、そのキーの修正を取り消す
    - insert は t をキーに上書き。text が空なら取り消し
    失敗理由の文字列 or (doc, None) を返す。"""
    fp = fingerprint(base)
    if fp is None:
        return None, "no_transcript"
    d = load(base)
    if d.get("edits") and d.get("transcript_sha256") != fp:
        return None, "stale_transcript"
    d["transcript_sha256"] = fp
    kind = op.get("op")
    if kind in ("replace", "delete"):
        try:
            key = round(float(op["s"]), 3)
        except (TypeError, ValueError, KeyError):
            return None, "bad_key"
        d["edits"] = [e for e in d["edits"]
                      if not (e.get("op") in ("replace", "delete")
                              and abs(float(e.get("s", -1)) - key) < KEY_EPS)]
        text = (op.get("text") or "").strip() if kind == "replace" else None
        if kind == "replace" and text == (op.get("orig") or "").strip():
            pass   # 原文に戻した = 修正の取り消し（何も追加しない）
        else:
            rec = {"op": kind, "s": key, "orig": (op.get("orig") or "").strip()}
            if kind == "replace":
                if not text:
                    rec = {"op": "delete", "s": key, "orig": rec["orig"]}
                else:
                    rec["text"] = text
            d["edits"].append(rec)
    elif kind == "insert":
        try:
            t = round(float(op["t"]), 3)
        except (TypeError, ValueError, KeyError):
            return None, "bad_key"
        d["edits"] = [e for e in d["edits"]
                      if not (e.get("op") == "insert"
                              and abs(float(e.get("t", -1)) - t) < KEY_EPS)]
        text = (op.get("text") or "").strip()
        if text:
            d["edits"].append({"op": "insert", "t": t, "text": text,
                               "dur": round(float(op.get("dur") or 1.5), 3)})
    else:
        return None, "bad_op"
    d["edits"].sort(key=lambda e: float(e.get("s", e.get("t", 0))))
    return d, None
