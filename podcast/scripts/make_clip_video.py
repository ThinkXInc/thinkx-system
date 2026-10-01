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


def wrap_lines(text, max_chars):
    """CJK 前提の単純折り返し（文字数ベース）。必要なだけ行を増やす。
    以前は行数上限の超過分を最終行へ詰め込んでいたため、その行が画面幅を超えて
    端が切れていた（原文 L125 のバグの増幅要因）。"""
    if max_chars < 4:
        max_chars = 4
    return r"\N".join(text[i:i + max_chars] for i in range(0, len(text), max_chars))


def pct_of(spec, size_key, default):
    """{"1080x1920": 62, "default": 66} 形式の解決。"""
    if isinstance(spec, dict):
        return float(spec.get(size_key, spec.get("default", default)))
    if spec is None:
        return float(default)
    return float(spec)


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
            cur = {"a": a, "b": max(b, a), "text": w["t"]}
        else:
            cur["text"] += w["t"]
            cur["b"] = max(cur["b"], b)
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


def build_ass(w, h, size_key, styles, cfg, captions, dur, fontname):
    sub = (styles.get("subtitle_styles") or [{}])[0]
    tstyles = {t.get("key"): t for t in (styles.get("title_styles") or [])}
    tstyle = tstyles.get(cfg.get("title_style")) or (styles.get("title_styles") or [{}])[0]

    # フォントサイズは**幅**に対する%で px 化する。高さ基準だと同じ指定でも
    # 1:1 と 9:16 で物理サイズが変わり、幅が同じ 1080 なのに縦長だけ端が切れる
    # （原文 L125 のバグ。実測: 10.1 指定で 1:1=109px / 9:16=194px になっていた）。
    # 表示位置(center_y/top_y)は従来どおり高さ%のまま
    sub_pct = float(cfg.get("size_pct") or sub.get("font_size_pct") or 8.3)
    sub_px = int(round(w * sub_pct / 100))
    sub_outline = max(1, int(round(sub_px * float(sub.get("outline_pct") or 0.35) / 4)))
    sub_shadow = int(round(sub_px * float(sub.get("shadow_pct") or 0.15) / 4))
    sub_cy = int(round(h * pct_of(sub.get("center_y_pct"), size_key, 65) / 100))
    sub_mx = float(sub.get("margin_x_pct") or 7)
    sub_max_chars = max(4, int((w * (1 - 2 * sub_mx / 100)) // sub_px))

    ttl_px = int(round(w * float(tstyle.get("font_size_pct") or 6.4) / 100))
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
        txt = wrap_lines(title, ttl_max_chars)
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(dur)},Title,,0,0,0,,"
                     f"{{\\an8\\pos({w // 2},{ttl_y})}}{txt}")
    for c in captions:
        if not c["text"].strip():
            continue
        txt = wrap_lines(c["text"], sub_max_chars)
        lines.append(f"Dialogue: 0,{ass_time(c['a'])},{ass_time(min(c['b'], dur))},Sub,,0,0,0,,"
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

    font_name = cfg.get("font") or ""
    font_path = FONTS_DIR / font_name
    if not font_name or not font_path.is_file():
        sys.exit(f"[clipvid] フォントがありません: {font_path}")
    family = font_family_name(font_path) or pathlib.Path(font_name).stem

    captions, _dur2 = build_captions(clip_tokens(base, g, keeps), keeps, styles)

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
            build_ass(w, h, size_key, styles, cfg, captions, dur, family),
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
        print(f"[clipvid] done {size_key} / {dur:.1f}s / 字幕フォント {family} -> {out}",
              flush=True)

    if concat_wav is not None:
        concat_wav.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
