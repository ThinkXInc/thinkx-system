#!/usr/bin/env python3
"""切り抜き動画を1本合成する（CLIP_PLAN C-8・C-17 改定）。

構成要素は 音声 + 字幕 + タイトル（全編表示） + 背景動画（ループ）。
C-17: 凍結音源は使わない。音声は**元音源**から、切り抜き区間 −（1次編集の drops）−
（「間を詰める」の drops）の keep を抽出・連結する。字幕は修正オーバーレイ適用済みの
単語トークン（元音源時刻）を、出力時間へ再配置してから clip_styles.json の caption
パラメータで字幕行にまとめる。スタイルはコードに埋め込まない（原文 L53）。

usage: python scripts/make_clip_video.py <ID> --key <KEY> --seg <N> --sizes <WxH>[,<WxH>…] \
           [--out <出力パス>] [--export]
  N は切り抜きの時系列順の番号（0始まり）。--export は contents/clip/<KEY>/ へ
  ファイル名規則（タイトル_長さ_規格）で書き出す（C-9）。
"""
import os
import sys
import json
import struct
import pathlib
import argparse
import tempfile
import subprocess

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts"))
import idpaths
import transcript_edits
from render import find_media, keep_ranges, load_conf, safe_name
from export_audio import aac_encoder

FONTS_DIR = HERE / "assets" / "fonts"
BG_DIR = HERE / "assets" / "clip_backgrounds"


def ffmpeg_with_subtitles():
    """libass(subtitles フィルタ)が有効な ffmpeg を選ぶ。
    Homebrew の ffmpeg は libass 無効ビルドのことがある(2026-09-28 実測: 8.1.2 に無く、
    /usr/local/bin/ffmpeg 7.1 にはある)。CLIP_FFMPEG 環境変数で明示指定もできる。"""
    cands = [os.environ.get("CLIP_FFMPEG"), "ffmpeg",
             "/usr/local/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg"]
    for c in cands:
        if not c:
            continue
        try:
            out = subprocess.run([c, "-hide_banner", "-filters"],
                                 capture_output=True, text=True).stdout
        except OSError:
            continue
        if " subtitles " in out:
            return c
    sys.exit("[clipvid] libass 対応の ffmpeg が見つかりません"
             "（brew の ffmpeg が libass 無効の場合があります。CLIP_FFMPEG で指定可）")


def font_family_name(path):
    """フォントファイルの family 名（name テーブル）。libass はファイル名でなく
    family 名で探すため、ファイルから直接読む（依存を増やさない）。ttc は先頭フォント。"""
    data = pathlib.Path(path).read_bytes()

    def u32(o):
        return struct.unpack(">I", data[o:o + 4])[0]

    def u16(o):
        return struct.unpack(">H", data[o:o + 2])[0]

    off = u32(12) if data[:4] == b"ttcf" else 0
    num_tables = u16(off + 4)
    rec = off + 12
    name_off = None
    for _ in range(num_tables):
        if data[rec:rec + 4] == b"name":
            name_off = u32(rec + 8)
            break
        rec += 16
    if name_off is None:
        return None
    count = u16(name_off + 2)
    str_off = name_off + u16(name_off + 4)
    best = None          # family (nameID 16 > 1)
    best_sub = None      # subfamily (nameID 17 > 2)
    r = name_off + 6
    for _ in range(count):
        pid, _eid, _lid, nid = u16(r), u16(r + 2), u16(r + 4), u16(r + 6)
        ln, so = u16(r + 8), u16(r + 10)
        r += 12
        if nid not in (16, 1, 17, 2):
            continue
        raw = data[str_off + so:str_off + so + ln]
        s = raw.decode("mac_roman", "ignore") if pid == 1 else raw.decode("utf-16-be", "ignore")
        if not s:
            continue
        if nid in (16, 1):
            score = (0 if nid == 16 else 1, 0 if pid == 3 else 1)
            if best is None or score < best[0]:
                best = (score, s)
        else:
            score = (0 if nid == 17 else 1, 0 if pid == 3 else 1)
            if best_sub is None or score < best_sub[0]:
                best_sub = (score, s)
    if best is None:
        return None
    fam = best[1]
    # 同一 family の別ウェイト(ヒラギノ W3/W6/W8 等)を区別できるよう、
    # Regular/Bold 以外のサブファミリーは family に含める(原文 L130 のバリエーション対応)
    sub = best_sub[1] if best_sub else ""
    if sub and sub.lower() not in ("regular", "bold", "italic", "bold italic") \
            and sub not in fam:
        fam = f"{fam} {sub}"
    return fam


def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def resolve_style(cfg, sub_style):
    """スタイル調整パネル(原文 L126)の実効値。web-server/main.py の
    resolve_clip_style と同じ既定を共有する(片方を変えたら両方直す)。"""
    legacy_font = cfg.get("font") or ""
    base = {
        "sub": {"color": ["#ffffff"], "outline": ["#000000"], "outline_w": 8,
                "shadow_w": 3, "shadow_color": "#000000", "font": legacy_font,
                "bold": True,
                "size_pct": float(cfg.get("size_pct") or sub_style.get("font_size_pct") or 8.3),
                "width_pct": 86, "x_pct": 50, "y_pct": 62,
                "bg_on": False, "bg_color": "#000000", "bg_pad": 24, "bg_pad_v": 8,
                "bg_radius": 16, "bg_alpha": 70},
        "title": {"color": ["#ffffff"], "outline": ["#000000"], "outline_w": 6,
                  "shadow_w": 2, "shadow_color": "#000000", "font": legacy_font,
                  "bold": True, "size_pct": 6.4, "width_pct": 84, "x_pct": 50, "y_pct": 20,
                  "bg_on": False, "bg_color": "#000000", "bg_pad": 24, "bg_pad_v": 8,
                  "bg_radius": 16, "bg_alpha": 70},
    }
    st = cfg.get("style") or {}
    out = {}
    for k, d in base.items():
        merged = dict(d)
        for kk, vv in (st.get(k) or {}).items():
            if vv is not None:
                merged[kk] = vv
        out[k] = merged
    return out


def _hex_rgb(h):
    h = (h or "#ffffff").lstrip("#")
    if len(h) != 6:
        h = "ffffff"
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def ass_colour(h):
    """#rrggbb → スタイル行用 &H00BBGGRR。"""
    r, g, b = _hex_rgb(h)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def _lerp_hex(a, b, t):
    ra, ga, ba = _hex_rgb(a)
    rb, gb, bb = _hex_rgb(b)
    return (round(ra + (rb - ra) * t), round(ga + (gb - ga) * t),
            round(ba + (bb - ba) * t))


def styled_text(text, max_chars, fill, outline):
    """折り返し + グラデーション。libass はグラデーションを持たないため、
    2色指定のときは1文字ずつ色を補間した \\c / \\3c タグで焼く(原文 L126)。"""
    if max_chars < 4:
        max_chars = 4
    lines = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    if len(fill) < 2 and len(outline) < 2:
        return r"\N".join(lines)
    total = max(1, sum(len(ln) for ln in lines) - 1)
    out_lines, idx = [], 0
    for ln in lines:
        buf = ""
        for ch in ln:
            t = idx / total
            tags = ""
            if len(fill) > 1:
                r, g, b = _lerp_hex(fill[0], fill[1], t)
                tags += rf"\c&H{b:02X}{g:02X}{r:02X}&"
            if len(outline) > 1:
                r, g, b = _lerp_hex(outline[0], outline[1], t)
                tags += rf"\3c&H{b:02X}{g:02X}{r:02X}&"
            buf += "{" + tags + "}" + ch
            idx += 1
        out_lines.append(buf)
    return r"\N".join(out_lines)


def token_in_keeps(st, en, keeps):
    """中点が keep 内、または端をまたぐ語は重なり 0.2 秒以上（main.py と同じ規則。
    「重なり 0.2 秒以上」だけだと 0.2 秒未満の短い語が keep 内でも全部落ちる）。"""
    mid = (st + en) / 2
    if any(ka <= mid < kb for ka, kb in keeps):
        return True
    return sum(max(0.0, min(en, kb) - max(st, ka)) for ka, kb in keeps) >= 0.2


def clip_tokens(base, geometry, keeps):
    """keep に属する修正済みトークン（元音源時刻）。"""
    tsegments, _st = transcript_edits.corrected_segments(str(base))
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
            if not token_in_keeps(st, en, keeps):
                continue
            out.append({"s": st, "e": en, "t": tok})
    out.sort(key=lambda w: w["s"])
    return out


def build_captions(tokens, keeps, styles):
    """トークンを出力時間へ再配置し、字幕行（caption）にまとめる（C-17。
    表示のまとめ方はデータでなくスタイルの問題なのでここで行う）。"""
    cap = styles.get("caption") or {}
    max_chars = int(cap.get("max_chars") or 16)
    gap_sec = float(cap.get("gap_sec") or 0.6)
    min_show = float(cap.get("min_show_sec") or 0.8)
    kmap, acc = [], 0.0
    for ka, kb in keeps:
        kmap.append((ka, kb, acc))
        acc += kb - ka
    dur = acc

    def remap(t):
        for ka, kb, off in kmap:
            if t <= kb:
                return off + min(max(t, ka), kb) - ka
        return dur

    caps, cur = [], None
    for w in tokens:
        a, b = remap(w["s"]), remap(w["e"])
        if cur is not None and (a - cur["b"] >= gap_sec or len(cur["text"]) >= max_chars):
            caps.append(cur)
            cur = None
        if cur is None:
            cur = {"a": a, "b": max(b, a), "text": w["t"],
                   "toks": [{"s": w["s"], "t": w["t"]}]}
        else:
            cur["text"] += w["t"]
            cur["b"] = max(cur["b"], b)
            cur["toks"].append({"s": w["s"], "t": w["t"]})
        if cur["text"] and cur["text"][-1] in "。．！？!?":
            caps.append(cur)
            cur = None
    if cur is not None:
        caps.append(cur)
    # 短すぎる表示は読めない。次の字幕開始までの範囲で最低表示時間を確保する
    for i, c in enumerate(caps):
        if c["b"] - c["a"] < min_show:
            limit = caps[i + 1]["a"] if i + 1 < len(caps) else dur
            c["b"] = min(max(c["b"], c["a"] + min_show), max(limit, c["a"]))
    return caps, dur


def emit_caption_text(toks, max_chars_n, base, effects, fxmap, w, px_base):
    """キャプション本文を1文字ずつ組み立てる(原文 L134)。
    各トークンは effects([{a,b,style}] 元音源時刻)に当たれば名前付きスタイルの
    上書き(サイズ・色/グラデ・縁・影・フォント・太字・ポップ)を受ける。
    折り返しは基準サイズの文字数で行う(部分的な拡大による幅増は近似のまま)。"""
    scale = w / 1080.0

    def styles_of(tok_s):
        """このトークンに重なる全スタイル名。アニメとスタイルは共存し(原文 L142)、
        広い範囲(=まとまり全体のアニメ)を先に、狭い範囲(=部分スタイル)を後に重ねる。"""
        ms = [e for e in effects
              if float(e["a"]) - 0.005 <= tok_s <= float(e["b"]) + 0.005
              and str(e.get("style")) in fxmap]
        ms.sort(key=lambda e: -(float(e["b"]) - float(e["a"])))
        return tuple(str(e["style"]) for e in ms)

    # 文字列に展開(文字ごとのスタイル名の組)
    chars = []
    for tk in toks:
        nm = styles_of(float(tk["s"]))
        for ch in tk["t"]:
            chars.append((ch, nm))
    # 折り返し位置(基準文字数)
    if max_chars_n < 4:
        max_chars_n = 4
    total = max(1, len(chars) - 1)

    def props_of(nms):
        if not nms:
            return base
        q = dict(base)
        for nm in nms:
            q.update({k: v for k, v in fxmap.get(nm, {}).items() if v is not None})
        return q

    def run_tags(q, nm, run_len_info=None):
        px = max(1, int(round(w * float(q["size_pct"]) / 100)))
        ow = round(float(q.get("outline_w") or 0) * scale, 1)
        sw = round(float(q.get("shadow_w") or 0) * scale, 1)
        fam = q.get("_family") or ""
        t = rf"\fs{px}\bord{ow}\shad{sw}"
        t += r"\b1" if q.get("bold") else r"\b0"
        if fam:
            t += rf"\fn{fam}"
        sr, sg, sb = _hex_rgb(q.get("shadow_color") or "#000000")
        t += rf"\4c&H{sb:02X}{sg:02X}{sr:02X}&"
        oc = (q.get("outline") or ["#000000"])
        if len(oc) < 2:
            r, g, b = _hex_rgb(oc[0])
            t += rf"\3c&H{b:02X}{g:02X}{r:02X}&"
        fc = (q.get("color") or ["#ffffff"])
        if len(fc) < 2:
            r, g, b = _hex_rgb(fc[0])
            t += rf"\c&H{b:02X}{g:02X}{r:02X}&"
        # ポップ(拡大アニメ)。スライドはまとまり単位のみ(イベント移動のため)
        if nm and q.get("anim") == "pop":
            ms = int(float(q.get("anim_dur") or 0.25) * 1000)
            t += rf"\fscx20\fscy20\t(0,{ms},\fscx100\fscy100)"
        else:
            t += r"\fscx100\fscy100"
        return "{" + t + "}"

    out = []
    cur_nm = object()   # 強制的に先頭でタグを吐く
    col = 0
    gi = 0
    for ch, nm in chars:
        if col >= max_chars_n:
            out.append(r"\N")
            col = 0
        if nm != cur_nm:
            q = props_of(nm)
            out.append(run_tags(q, nm))
            cur_nm = nm
            cur_q = q
        # グラデーション(スタイルのスコープ内で全体に補間)
        fc = (cur_q.get("color") or ["#ffffff"])
        oc = (cur_q.get("outline") or ["#000000"])
        tags = ""
        if len(fc) > 1:
            r, g, b = _lerp_hex(fc[0], fc[1], gi / total)
            tags += rf"\c&H{b:02X}{g:02X}{r:02X}&"
        if len(oc) > 1:
            r, g, b = _lerp_hex(oc[0], oc[1], gi / total)
            tags += rf"\3c&H{b:02X}{g:02X}{r:02X}&"
        if tags:
            out.append("{" + tags + "}")
        out.append(ch)
        col += 1
        gi += 1
    return "".join(out)


def build_ass(w, h, stl, cfg, captions, dur, families, effects=None, fxmap=None):
    """stl = resolve_style() の実効値(タイトル/字幕とも 色[1-2]・縁[1-2]・縁太・影・影色・
    フォント・太字・サイズ(幅%)・位置(x/y %))。families = {"sub": family, "title": family}。
    縁太・影は 1080 幅基準の px 指定を実寸へスケールする。位置は中央アンカー(\\an5)。"""
    scale = w / 1080.0

    def px_of(d):
        return max(1, int(round(w * float(d["size_pct"]) / 100)))

    def style_line(name, d, fam):
        px = px_of(d)
        bold = -1 if d.get("bold") else 0
        ow = round(float(d.get("outline_w") or 0) * scale, 1)
        sw = round(float(d.get("shadow_w") or 0) * scale, 1)
        return (f"Style: {name},{fam},{px},{ass_colour((d.get('color') or ['#ffffff'])[0])},"
                f"&H000000FF,{ass_colour((d.get('outline') or ['#000000'])[0])},"
                f"{ass_colour(d.get('shadow_color') or '#000000')},"
                f"{bold},0,0,0,100,100,0,0,1,{ow},{sw},5,20,20,20,1")

    def max_chars(d):
        # テキストボックスの幅はスタイルの width_pct(画面幅に対する%)が決める(原文 L130)
        return max(2, int((w * float(d.get("width_pct") or 86) / 100) // px_of(d)))

    def pos_tag(d):
        x = int(round(w * float(d.get("x_pct") or 50) / 100))
        y = int(round(h * float(d.get("y_pct") or 50) / 100))
        return rf"{{\an5\pos({x},{y})}}"

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {w}",
        f"PlayResY: {h}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        style_line("Sub", stl["sub"], families["sub"]),
        style_line("Title", stl["title"], families["title"]),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    def bg_event(d, style_name, text, t0, t1):
        """背景の角丸矩形(原文 L132/L133)。ASS に角丸ボックスが無いので描画コマンド
        (\\p1 のベジェ角丸矩形)をテキストの背面レイヤーに焼く。半透明は \\1a で指定。
        文字幅は 全角=1em・半角=0.55em の見積り(プレビューは CSS なので数 px の近似差は許容)"""
        if not d.get("bg_on"):
            return None
        px = max(1, int(round(w * float(d["size_pct"]) / 100)))
        mc0 = max_chars(d)
        tl = [text[i:i + mc0] for i in range(0, len(text), mc0)] or [""]

        def _est(ln):
            return sum(px if ord(ch) > 0xFF else px * 0.55 for ch in ln)

        pad = float(d.get("bg_pad") or 0) * scale
        pad_v = float(d.get("bg_pad_v") or 0) * scale
        rad = float(d.get("bg_radius") or 0) * scale
        bw = max(_est(ln) for ln in tl) + 2 * pad
        bh = len(tl) * px * 1.18 + 2 * pad_v
        rad = max(0.0, min(rad, bw / 2, bh / 2))
        cx = w * float(d.get("x_pct") or 50) / 100
        cy = h * float(d.get("y_pct") or 50) / 100
        x0, y0 = cx - bw / 2, cy - bh / 2

        def f(v):
            return f"{v:.1f}"

        r_ = rad
        path = (f"m {f(r_)} 0 l {f(bw - r_)} 0 "
                f"b {f(bw)} 0 {f(bw)} 0 {f(bw)} {f(r_)} "
                f"l {f(bw)} {f(bh - r_)} "
                f"b {f(bw)} {f(bh)} {f(bw)} {f(bh)} {f(bw - r_)} {f(bh)} "
                f"l {f(r_)} {f(bh)} "
                f"b 0 {f(bh)} 0 {f(bh)} 0 {f(bh - r_)} "
                f"l 0 {f(r_)} "
                f"b 0 0 0 0 {f(r_)} 0")
        br, bgg, bb = _hex_rgb(d.get("bg_color") or "#000000")
        op = d.get("bg_alpha")
        op = 100.0 if op is None else float(op)
        aa = max(0, min(255, int(round(255 * (1 - op / 100)))))
        return (f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},{style_name},,0,0,0,,"
                rf"{{\an7\pos({x0:.1f},{y0:.1f})\p1\bord0\shad0"
                rf"\1c&H{bb:02X}{bgg:02X}{br:02X}&\1a&H{aa:02X}&}}{path}{{\p0}}")

    title = (cfg.get("title") or "").strip()
    if title:
        d = stl["title"]
        ev = bg_event(d, "Title", title, 0, dur)
        if ev:
            lines.append(ev)
        txt = styled_text(title, max_chars(d), d.get("color") or [], d.get("outline") or [])
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(dur)},Title,,0,0,0,,"
                     f"{pos_tag(d)}{txt}")
    d = stl["sub"]
    mc = max_chars(d)
    effects = effects or []
    fxmap = fxmap or {}
    base_sub = dict(d, _family=families["sub"])
    px_sub = px_of(d)

    def whole_anim(toks):
        """slide_up のスタイルがまとまりの全トークンを覆っていれば返す(原文 L142。
        内側に部分スタイルが重なっていてもスライドは生きる)。"""
        for e in effects:
            pr = fxmap.get(str(e.get("style"))) or {}
            if pr.get("anim") != "slide_up":
                continue
            if all(float(e["a"]) - 0.005 <= float(tk["s"]) <= float(e["b"]) + 0.005
                   for tk in toks):
                return pr
        return None

    for c in captions:
        if not c["text"].strip():
            continue
        ev = bg_event(d, "Sub", c["text"], c["a"], min(c["b"], dur))
        if ev:
            lines.append(ev)
        toks = c.get("toks") or [{"s": -1, "t": c["text"]}]
        if effects and fxmap:
            txt = emit_caption_text(toks, mc, base_sub, effects, fxmap, w, px_sub)
        else:
            txt = styled_text(c["text"], mc, d.get("color") or [], d.get("outline") or [])
        wa = whole_anim(toks) if (effects and fxmap) else None
        if wa:
            # 下からスライドして現れる(まとまり単位。原文 L134)
            ms = int(float(wa.get("anim_dur") or 0.3) * 1000)
            x = int(round(w * float(d.get("x_pct") or 50) / 100))
            y = int(round(h * float(d.get("y_pct") or 50) / 100))
            dy = int(round(h * 0.045))
            head = rf"{{\an5\move({x},{y + dy},{x},{y},0,{ms})}}"
        else:
            head = pos_tag(d)
        lines.append(f"Dialogue: 1,{ass_time(c['a'])},{ass_time(min(c['b'], dur))},Sub,,0,0,0,,"
                     f"{head}{txt}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--key", required=True)
    ap.add_argument("--seg", type=int, required=True, help="切り抜きの時系列順の番号（0始まり）")
    ap.add_argument("--sizes", required=True,
                    help="例 1080x1920,1080x1080（clip_styles.json の key をカンマ区切り）")
    ap.add_argument("--out", default=None, help="出力パス（単一サイズのときのみ）")
    ap.add_argument("--export", action="store_true",
                    help="contents/clip/<KEY>/ にファイル名規則（タイトル_長さ_規格）で書き出す（C-9）")
    args = ap.parse_args()
    size_keys = [s for s in args.sizes.split(",") if s]
    if args.out and (len(size_keys) != 1 or args.export):
        sys.exit("[clipvid] --out は単一サイズ・--export なしのときだけ指定できます")

    paths = load_conf("config/paths.conf")
    root = os.environ.get("SITE_DATA_DIR") or paths.get("PODCAST_ROOT") or str(HERE / "data")
    base = pathlib.Path(root) / args.id

    styles = json.loads((HERE / "config" / "clip_styles.json").read_text(encoding="utf-8"))
    cur = json.loads(pathlib.Path(idpaths.find(str(base), f"clip_{args.key}.json"))
                     .read_text(encoding="utf-8"))
    if "geometry" not in cur:
        sys.exit("[clipvid] この版ファイルに geometry がありません（旧形式）")
    g = cur["geometry"]
    g_drops = [tuple(map(float, d)) for d in g.get("drops") or []]
    clips = sorted(cur.get("clips") or [], key=lambda c: (c[0], c[1]))
    if not (0 <= args.seg < len(clips)):
        sys.exit(f"[clipvid] 切り抜き {args.seg} がありません（{len(clips)}本）")
    row = clips[args.seg]
    cs, ce = float(row[0]), float(row[1])
    row_drops = [tuple(map(float, d)) for d in (row[2] if len(row) > 2 else [])]
    # keep = 切り抜き −（1次編集の drops）−（詰めた間）。音声・字幕・尺の唯一の根拠（C-17）
    keeps = keep_ranges(cs, ce, g_drops + row_drops)
    if not keeps:
        sys.exit("[clipvid] 有効区間がありません")
    dur = sum(b - a for a, b in keeps)
    cfg = (cur.get("video") or {}).get("clips", {}).get(str(args.seg)) or {}

    media = find_media(base, args.id, None)
    if not media or not media.exists():
        sys.exit(f"[clipvid] メディアが見つかりません（{base}）")
    wav = media.with_suffix(".wav")
    if wav.exists():
        media = wav

    bg_name = cfg.get("background") or ""
    bg = BG_DIR / bg_name
    if not bg_name or not bg.is_file():
        sys.exit(f"[clipvid] 背景動画がありません: {bg}")

    stl = resolve_style(cfg, (styles.get("subtitle_styles") or [{}])[0])
    families = {}
    for el in ("sub", "title"):
        fn = stl[el].get("font") or ""
        fp2 = FONTS_DIR / fn
        if not fn or not fp2.is_file():
            sys.exit(f"[clipvid] フォントがありません({el}): {fp2}")
        families[el] = font_family_name(fp2) or pathlib.Path(fn).stem

    captions, _dur2 = build_captions(clip_tokens(base, g, keeps), keeps, styles)

    # 名前付きエフェクトスタイル(原文 L134)。定義は data/effect_styles.json(全エピソード共通)
    effects = cur.get("effects") or []
    fxmap = {}
    fx_path = pathlib.Path(root) / "effect_styles.json"
    if effects and fx_path.is_file():
        try:
            for st_ in (json.loads(fx_path.read_text(encoding="utf-8")).get("styles") or []):
                props = dict(st_.get("props") or {})
                fn_ = props.get("font")
                if fn_ and (FONTS_DIR / fn_).is_file():
                    props["_family"] = font_family_name(FONTS_DIR / fn_)
                fxmap[str(st_.get("name"))] = props
        except (OSError, json.JSONDecodeError):
            pass

    ff = ffmpeg_with_subtitles()
    gen = pathlib.Path(idpaths.gen_dir(str(base)))

    # 音声。単一区間なら元音源を -ss/-t で直接切り、複数区間なら抽出して無劣化連結
    audio_in = media
    audio_seek = ["-ss", f"{keeps[0][0]:.3f}", "-t", f"{dur:.3f}"]
    concat_wav = None
    if len(keeps) > 1:
        concat_wav = gen / f"clip_{args.key}_{args.seg}_audio.part.wav"
        with tempfile.TemporaryDirectory(dir=str(gen)) as td:
            tdp = pathlib.Path(td)
            listf = tdp / "list.txt"
            with open(listf, "w") as lf:
                for i, (ka, kb) in enumerate(keeps):
                    part = tdp / f"p{i:04d}.wav"
                    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                                    "-ss", f"{ka:.3f}", "-to", f"{kb:.3f}", "-i", str(media),
                                    "-c:a", "pcm_s16le", str(part)], check=True)
                    lf.write(f"file '{part.name}'\n")
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "concat", "-safe", "0", "-i", str(listf),
                            "-c", "copy", str(concat_wav)], check=True)
        audio_in = concat_wav
        audio_seek = []

    for size_key in size_keys:
        size = next((s for s in styles.get("sizes", []) if s["key"] == size_key), None)
        if size is None:
            sys.exit(f"[clipvid] 未知のサイズ規格: {size_key}")
        w, h = int(size["w"]), int(size["h"])
        if args.export:
            # ファイル名はタイトル・長さ・サイズ規格から（原文 L71）
            title = (cfg.get("title") or f"クリップ{args.seg + 1}").strip()
            name = f"{safe_name(title)}_{int(dur // 60)}m{int(dur % 60):02d}s_{size_key}.mp4"
            out = base / "contents" / "clip" / args.key / name
        elif args.out:
            out = pathlib.Path(args.out)
        else:
            out = pathlib.Path(
                idpaths.save(str(base), f"clip_{args.key}_preview_{args.seg}_{size_key}.mp4"))
        out.parent.mkdir(parents=True, exist_ok=True)

        ass_path = gen / f"clip_{args.key}_{args.seg}_{size_key}.ass"
        ass_path.write_text(
            build_ass(w, h, stl, cfg, captions, dur, families,
                      effects=effects, fxmap=fxmap),
            encoding="utf-8")

        # フィルタ内のパス引用を避けるため、ass はファイル名だけ渡して cwd を generated/ にする
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps=30,"
              f"subtitles=filename={ass_path.name}:fontsdir='{FONTS_DIR}'")
        tmp = out.with_name(out.name + ".part.mp4")
        cmd = ([ff, "-hide_banner", "-loglevel", "error", "-y",
                "-stream_loop", "-1", "-i", str(bg)]
               + audio_seek + ["-i", str(audio_in),
               "-map", "0:v", "-map", "1:a", "-t", f"{dur:.3f}",
               "-vf", vf,
               "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k",
               str(tmp)])
        subprocess.run(cmd, cwd=str(gen), check=True)

        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=noprint_wrappers=1:nokey=1", str(tmp)],
                               capture_output=True, text=True)
        actual = float(probe.stdout.strip() or 0)
        if abs(actual - dur) > 2.0:
            tmp.unlink(missing_ok=True)
            sys.exit(f"[clipvid] 出力尺が不一致（指定{dur:.1f}s / 実際{actual:.1f}s）")
        tmp.replace(out)
        print(f"[clipvid] done {size_key} / {dur:.1f}s / 字幕フォント {families['sub']} -> {out}",
              flush=True)

    if concat_wav is not None:
        concat_wav.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
