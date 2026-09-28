#!/usr/bin/env python3
"""凍結音源を書き出す（CLIP_PLAN C-1）。

edit/clip_<KEY>_source.json の区間（seg.start_sec / seg.end_sec / seg.drops）を
元音源へ適用し、generated/clip_<KEY>_source.m4a を作る。切り抜き編集画面は
この連続音源をそのまま再生する（スキップ処理が不要になる）。
source.json から決定的に再生成できるため generated 扱い（消えても作り直せる）。

書き出し方式は export_audio.py と同じ「区間ごとに抽出 → 無劣化連結 → AAC 256kbps」
（aselect 単一式は約100区間で式パーサが破綻した実害があるため。2026-08-10）。

usage: python scripts/make_clip_source.py <ID> --key <CLIPKEY>
"""
import os
import sys
import json
import pathlib
import argparse
import tempfile
import subprocess

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts"))
import idpaths
from render import find_media, keep_ranges, load_conf
from export_audio import aac_encoder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--key", required=True, help="clipkey（<sid>_<hash8>）")
    args = ap.parse_args()

    paths = load_conf("config/paths.conf")
    root = os.environ.get("SITE_DATA_DIR") or paths.get("PODCAST_ROOT") or str(HERE / "data")
    base = pathlib.Path(root) / args.id

    src_file = pathlib.Path(idpaths.find(str(base), f"clip_{args.key}_source.json"))
    if not src_file.is_file():
        sys.exit(f"[clip] 凍結スナップショットがありません: {src_file}")
    src = json.loads(src_file.read_text(encoding="utf-8"))
    seg = src["seg"]
    keeps = keep_ranges(float(seg["start_sec"]), float(seg["end_sec"]),
                        [tuple(map(float, d)) for d in seg.get("drops", [])])
    if not keeps:
        sys.exit("[clip] 有効区間がありません")

    media = find_media(base, args.id, None)
    if not media or not media.exists():
        sys.exit(f"[clip] メディアが見つかりません（{base}）")
    wav = media.with_suffix(".wav")
    if wav.exists():
        media = wav

    out = pathlib.Path(idpaths.save(str(base), f"clip_{args.key}_source.m4a"))
    enc = aac_encoder()
    tmp = out.with_name(out.name + ".part.m4a")
    pcm = out.with_name(out.name + ".part.wav")
    with tempfile.TemporaryDirectory(dir=str(out.parent)) as td:
        tdp = pathlib.Path(td)
        listf = tdp / "list.txt"
        with open(listf, "w") as lf:
            for i, (a, b) in enumerate(keeps):
                part = tdp / f"p{i:04d}.wav"
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                                "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(media),
                                "-c:a", "pcm_s16le", str(part)], check=True)
                lf.write(f"file '{part.name}'\n")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "concat", "-safe", "0", "-i", str(listf),
                        "-c", "copy", str(pcm)], check=True)
    try:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-i", str(pcm), "-c:a", enc, "-b:a", "256k", str(tmp)], check=True)
    finally:
        pcm.unlink(missing_ok=True)

    # 実尺を検証してから置く（短いファイルを完了と言わないため。export_audio と同じ作法）
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(tmp)],
                           capture_output=True, text=True)
    actual = float(probe.stdout.strip() or 0)
    expected = sum(b - a for a, b in keeps)
    if abs(actual - expected) > 2.0:
        tmp.unlink(missing_ok=True)
        sys.exit(f"[clip] 書き出し尺が不一致（指定{expected:.1f}s / 実際{actual:.1f}s）。"
                 f" ファイルは出力しません")
    tmp.replace(out)
    print(f"[clip] {len(keeps)}区間 / 正味 {int(expected // 60)}分{int(expected % 60):02d}秒"
          f" / AAC 256kbps ({enc}) -> {out}")


if __name__ == "__main__":
    main()
