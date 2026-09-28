#!/usr/bin/env python3
"""切り抜き動画を1本合成する（CLIP_PLAN C-8）。

構成要素は 音声（凍結音源の該当区間）+ 字幕（修正済みユニット）+ タイトル（全編表示）+
背景動画（ループ）。スタイルは config/clip_styles.json（C-7）をデータとして読む。
プログラムが全要素を結合して1本にする（原文 L36-37。After Effects を使わない）。

usage: python scripts/make_clip_video.py <ID> --key <CLIPKEY> --seg <N> --sizes <WxH>[,<WxH>…] \
           [--out <出力パス>]
  N は切り抜きの時系列順の番号（0始まり）。--out は単一サイズのときだけ指定できる。
  省略時は generated/clip_<KEY>_preview_<N>_<WxH>.mp4 に書く。
"""
import os
import sys
import json
import struct
import pathlib
import argparse
import subprocess

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts"))
import idpaths
from render import load_conf, safe_name

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
    best = None
    r = name_off + 6
    for _ in range(count):
        pid, _eid, _lid, nid = u16(r), u16(r + 2), u16(r + 4), u16(r + 6)
        ln, so = u16(r + 8), u16(r + 10)
        r += 12
        if nid not in (16, 1):
            continue
        raw = data[str_off + so:str_off + so + ln]
        s = raw.decode("mac_roman", "ignore") if pid == 1 else raw.decode("utf-16-be", "ignore")
        if not s:
            continue
        score = (0 if nid == 16 else 1, 0 if pid == 3 else 1)
        if best is None or score < best[0]:
            best = (score, s)
    return best[1] if best else None


def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def wrap_lines(text, max_chars, max_lines):
    """CJK 前提の単純折り返し（文字数ベース）。超過分も捨てずに最終行へ入れる。"""
    if max_chars < 4:
        max_chars = 4
    lines = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + ["".join(lines[max_lines - 1:])]
    return r"\N".join(lines)


def pct_of(spec, size_key, default):
    """{"1080x1920": 62, "default": 66} 形式の解決。"""
    if isinstance(spec, dict):
        return float(spec.get(size_key, spec.get("default", default)))
    if spec is None:
        return float(default)
    return float(spec)


def build_ass(w, h, size_key, styles, cfg, units, cs, ce, fontname):
    sub = (styles.get("subtitle_styles") or [{}])[0]
    tstyles = {t.get("key"): t for t in (styles.get("title_styles") or [])}
    tstyle = tstyles.get(cfg.get("title_style")) or (styles.get("title_styles") or [{}])[0]
    dur = ce - cs

    sub_pct = float(cfg.get("size_pct") or sub.get("font_size_pct") or 4.7)
    sub_px = int(round(h * sub_pct / 100))
    sub_outline = max(1, int(round(sub_px * float(sub.get("outline_pct") or 0.35) / 4)))
    sub_shadow = int(round(sub_px * float(sub.get("shadow_pct") or 0.15) / 4))
    sub_cy = int(round(h * pct_of(sub.get("center_y_pct"), size_key, 65) / 100))
    sub_mx = float(sub.get("margin_x_pct") or 7)
    sub_max_chars = max(4, int((w * (1 - 2 * sub_mx / 100)) // sub_px))

    ttl_px = int(round(h * float(tstyle.get("font_size_pct") or 3.6) / 100))
    ttl_outline = max(1, int(round(ttl_px * float(tstyle.get("outline_pct") or 0.25) / 4)))
    ttl_shadow = int(round(ttl_px * float(tstyle.get("shadow_pct") or 0.1) / 4))
    ttl_y = int(round(h * pct_of(tstyle.get("top_y_pct"), size_key, 12) / 100))
    ttl_mx = float(tstyle.get("margin_x_pct") or 8)
    ttl_max_chars = max(4, int((w * (1 - 2 * ttl_mx / 100)) // ttl_px))

    def style_line(name, px, st, outline, shadow):
        bold = -1 if st.get("bold", True) else 0
        return (f"Style: {name},{fontname},{px},{st.get('primary_colour', '&H00FFFFFF')},"
                f"&H000000FF,{st.get('outline_colour', '&H00000000')},&H80000000,"
                f"{bold},0,0,0,100,100,0,0,1,{outline},{shadow},5,20,20,20,1")

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
        style_line("Sub", sub_px, sub, sub_outline, sub_shadow),
        style_line("Title", ttl_px, tstyle, ttl_outline, ttl_shadow),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    title = (cfg.get("title") or "").strip()
    if title:
        txt = wrap_lines(title, ttl_max_chars, int(tstyle.get("max_lines") or 3))
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(dur)},Title,,0,0,0,,"
                     f"{{\\an8\\pos({w // 2},{ttl_y})}}{txt}")
    for u in units:
        us, ue = float(u["s"]), float(u["e"])
        if ue <= cs or us >= ce:
            continue
        text = (u.get("t") or "").strip()
        if not text:
            continue
        a, b = max(0.0, us - cs), min(dur, ue - cs)
        # 短すぎる表示は読めないので最低 0.8 秒は出す（次の字幕開始までに収める）
        if b - a < 0.8:
            b = min(dur, a + 0.8)
        txt = wrap_lines(text, sub_max_chars, int(sub.get("max_lines") or 2))
        lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Sub,,0,0,0,,"
                     f"{{\\an5\\pos({w // 2},{sub_cy})}}{txt}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--key", required=True)
    ap.add_argument("--seg", type=int, required=True, help="切り抜きの時系列順の番号（0始まり）")
    ap.add_argument("--sizes", required=True,
                    help="例 1080x1920,1080x1080（clip_styles.json の key をカンマ区切り）")
    ap.add_argument("--out", default=None, help="出力パス（単一サイズのときのみ）")
    args = ap.parse_args()
    size_keys = [s for s in args.sizes.split(",") if s]
    if args.out and len(size_keys) != 1:
        sys.exit("[clipvid] --out は単一サイズのときだけ指定できます")

    paths = load_conf("config/paths.conf")
    root = os.environ.get("SITE_DATA_DIR") or paths.get("PODCAST_ROOT") or str(HERE / "data")
    base = pathlib.Path(root) / args.id

    styles = json.loads((HERE / "config" / "clip_styles.json").read_text(encoding="utf-8"))
    cur = json.loads(pathlib.Path(idpaths.find(str(base), f"clip_{args.key}.json"))
                     .read_text(encoding="utf-8"))
    clips = sorted(cur.get("clips") or [])
    if not (0 <= args.seg < len(clips)):
        sys.exit(f"[clipvid] 切り抜き {args.seg} がありません（{len(clips)}本）")
    cs, ce = float(clips[args.seg][0]), float(clips[args.seg][1])
    dur = ce - cs
    cfg = (cur.get("video") or {}).get("clips", {}).get(str(args.seg)) or {}

    audio = pathlib.Path(idpaths.find(str(base), f"clip_{args.key}_source.m4a"))
    if not audio.is_file():
        sys.exit("[clipvid] 凍結音源がありません（切り抜き編集画面で生成されます）")

    bg_name = cfg.get("background") or ""
    bg = BG_DIR / bg_name
    if not bg_name or not bg.is_file():
        sys.exit(f"[clipvid] 背景動画がありません: {bg}")

    font_name = cfg.get("font") or ""
    font_path = FONTS_DIR / font_name
    if not font_name or not font_path.is_file():
        sys.exit(f"[clipvid] フォントがありません: {font_path}")
    family = font_family_name(font_path) or pathlib.Path(font_name).stem

    ff = ffmpeg_with_subtitles()
    gen = pathlib.Path(idpaths.gen_dir(str(base)))
    for size_key in size_keys:
        size = next((s for s in styles.get("sizes", []) if s["key"] == size_key), None)
        if size is None:
            sys.exit(f"[clipvid] 未知のサイズ規格: {size_key}")
        w, h = int(size["w"]), int(size["h"])
        out = pathlib.Path(args.out) if args.out else pathlib.Path(
            idpaths.save(str(base), f"clip_{args.key}_preview_{args.seg}_{size_key}.mp4"))
        out.parent.mkdir(parents=True, exist_ok=True)

        ass_path = gen / f"clip_{args.key}_{args.seg}_{size_key}.ass"
        ass_path.write_text(
            build_ass(w, h, size_key, styles, cfg, cur.get("units") or [], cs, ce, family),
            encoding="utf-8")

        # フィルタ内のパス引用を避けるため、ass はファイル名だけ渡して cwd を generated/ にする
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps=30,"
              f"subtitles=filename={ass_path.name}:fontsdir='{FONTS_DIR}'")
        tmp = out.with_name(out.name + ".part.mp4")
        cmd = [ff, "-hide_banner", "-loglevel", "error", "-y",
               "-stream_loop", "-1", "-i", str(bg),
               "-ss", f"{cs:.3f}", "-t", f"{dur:.3f}", "-i", str(audio),
               "-map", "0:v", "-map", "1:a", "-t", f"{dur:.3f}",
               "-vf", vf,
               "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k",
               str(tmp)]
        subprocess.run(cmd, cwd=str(gen), check=True)

        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=noprint_wrappers=1:nokey=1", str(tmp)],
                               capture_output=True, text=True)
        actual = float(probe.stdout.strip() or 0)
        if abs(actual - dur) > 2.0:
            tmp.unlink(missing_ok=True)
            sys.exit(f"[clipvid] 出力尺が不一致（指定{dur:.1f}s / 実際{actual:.1f}s）")
        tmp.replace(out)
        print(f"[clipvid] done {size_key} / {dur:.1f}s / 字幕フォント {family} -> {out}",
              flush=True)


if __name__ == "__main__":
    main()
