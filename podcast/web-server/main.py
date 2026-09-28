#!/usr/bin/env python3
# web-server/main.py — podcast タイムライン編集サイト（Flask アプリ本体）。
#
# 動画がメイン。各動画の下に「切り出し全文」を出し、校正用PDFに近い配色で
# カット済み(確定)/カット推奨(未決)/事実確認/候補外/詰め候補(無音)/象徴的セリフ を
# すべて全文中にインライン表示する。文字起こしの場所がそのままタイムラインになる。
#
# 起動:  ローカル = venv/bin/python main.py → http://127.0.0.1:8010/
#        本番     = uwsgi --ini uwsgi/uwsgi.ini（mount=/podcast。プレフィックスは
#                   manage-script-name が剥がすので、この中では意識しない）
# data:  既定は web-server/ の1つ上の data/。環境変数 SITE_DATA_DIR で上書き可。

import os
import re
import json
import html
import mimetypes
import urllib.parse
from difflib import SequenceMatcher

from flask import Flask, Response, request, send_file

HERE = os.path.dirname(os.path.abspath(__file__))
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import idpaths  # data/<ID>/ のファイル配置は idpaths が唯一の定義（D-002 改定）
from render import safe_name  # 書き出しファイル名（タイトル部）の正規化を生成側と揃える
DATA_DIR = os.path.realpath(
    os.environ.get("SITE_DATA_DIR") or os.path.join(os.path.dirname(HERE), "data")
)
PORT = int(os.environ.get("PORT", "8010"))

app = Flask(__name__)


def approot():
    """公開プレフィックス（本番 = /podcast、ローカル = 空）。リンクは必ずこれ経由で作る。"""
    try:
        return request.script_root or ""
    except RuntimeError:
        return ""

MEDIA_FILES = [
    ("final.mp4", "mp4(字幕あり)"),
    ("video_nosub.mp4", "mp4(字幕なし)"),
    ("audio.m4a", "m4a"),
    ("segment.ass", ".ass"),
]

PAGE_CSS = """
/* 既定はダーク（従来のレイアウト）。data-theme="light" でライトに切り替え */
:root { color-scheme: dark; }
:root[data-theme="light"] { color-scheme: light; }
body { font-family: -apple-system, "Hiragino Sans", sans-serif; margin: 24px auto;
       max-width: 960px; padding: 0 16px; line-height: 1.6;
       background:#1b1b1b; color:#e8e8e8; }
:root[data-theme="light"] body { background:#ffffff; color:#111111; }
h1 { font-size: 22px; } h2 { font-size: 18px; margin: 0 0 3px; }
a { color: #2563eb; text-decoration: none; } a:hover { text-decoration: underline; }
.crumb { font-size: 14px; margin-bottom: 16px; }
.crumb a { color:#8c8c8c; }
.meta { color: #ffffff; font-size: 15px; }
:root[data-theme="light"] .meta { color:#111111; }
/* テーマ切替ボタン（右上・最小限） */
.theme-btn { position:fixed; top:10px; right:12px; z-index:9; cursor:pointer;
             font-size:13px; color:#6b7280; border:1px solid #6b728066;
             border-radius:6px; padding:2px 8px; background:transparent; }
/* ライトでは「沈む＝薄い」方向を反転（濃→淡） */
:root[data-theme="light"] .box.summary { background:#f1f1f1; }
:root[data-theme="light"] .r-donespk { color:#c2c2c2; }
:root[data-theme="light"] .ann-donespk { color:#c2c2c2; }
:root[data-theme="light"] .ann-keep { color:#b8b8b8; }
:root[data-theme="light"] .trim.done { color:#c8c8c8; }
ul.ids { list-style: none; padding: 0; max-width: 620px; }
ul.ids li { display:flex; align-items:center; gap:14px;
            padding: 11px 0; border-bottom: 1px solid #ccc4; }
ul.ids li a { flex:1; color: inherit; font-size: 16px; }
ul.ids li a:hover { text-decoration: underline; }
/* 進み具合。白抜きで、落ち着いた色。タイムラインの配色と揃える */
.st { flex:none; font-size: 11px; font-weight: 700; color: #fff;
      padding: 3px 11px; border-radius: 11px; letter-spacing: .04em; }
.st-none  { background: #6b7280; }   /* 未処理  グレー */
.st-done0 { background: #969da8; }   /* 未編集  未処理と似せた少し薄いグレー（2026-09-17） */
.st-wip   { background: #a08040; }   /* 編集中  黄土（タイムラインの無音色） */
.st-done  { background: #804e7f; }   /* 編集完了 紫（本番使用チェックあり。オーナー指定 2026-09-17） */
.st-sent  { background: #804e7f; }   /* 配信済み 紫のまま（オーナー指示 2026-09-17） */
/* 本番使用が付いた ID は一覧でも黄背景（.seg.production と同じ色） */
ul.ids li.production { background:#3a3410; }
:root[data-theme="light"] ul.ids li.production { background:#fff9e4; }
/* 配信済みは黄ではなく薄紫（オーナー指定 #fcefef）。production より優先 */
ul.ids li.delivered { background:#382626; }
:root[data-theme="light"] ul.ids li.delivered { background:#fcefef; }

.seg { border: 1px solid #ccc4; border-radius: 12px; padding: 16px 19px 21px;
       margin-bottom: 35px; }
.seghd { padding-left: 11px; margin-bottom: 13px; }
.seghd .rank { font-weight:700; }
video { width: 100%; max-width: 860px; display: block; border-radius: 6px;
        background: #000; margin: 5px 0 11px; }
.dl { font-size: 13px; margin-bottom: 13px; }
.dl a { margin-right: 16px; color: inherit; }

/* 要約・レビュー：少し行間をつける */
.box.summary { background:#292929; border-radius:5px;
               padding:11px 14px; margin:10px 0; font-size:14px; line-height:1.9; }
.box.summary p { margin:9px 0; }

/* 本文：行間を詰める */
.transcript { margin-top:16px; border-top:1px dashed #ccc6; padding-top:10px; }
.transcript h3 { font-size:14px; margin:3px 0 8px; }
.tp { margin:9px 0; line-height:1.7; }
.ts { color:#94a3b8; font-size:12px; font-variant-numeric:tabular-nums;
      display:block; margin-bottom:0px; }
.ts-link { cursor:pointer; color:#6b7280; }
.ts-link:hover { text-decoration:underline; }
/* 本文チャンク: クリックで直前から再生 */
.txt { cursor:pointer; border-radius:3px; }
.txt:hover { background:#2563eb14; box-shadow:0 0 0 2px #2563eb22; }
/* いま再生中の箇所（hoverと同系だが少し強め） */
.txt.playing { background:#2563eb2e; }
/* 理由の注釈: 該当箇所の直上に独立行で置く（本文の流れを邪魔しない・重ならない） */
.ann-label { display:block; font-size:10px; font-weight:700; line-height:1.35;
             margin:2px 0 0; opacity:.85; }
.ann-done{ color:#888888b3; } .ann-todo{ color:#e7a7bc; }
.ann-fact{ color:#c9eb00; }
.ann-spk{ color:#6b7280; } .ann-donespk{ color:#575757; }
/* 詰め: |← X秒 →| のみ。目立たないグレー（候補=グレー / 詰め済み=より見えにくい薄グレー）。クリックで直前から再生 */
.trim { cursor:pointer; color:#9ca3af; font-weight:700; font-size:12px;
        white-space:nowrap; padding:0 2px; border-radius:3px;
        font-variant-numeric:tabular-nums; }
.trim:hover { background:#9ca3af22; text-decoration:underline; }
.trim.done { color:#575757; }
.trim.done:hover { background:#9ca3af22; }

.chip { display:inline; font-size:12px; font-weight:700; padding:0 5px;
        border-radius:4px; margin:0 3px; white-space:normal; }
/* 線（下線・取り消し線・背景帯）は引かない。色だけで判別する。
   確定＝見えにくいグレー / 未決＝分類ごとの色 */
/* カット済み(確定) = ごく薄いグレー（読み飛ばし用） */
.r-done { color:#888888b3; }
.chip-done { background:#9ca3af; color:#fff; }
/* カット推奨(未決・gpt) = ピンク #e7a7bc（ラベルも本文も） */
.r-todo { color:#e7a7bc; }
.chip-todo { background:#6b7280; color:#fff; }
/* 会話相手(未決) = #30d8ff（ラベルも本文も） */
.r-spkopen { color:#30d8ff; }
.ann-spkopen { color:#30d8ff; }
/* その他の分類(未決) = 紫系 */
.r-other { color:#cdb4e2; }
.ann-other { color:#cdb4e2; }
/* 事実確認 = #c9eb00（ラベルも本文も。下線・背景なし） */
.r-fact { color:#c9eb00; }
.chip-fact { background:#ea580c; color:#fff; }
/* 会話相手の発言（cutlist由来・未処理） = #30d8ff */
.r-spk { color:#30d8ff; }
.chip-spk { background:#6b7280; color:#fff; }
/* カット済み(会話相手の発言) = 削除確定なので沈ませる（#575757 ユーザー指定） */
.r-donespk { color:#575757; }
/* カット/残す 確定ボタン（未決の注釈行に置く） */
.dbtn button { font-size:11px; margin-left:6px; padding:0 8px; cursor:pointer;
               background:transparent; color:inherit; border:1px solid #6b728088;
               border-radius:4px; line-height:1.6; }
.dbtn button:hover { background:#6b728033; }
/* 判断済み: 残す = ただのグレーのテキスト #5d5d5d（ユーザー指定）。本文への下線などは付けない */
.ann-keep { color:#5d5d5d; }
/* オーナー評価 = 金の星（見出し直下）。根拠の発言を併記 */
.rating { font-size:15px; margin:2px 0 2px; }
.rating .stars { color:#f59e0b; letter-spacing:.05em; }
.rating .rq { color:#94a3b8; font-size:13px; }
.rating.unrated { color:#94a3b8; font-size:13px; }
/* 象徴的セリフ = 色なしの太字（モノトーン方針） */
.r-quote { font-weight:700; }
/* 詰め候補(無音) = 紫の点マーカー（本文中に差し込む） */
.chip-trim { background:#7c3aed; color:#fff; font-size:11px; }
.chip-trim.muted { background:#a78bfa; }

/* 目次（縦並び。タイトル・尺・★＋ハイライト原文） */
.toc { margin:10px 0 22px; }
.toc-item { line-height:1.9; font-size:18px; margin-top:8px; }
.toc-item a { color:inherit; }
.toc-item a:hover { text-decoration:underline; }
.toc-q { font-size:14px; color:#9ca3af; line-height:1.7; margin-left:10px; }
.toc-sum { font-size:14px; line-height:1.8; margin:2px 0 4px 10px; opacity:.92; }
.seg { scroll-margin-top:42px; }
/* 全編セグメントは枠で区別する（オーナー指示・2026-08-08） */
.seg.fullep { border: 3px solid #68000044; border-radius: 12px; }
/* 本番使用にチェックした切り出しは背景を黄にする（オーナー指示・2026-09-17）。
   指定色 #fff9e4 はライト用。ダークは同系の暗い黄で沈ませる */
.seg.production { background-color:#3a3410; }
:root[data-theme="light"] .seg.production { background-color:#fff9e4; }
/* 配信済みは黄ではなく薄紫（オーナー指定 #fcefef）。後置で production より優先 */
.seg.delivered { background-color:#382626; }
:root[data-theme="light"] .seg.delivered { background-color:#fcefef; }
.editlink { font-size:13px; color:#6b7280; }
"""

# ---------- タイムライン（文字起こしの場所に埋め込む・別ページは作らない） ----------
TIMELINE_CSS = """
/* 文字起こしの場所がそのままタイムラインになる。別ページは作らない。
   要点は「文字もバーも同じ時間軸の座標に置く」こと。
   x = (時刻 - 行頭時刻) * pxPerSec なので、無音のぶんだけ文字と文字のあいだが空き、
   見た目がそのまま時間になる。 */
.tlbar { display:flex; align-items:center; gap:12px; font-size:12px; color:#9ca3af;
         margin:10px 0 6px; }
.tlbar button { font-size:12px; padding:1px 10px; cursor:pointer; background:transparent;
                color:inherit; border:1px solid #6b728088; border-radius:5px; }
.tlbar button:hover { background:#6b728033; }
.tltime { font-variant-numeric:tabular-nums; min-width:70px; color:#e8e8e8; font-size:13px; }
:root[data-theme="light"] .tltime { color:#111; }
.tlstat { margin-left:auto; }
.tlhelp { font-size:11px; color:#6b7280; line-height:1.8; margin:0 0 8px; }

.row { position:relative; margin:0 0 10px; }
.lane { position:relative; height:76px; }
/* 上から: タイムスタンプ / 発話テキスト / バー。すべて同じ時間軸の x 座標に置く。 */
.ts2 { position:absolute; top:0; font-size:11px; color:#8a8a8a;
       font-variant-numeric:tabular-nums; white-space:nowrap; }
.w { position:absolute; top:16px; white-space:pre; font-size:14px; line-height:20px;
     cursor:pointer; border-radius:2px; }
.w.cut { color:#6d6d6d; }
/* 話者の色分け。メイン話者（最多話者＝大塚さん）は既定色のまま、
   会話相手はモックの赤系に寄せたオレンジ系にする。docs/編集規則.md の
   「Speaker1 はほぼそのまま／会話相手は基本カット」を目で見て分けられるようにする。 */
.w.s2 { color:#d97a2b; } .w.s3 { color:#c9603a; } .w.s4 { color:#b8813a; }
.w.s5 { color:#d4643a; } .w.s6 { color:#c08a3f; } .w.s7 { color:#e0863c; }
.w.s8 { color:#b06a45; } .w.sx { color:#c9773a; }
/* カット済みでも話者の色は保つ。ただし沈める。
   一律グレーにすると「話者が違うから切った」のか「内容で切った」のかが分からなくなる。 */
.w.cut.s2 { color:#8a5a2e; } .w.cut.s3 { color:#84462c; } .w.cut.s4 { color:#7a562c; }
.w.cut.s5 { color:#8a4a2e; } .w.cut.s6 { color:#7d5c2e; } .w.cut.s7 { color:#91582a; }
.w.cut.s8 { color:#754b33; } .w.cut.sx { color:#815129; }
:root[data-theme="light"] .w.cut { color:#c4c4c4; }
:root[data-theme="light"] .w.cut.s2 { color:#f0c79b; }
:root[data-theme="light"] .w.cut.s3 { color:#eeb9a2; }
:root[data-theme="light"] .w.cut.s4 { color:#e8cda0; }
:root[data-theme="light"] .w.cut.s5 { color:#f2bda6; }
:root[data-theme="light"] .w.cut.s6 { color:#ead3a4; }
:root[data-theme="light"] .w.cut.s7 { color:#f5cba3; }
:root[data-theme="light"] .w.cut.s8 { color:#e3c3ae; }
:root[data-theme="light"] .w.cut.sx { color:#eec9a4; }
/* 話者ラベル。会話相手のターンの頭に小さく出す */
.spk { position:absolute; top:0; font-size:10px; font-weight:700; white-space:nowrap; }
.spk.s2 { color:#d97a2b; } .spk.s3 { color:#c9603a; } .spk.s4 { color:#b8813a; }
.spk.s5 { color:#d4643a; } .spk.s6 { color:#c08a3f; } .spk.s7 { color:#e0863c; }
.spk.s8 { color:#b06a45; } .spk.sx { color:#c9773a; }
.w.playing { background:#2563eb33; }
/* バーは常に1本の連続した帯。カットしても消さず、黒く塗る（AfterEffects と同じ見え方）。
   青緑＝発話 / 黄＝VADが検出した無音 / 黒＝カット済み。 */
.strip { position:absolute; left:0; right:0; top:40px; height:16px; cursor:crosshair; }
.barbase { position:absolute; top:0; height:16px; background:#5f8a9c; }
.sil { position:absolute; top:0; height:16px; background:#a89a3c; }
.cutz { position:absolute; top:0; height:16px; background:#2e2e2e; }
/* ドラッグ中の端は印として明示する（AfterEffects と同様） */
.splitline { position:absolute; top:-3px; height:22px; width:12px; pointer-events:none; }
.splitline::before, .splitline::after {
  content:''; position:absolute; top:0; bottom:0; width:4px;
  border-top:2px solid #e8e8e8; border-bottom:2px solid #e8e8e8; }
.splitline::before { left:0;  border-right:2px solid #e8e8e8; }   /* ] 左クリップの終端 */
.splitline::after  { right:0; border-left:2px solid #e8e8e8; }    /* [ 右クリップの始端 */
.edge { position:absolute; top:-2px; height:20px; width:2px; background:#e8e8e8; opacity:0; }
.edge.on { opacity:1; }
.hoverline { position:absolute; top:-26px; bottom:-2px; width:1px; background:#9ca3af;
             display:none; pointer-events:none; }
.playline { position:absolute; top:-26px; bottom:-2px; width:2px; background:#e11d48;
            display:none; pointer-events:none; z-index:3; }
.tlabel { position:absolute; top:-40px; font-size:10px; color:#9ca3af; display:none;
          pointer-events:none; font-variant-numeric:tabular-nums; white-space:nowrap; }
.tlwait { color:#6b7280; font-size:12px; padding:12px 0; }
/* 象徴的セリフ（highlight_quotes）は色を付けず太字にする（D-008 モノトーン方針） */
.w.hl { font-weight:700; }
/* 未決のカット候補。バーの直下に細い帯で出す。分類色は D-013 準拠 */
.pend { position:absolute; top:58px; height:5px; cursor:pointer; border-radius:2px; }
.pend.gpt { background:#e7a7bc; } .pend.speaker { background:#30d8ff; }
.pend.fact { background:#c9eb00; } .pend.other { background:#cdb4e2; }
.pend:hover { filter:brightness(1.25); }
.pcid { position:absolute; top:64px; font-size:10px; font-weight:700; white-space:nowrap;
        pointer-events:none; }
.pcid.gpt { color:#e7a7bc; } .pcid.speaker { color:#30d8ff; }
.pcid.fact { color:#c9eb00; } .pcid.other { color:#cdb4e2; }
/* 未決をクリックしたときに出す小さなパネル */
.pbox { position:fixed; z-index:50; max-width:420px; background:#232323; color:#e8e8e8;
        border:1px solid #6b7280; border-radius:8px; padding:10px 12px; font-size:12px;
        line-height:1.7; box-shadow:0 6px 24px #0008; }
:root[data-theme="light"] .pbox { background:#fff; color:#111; box-shadow:0 6px 24px #0003; }
.pbox b { font-size:13px; }
.pbox .q { color:#9ca3af; }
.pbox .btns { margin-top:8px; display:flex; gap:8px; }
.pbox button { font-size:12px; padding:3px 14px; cursor:pointer; background:transparent;
               color:inherit; border:1px solid #6b728088; border-radius:5px; }
.pbox button:hover { background:#6b728033; }
/* いまキー操作の対象になっているタイムライン。Space がどれに効くかを示す */
.tl { border-left:3px solid transparent; padding-left:9px; margin-left:-12px; }
.tl.tlfocus { border-left-color:#2563eb; }
"""

# ---------- 切り抜き編集画面（CLIP_PLAN C-2〜C-5）----------
CLIP_CSS = """
/* 切り抜き編集画面。1次編集のタイムラインと同じ見た目の作法で、
   時間軸は凍結版の編集後時間（カットを詰めた連続時間）。 */
.cu { position:absolute; top:16px; white-space:pre; font-size:14px; line-height:20px;
      cursor:text; border-radius:2px; max-width:none; }
.cu.out { color:#6d6d6d; }                    /* どの切り抜きにも入っていない部分 */
:root[data-theme="light"] .cu.out { color:#c4c4c4; }
.cu.playing { background:#2563eb33; }
.cu:hover { background:#2563eb14; box-shadow:0 0 0 2px #2563eb22; }
.cu input { font:inherit; color:inherit; background:#2563eb18;
            border:1px solid #2563eb88; border-radius:3px; padding:0 2px; }
/* 切り抜きセグメント＝開始から終了までグラデーション（原文 L21）。
   開始側が明るい（開始と終了を色で見分ける。オーナー指示 2026-09-28・原文 L98） */
.clipz { position:absolute; top:0; height:24px;
         background-image:linear-gradient(90deg,#4fb3ff,#5b39c9); background-repeat:no-repeat; }
/* 切り抜きの間（空白）は黒（原文 L98） */
.gapz { position:absolute; top:0; height:24px; background:#141417; }
/* 開始端＝太い白線 / 終了端＝細い白線 */
.clipedge-s { position:absolute; top:-4px; height:32px; width:3px; background:#ffffff;
              pointer-events:none; z-index:2; }
.clipedge-e { position:absolute; top:-2px; height:28px; width:2px; background:#ffffffb0;
              pointer-events:none; z-index:2; }
/* S（開始指定）の保留マーカー。緑は土台と紛らわしいのでオレンジ（原文 L98） */
.startline { position:absolute; top:-26px; bottom:-2px; width:3px; background:#ff9800;
             pointer-events:none; z-index:2; }
.startlabel { position:absolute; top:-40px; font-size:10px; font-weight:700; color:#ff9800;
              pointer-events:none; }
.clipsel { position:absolute; top:-3px; height:30px; pointer-events:none;
           box-shadow:inset 0 0 0 2px #2563eb; }
/* 切り抜き編集のタイムラインは少し太く(24px)・土台は青緑でなくグレー（原文 L98。
   1次編集のタイムラインには影響させない） */
.cliptl .strip { height:24px; }
.cliptl .barbase { height:24px; background:#4c525c; }
.cliptl .splitline { height:30px; }
.cliptl .lane { height:84px; }
/* コンテナ。既存 TIMELINE_JS が拾う .tl は使わない（同じ要素を二重に組んで壊れる） */
.cliptl { border-left:3px solid #2563eb; padding-left:9px; margin-left:-12px; }
/* 主要導線ボタン。Google 風（オーナー指示 2026-09-28・原文 L97） */
.gbtn { display:inline-block; background:#1a73e8; color:#fff; border:none;
        border-radius:6px; padding:7px 16px; font-size:13px; font-weight:600;
        font-family:inherit; letter-spacing:.02em; cursor:pointer;
        text-decoration:none; line-height:1.5; box-shadow:0 1px 2px #0003; }
.gbtn:hover { background:#1765cc; box-shadow:0 1px 3px #0004; text-decoration:none; }
.gbtn:disabled { background:#dadce0; color:#80868b; cursor:default; box-shadow:none; }
:root:not([data-theme="light"]) .gbtn:disabled { background:#3c4043; color:#9aa0a6; }
/* セグメント参考（AI 候補。C-12） */
.sugbox { border:1px solid #ccc4; border-radius:12px; padding:14px 18px 16px;
          margin:14px 0 22px; }
.sughd { display:flex; align-items:center; gap:14px; margin-bottom:6px; }
.sughd b { font-size:15px; }
.sugitem { margin:12px 0 0; }
.sugtitle { font-size:15px; font-weight:700; line-height:1.6; }
.sugtime { font-size:13px; color:#6b7280; font-variant-numeric:tabular-nums; }
.sugtime a { color:#2563eb; cursor:pointer; }
.sugtext { font-size:13px; line-height:1.8; opacity:.9; margin-top:2px; }
"""

CLIP_JS = r"""
/* 切り抜き編集画面のタイムライン（1ページに1本）。凍結音源は連続なので
   再生にスキップ処理はない。設計の正本は podcast/CLIP_PLAN.md。 */
(function(){
var root=document.getElementById('cliptl');
if(!root) return;
var D=JSON.parse(root.querySelector('script[type="application/json"]').textContent);
var audio=document.getElementById('orig');
var pxPerSec=parseFloat(localStorage.getItem('tl_pps'))||140;
var clips=(D.clips||[]).map(function(c){return [+c[0],+c[1]];});
var units=(D.units||[]).map(function(u){return {s:+u.s,e:+u.e,t:String(u.t)};});
var pendingStart=null, playhead=0, selCi=-1;
var rows=[], laneW=0, built=false, playing=false;
var undoStack=[], redoStack=[], lastOp='', saveTimer=null;
var host=root.querySelector('.tlrows');
var elTime=root.querySelector('.tltime'), elStat=root.querySelector('.tlstat');
var elZoom=root.querySelector('.tlzoom'), elBtn=root.querySelector('.tlplay');
var elSel=root.querySelector('.tlsel');
var MINW=0.05, EPS=0.01;

function fmtAbs(t){
  var m=Math.floor(t/60), s=t-m*60;
  return m+':'+(s<10?'0':'')+s.toFixed(2);
}
function X(R,t){ return (t-R.t0)*pxPerSec; }
function T(R,x){ return R.t0 + x/pxPerSec; }
function clipAt(t){ for(var i=0;i<clips.length;i++){ if(clips[i][0]<=t&&t<clips[i][1]) return i; } return -1; }
function setStatus(s){ if(elStat) elStat.textContent=s; }

/* ---- 保存（C-5）。1次編集と同じ三重の作法:
   操作の瞬間に localStorage へ同期的に記録 → サーバー送信は後追い（失敗は3秒再送）→
   サーバー側で受信ジャーナル・履歴退避・git 同期キュー ---- */
function journalNow(){
  try{ var k='clip_journal_'+D.key, j=JSON.parse(localStorage.getItem(k)||'[]');
       j.push({at:Date.now(),op:lastOp,clips:clips,units:units});
       try{ localStorage.setItem(k,JSON.stringify(j)); }
       catch(qe){ j=j.slice(Math.floor(j.length/2));
                  try{ localStorage.setItem(k,JSON.stringify(j)); }catch(e2){} }
       localStorage.setItem('clip_dirty_'+D.key,'1');
  }catch(e){}
}
function scheduleSave(){ journalNow(); setStatus('未保存'); clearTimeout(saveTimer); saveTimer=setTimeout(doSave,0); }
function doSave(){
  setStatus('保存中…');
  var rec={id:D.id,key:D.key,op:lastOp,clips:clips,units:units};
  lastOp='';
  fetch(window.APP+'/clip_save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(rec)})
  .then(function(r){
    if(r.ok){ setStatus('保存済み'); try{ localStorage.removeItem('clip_dirty_'+D.key); }catch(e){} }
    else{ setStatus('保存失敗（3秒後に再送します）'); clearTimeout(saveTimer); saveTimer=setTimeout(doSave,3000); }
  })
  .catch(function(){ setStatus('サーバーに接続できません（3秒後に再送します）');
    clearTimeout(saveTimer); saveTimer=setTimeout(doSave,3000); });
}

function build(){
  host.innerHTML=''; rows=[];
  var probe=document.createElement('div'); probe.className='lane';
  host.appendChild(probe); laneW=probe.clientWidth||800; host.removeChild(probe);
  var rowSec=laneW/pxPerSec;
  var nRows=Math.max(1,Math.ceil(D.duration/rowSec));
  if(elZoom) elZoom.textContent=pxPerSec.toFixed(0)+'px/秒・1行'+rowSec.toFixed(1)+'秒';
  var ui=0;
  for(var r=0;r<nRows;r++){
    var t0=r*rowSec, t1=Math.min(D.duration,t0+rowSec);
    var row=document.createElement('div'); row.className='row';
    var lane=document.createElement('div'); lane.className='lane'; row.appendChild(lane);
    var strip=document.createElement('div'); strip.className='strip'; lane.appendChild(strip);
    var lastRight=-1e9, lastTsRight=-1e9, els=[], prevEnd=null;
    while(ui<units.length && units[ui].s < t1){
      var u=units[ui];
      if(u.e<=t0){ ui++; continue; }
      var x=(u.s-t0)*pxPerSec;
      if(x<lastRight) x=lastRight;
      var newBlock=(prevEnd===null || u.s-prevEnd>=0.8);
      if(newBlock && x>=lastTsRight){
        var ts=document.createElement('div'); ts.className='ts2';
        ts.textContent=fmtAbs(u.s); ts.style.left=x+'px';
        lane.appendChild(ts); lastTsRight=x+ts.offsetWidth+8;
      }
      var el=document.createElement('span'); el.className='cu';
      el.textContent=u.t; el.style.left=x+'px';
      el.dataset.ui=ui;
      lane.appendChild(el); els.push(el);
      lastRight=x+el.offsetWidth+6; prevEnd=u.e; ui++;
    }
    host.appendChild(row);
    var R={t0:t0,t1:t1,strip:strip,els:els,lane:lane};
    rows.push(R); bindStrip(R);
  }
  built=true;
  renderBars(); styleUnits(); movePlayhead();
}

function renderBars(){
  rows.forEach(function(R){
    R.strip.innerHTML='';
    var W=X(R,R.t1);
    var base=document.createElement('div'); base.className='barbase';
    base.style.left='0px'; base.style.width=W+'px'; R.strip.appendChild(base);
    /* 切り抜きの間（どの切り抜きにも入らない区間）は黒（原文 L98）。
       まだ1本も無いときは全部黒にせず土台色のまま */
    if(clips.length){
      var t=0;
      clips.slice().sort(function(a,b){return a[0]-b[0];}).concat([[D.duration,D.duration]])
        .forEach(function(c){
          var a=Math.max(t,R.t0), b=Math.min(c[0],R.t1);
          if(b-a>0){
            var g=document.createElement('div'); g.className='gapz';
            g.style.left=X(R,a)+'px'; g.style.width=Math.max(1,X(R,b)-X(R,a))+'px';
            R.strip.appendChild(g);
          }
          t=Math.max(t,c[1]);
        });
    }
    /* 切り抜きセグメント。開始（明）→終了（暗）で1本のグラデーション。行をまたいでも
       background-position をずらして1本につながって見えるようにする */
    clips.forEach(function(c,ci){
      var a=Math.max(c[0],R.t0), b=Math.min(c[1],R.t1);
      if(b-a<=0) return;
      var d=document.createElement('div'); d.className='clipz';
      d.style.left=X(R,a)+'px'; d.style.width=Math.max(1,X(R,b)-X(R,a))+'px';
      d.style.backgroundSize=((c[1]-c[0])*pxPerSec)+'px 100%';
      d.style.backgroundPosition=(-(a-c[0])*pxPerSec)+'px 0';
      R.strip.appendChild(d);
      /* (a) 結合で捨てた間（drops）は切り抜きの中でも黒 */
      (c[2]||[]).forEach(function(dr){
        var da=Math.max(dr[0],R.t0), db=Math.min(dr[1],R.t1);
        if(db-da<=0) return;
        var g2=document.createElement('div'); g2.className='gapz';
        g2.style.left=X(R,da)+'px'; g2.style.width=Math.max(1,X(R,db)-X(R,da))+'px';
        R.strip.appendChild(g2);
      });
      /* 開始端＝太い白線 / 終了端＝細い白線（開始が分かりにくい問題。原文 L98） */
      if(c[0]>=R.t0-1e-9&&c[0]<=R.t1){
        var es=document.createElement('div'); es.className='clipedge-s';
        es.style.left=X(R,c[0])+'px'; R.strip.appendChild(es);
      }
      if(c[1]>=R.t0&&c[1]<=R.t1+1e-9){
        var ee=document.createElement('div'); ee.className='clipedge-e';
        ee.style.left=(X(R,c[1])-2)+'px'; R.strip.appendChild(ee);
      }
      if(ci===selCi){
        var sel=document.createElement('div'); sel.className='clipsel';
        sel.style.left=X(R,a)+'px'; sel.style.width=Math.max(1,X(R,b)-X(R,a))+'px';
        R.strip.appendChild(sel);
      }
    });
    /* 隣接する切り抜きの境界（分割線） */
    for(var i=0;i+1<clips.length;i++){
      if(Math.abs(clips[i][1]-clips[i+1][0])>EPS) continue;
      var bt=clips[i][1];
      if(bt<R.t0||bt>R.t1) continue;
      var sp=document.createElement('div'); sp.className='splitline';
      sp.style.left=(X(R,bt)-6)+'px'; R.strip.appendChild(sp);
    }
    /* S（開始指定）の保留マーカー */
    if(pendingStart!=null && pendingStart>=R.t0 && pendingStart<=R.t1){
      var st=document.createElement('div'); st.className='startline';
      st.style.left=X(R,pendingStart)+'px'; R.strip.appendChild(st);
      var sl=document.createElement('div'); sl.className='startlabel';
      sl.textContent='S 開始'; sl.style.left=(X(R,pendingStart)+4)+'px';
      R.strip.appendChild(sl);
    }
    R.hover=document.createElement('div'); R.hover.className='hoverline'; R.strip.appendChild(R.hover);
    R.play=document.createElement('div'); R.play.className='playline'; R.strip.appendChild(R.play);
    R.tlab=document.createElement('div'); R.tlab.className='tlabel'; R.strip.appendChild(R.tlab);
  });
  var kept=clips.reduce(function(a,c){return a+(c[1]-c[0]);},0);
  var el=root.querySelector('.tlkeep');
  if(el){ var m=Math.floor(kept/60), s=Math.round(kept-m*60);
    el.textContent=clips.length+'本・計 '+m+'分'+(s<10?'0':'')+s+'秒'; }
}

function styleUnits(){
  rows.forEach(function(R){
    R.els.forEach(function(el){
      var u=units[+el.dataset.ui]; if(!u) return;
      var mid=(u.s+u.e)/2;
      /* まだ1本も指定していない段階では沈ませない（全部カット済みに見えるため） */
      el.classList.toggle('out', clips.length>0 && clipAt(mid)<0);
    });
  });
}

function movePlayhead(){
  rows.forEach(function(R){ if(R.play) R.play.style.display='none'; });
  var R=rows.find(function(R){return R.t0<=playhead&&playhead<R.t1;})||rows[rows.length-1];
  if(R&&R.play){ R.play.style.left=X(R,playhead)+'px'; R.play.style.display='block'; }
  if(elTime) elTime.textContent=fmtAbs(playhead);
}

function highlight(t){
  root.querySelectorAll('.cu.playing').forEach(function(x){x.classList.remove('playing');});
  var best=-1;
  units.forEach(function(u,i){ if(u.s<=t+0.01&&(best<0||u.s>units[best].s)) best=i; });
  if(best<0||t-units[best].s>30) return;
  var el=root.querySelector(".cu[data-ui='"+best+"']");
  if(el) el.classList.add('playing');
}

/* ---- 再生（連続音源。スキップなし） ---- */
function tick(){
  if(!playing) return;
  var t=audio.currentTime;
  if(t>=D.duration){ stop(); return; }
  playhead=t; movePlayhead(); highlight(t);
  requestAnimationFrame(tick);
}
function applyRate(){ try{ audio.playbackRate=parseFloat(localStorage.getItem('tl_rate')||'1'); }catch(e){} }
function play(){
  if(!audio){ setStatus('凍結音源がまだありません'); return; }
  applyRate();
  var go=function(){
    try{ audio.currentTime=playhead; }
    catch(err){ setStatus('シークできません: '+err.name); return; }
    audio.play().then(function(){ playing=true; if(elBtn) elBtn.textContent='∎ 停止';
      setStatus('再生中'); requestAnimationFrame(tick); })
      .catch(function(err){ setStatus('再生できません: '+err.name+' '+(err.message||'')); });
  };
  if(audio.readyState>=1){ go(); }
  else{
    setStatus('音源を読み込み中…');
    audio.addEventListener('loadedmetadata', go, {once:true});
    audio.addEventListener('error', function(){
      setStatus('音源を読み込めません。リロードしてください'); }, {once:true});
    audio.load();
  }
}
function stop(){
  if(audio) audio.pause();
  playing=false;
  if(elBtn) elBtn.textContent='▶ 再生';
  root.querySelectorAll('.cu.playing').forEach(function(x){x.classList.remove('playing');});
}

var pbox=null, hoverT=null;
function closeMenu(){ if(pbox){ pbox.remove(); pbox=null; } }
function esc(t){ return String(t).replace(/[&<>]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]; }); }

/* ---- 編集操作（C-3）。すべて Undo できる ---- */
function snapshot(){ return JSON.stringify({c:clips,u:units,p:pendingStart}); }
function restore(s){ var d=JSON.parse(s); clips=d.c; units=d.u; pendingStart=d.p; }
function pushUndo(){ undoStack.push(snapshot()); if(undoStack.length>200)undoStack.shift(); redoStack=[]; }
function undo(){ if(!undoStack.length){ setStatus('取り消す操作がありません'); return; }
  redoStack.push(snapshot()); restore(undoStack.pop()); selCi=-1; lastOp='undo'; afterEdit(true); }
function redo(){ if(!redoStack.length) return;
  undoStack.push(snapshot()); restore(redoStack.pop()); selCi=-1; lastOp='redo'; afterEdit(true); }
function afterEdit(rebuildRows){
  clips.sort(function(a,b){return a[0]-b[0];});
  if(rebuildRows){ build(); } else { renderBars(); styleUnits(); movePlayhead(); }
  scheduleSave();
}
function normalizeClips(){
  /* 重なりは1本に統合する */
  clips.sort(function(a,b){return a[0]-b[0];});
  var out=[];
  clips.forEach(function(c){
    if(out.length&&c[0]<=out[out.length-1][1]+EPS){
      out[out.length-1][1]=Math.max(out[out.length-1][1],c[1]);
    }else out.push([c[0],c[1]]);
  });
  clips=out;
}
function markStart(t){
  var ci=clipAt(t);
  if(ci>=0){
    /* 切り抜きの中で S ＝ その時点で分割（原文 L17） */
    var c=clips[ci];
    if(t-c[0]<MINW||c[1]-t<MINW){ setStatus('端に近すぎて分割できません'); return; }
    pushUndo(); lastOp='split@'+t.toFixed(1);
    clips.splice(ci,1,[c[0],t],[t,c[1]]); selCi=-1; afterEdit();
    setStatus('切り抜きを分割しました');
  }else{
    pushUndo(); lastOp='start@'+t.toFixed(1);
    pendingStart=t; afterEdit();
    setStatus('開始を指定しました（終了位置で E）');
  }
}
function markEnd(t){
  if(pendingStart!=null){
    if(t<=pendingStart+MINW){ setStatus('終了は開始より後にしてください'); return; }
    pushUndo(); lastOp='clip@'+pendingStart.toFixed(1)+'-'+t.toFixed(1);
    clips.push([pendingStart,t]); pendingStart=null;
    normalizeClips(); selCi=-1; afterEdit();
    setStatus('切り抜きを追加しました');
    return;
  }
  var ci=clipAt(t);
  if(ci>=0){
    if(t-clips[ci][0]<MINW){ setStatus('終了は開始より後にしてください'); return; }
    pushUndo(); lastOp='end@'+t.toFixed(1);
    clips[ci][1]=t; selCi=-1; afterEdit();
    setStatus('終了を指定しました（外側は空白になります）');
  }else setStatus('先に S で開始を指定してください');
}
function joinGap(t){
  /* 空白で「この間を詰める」＝前後の切り抜きを1本に結合する（原文 L23） */
  if(clipAt(t)>=0){ setStatus('ここは切り抜きの中です'); return; }
  var prev=null, next=null;
  clips.forEach(function(c,i){
    if(c[1]<=t&&(prev===null||c[1]>clips[prev][1])) prev=i;
    if(c[0]>=t&&(next===null||c[0]<clips[next][0])) next=i;
  });
  if(prev===null||next===null){ setStatus('この空白の前後に切り抜きがありません'); return; }
  pushUndo(); lastOp='join@'+t.toFixed(1);
  var a=clips[prev][0], b=clips[next][1];
  clips=clips.filter(function(c,i){return i!==prev&&i!==next;});
  clips.push([a,b]); pendingStart=null;
  normalizeClips(); selCi=-1; afterEdit();
  setStatus('つなげて1つの切り抜きにしました');
}
function deleteSel(){
  if(selCi<0){ setStatus('切り抜きをクリックして選択してから Delete'); return; }
  pushUndo(); lastOp='unclip';
  clips.splice(selCi,1); selCi=-1; afterEdit();
  setStatus('切り抜きを解除しました（音は消えていません。S/E で指定し直せます）');
}

/* 端のドラッグ調整 */
var dragging=null;
function edgesAt(R,x){
  var out=[];
  clips.forEach(function(c,ci){
    if(c[1]<=R.t0||c[0]>=R.t1) return;
    if(c[0]>=R.t0-1e-9&&Math.abs(x-X(R,c[0]))<8) out.push({ci:ci,which:0});
    if(c[1]<=R.t1+1e-9&&Math.abs(x-X(R,c[1]))<8) out.push({ci:ci,which:1});
  });
  return out;
}
document.addEventListener('mousemove',function(ev){
  if(!dragging) return;
  var R=dragging.R;
  var t=T(R, ev.clientX-R.strip.getBoundingClientRect().left);
  var c=clips[dragging.ci]; if(!c) return;
  if(dragging.which===0){
    var lo=0;
    clips.forEach(function(o,i){ if(i!==dragging.ci&&o[1]<=c[1]&&o[1]>lo) lo=o[1]; });
    c[0]=Math.min(Math.max(t,lo),c[1]-MINW);
  }else{
    var hi=D.duration;
    clips.forEach(function(o,i){ if(i!==dragging.ci&&o[0]>=c[0]&&o[0]<hi) hi=o[0]; });
    c[1]=Math.max(Math.min(t,hi),c[0]+MINW);
  }
  renderBars(); styleUnits(); movePlayhead();
});
document.addEventListener('mouseup',function(){
  if(dragging){ dragging=null; lastOp='trim'; scheduleSave(); }
});

function bindStrip(R){
  R.strip.addEventListener('mousemove',function(ev){
    var x=ev.clientX-R.strip.getBoundingClientRect().left;
    R.hover.style.left=x+'px'; R.hover.style.display='block';
    R.tlab.style.left=(x+4)+'px'; R.tlab.style.display='block';
    R.tlab.textContent=fmtAbs(T(R,x));
  });
  R.strip.addEventListener('mouseleave',function(){
    R.hover.style.display='none'; R.tlab.style.display='none';
  });
  R.lane.addEventListener('mousemove',function(ev){
    hoverT=T(R, ev.clientX-R.strip.getBoundingClientRect().left);
  });
  R.lane.addEventListener('mouseleave',function(){ hoverT=null; });
  R.lane.addEventListener('contextmenu',function(ev){
    ev.preventDefault();
    var t=T(R, ev.clientX-R.strip.getBoundingClientRect().left);
    openCtx(t, ev.clientX, ev.clientY, ev.target.closest('.cu'));
  });
  R.strip.addEventListener('mousemove',function(ev){
    var x=ev.clientX-R.strip.getBoundingClientRect().left;
    R.strip.style.cursor=edgesAt(R,x).length?'ew-resize':'crosshair';
  });
  R.strip.addEventListener('mousedown',function(ev){
    ev.preventDefault(); closeMenu();
    var x=ev.clientX-R.strip.getBoundingClientRect().left;
    var cand=edgesAt(R,x);
    if(cand.length){ pushUndo(); dragging={R:R,ci:cand[0].ci,which:cand[0].which}; return; }
    playhead=T(R,x);
    selCi=clipAt(playhead);
    renderBars(); movePlayhead();
    if(playing) audio.currentTime=playhead;
  });
}

/* ---- テキスト修正（C-4・原文 L25-29）。字幕の元になるので直せなければならない ---- */
function editUnit(el){
  var ui=+el.dataset.ui, u=units[ui]; if(!u) return;
  if(el.querySelector('input')) return;
  var inp=document.createElement('input');
  inp.value=u.t; inp.size=Math.max(u.t.length+2,8);
  el.textContent=''; el.appendChild(inp); inp.focus();
  var closed=false;
  var done=function(commit){
    if(closed) return; closed=true;
    var v=inp.value;
    if(commit&&v!==u.t){
      pushUndo(); lastOp='text@'+u.s.toFixed(1);
      if(v.trim()===''){ units.splice(ui,1); setStatus('テキストを削除しました'); }
      else { u.t=v; setStatus('テキストを修正しました'); }
      afterEdit(true);
    }else{
      /* 取り消し。挿入直後の空ユニットはゴミになるので消す */
      if(u.t===''){ units.splice(ui,1); }
      build();
    }
  };
  inp.addEventListener('keydown',function(ev){
    ev.stopPropagation();
    if(ev.key==='Enter'){ done(true); }
    else if(ev.key==='Escape'){ done(false); }
  });
  inp.addEventListener('blur',function(){ done(true); });
}
host.addEventListener('click',function(ev){
  var el=ev.target.closest('.cu'); if(!el) return;
  editUnit(el);
});
function insertUnit(t){
  pushUndo(); lastOp='instext@'+t.toFixed(1);
  var next=null; units.forEach(function(u){ if(u.s>t&&(next===null||u.s<next)) next=u.s; });
  var e=Math.min(t+3, next!==null?next:D.duration, D.duration);
  if(e-t<0.3) e=Math.min(t+0.5,D.duration);
  var nu={s:+t.toFixed(3),e:+e.toFixed(3),t:''};
  units.push(nu); units.sort(function(a,b){return a.s-b.s;});
  build();
  var idx=units.indexOf(nu);
  var el=root.querySelector(".cu[data-ui='"+idx+"']");
  if(el) editUnit(el);
}
window.clipTextMenu=function(t,cuEl){
  var items=[];
  if(cuEl) items.push({a:'delunit',label:'このテキストを削除'});
  items.push({a:'insunit',label:'ここにテキストを挿入'});
  return items;
};
window.clipTextRun=function(act,t,cuEl){
  if(act==='delunit'&&cuEl){
    var ui=+cuEl.dataset.ui;
    if(!units[ui]) return;
    pushUndo(); lastOp='deltext@'+t.toFixed(1);
    units.splice(ui,1); afterEdit(true);
    setStatus('テキストを削除しました');
  }else if(act==='insunit'){ insertUnit(t); }
};

/* 右クリックメニュー。即実行しない作法は1次編集と同じ（オーナー指示 2026-08-05） */
function openCtx(t,cx,cy,cuEl){
  closeMenu();
  pbox=document.createElement('div'); pbox.className='pbox';
  pbox.style.left=Math.min(cx,window.innerWidth-280)+'px';
  pbox.style.top=Math.min(cy+8,window.innerHeight-260)+'px';
  var items=[{a:'play',label:'ここから再生'},
             {a:'start',label:'ここを開始にする（S）'},
             {a:'end',label:'ここを終了にする（E）'}];
  if(clipAt(t)<0) items.push({a:'join',label:'この間を詰める（前後をつなげる）'});
  if(window.clipTextMenu) items=items.concat(window.clipTextMenu(t,cuEl));
  var html='<b>'+fmtAbs(t)+'</b><div class="btns" style="flex-direction:column;align-items:stretch">';
  items.forEach(function(it){ html+='<button data-a="'+it.a+'">'+esc(it.label)+'</button>'; });
  html+='<button data-a="close">閉じる</button></div>';
  pbox.innerHTML=html;
  document.body.appendChild(pbox);
  pbox.querySelectorAll('button').forEach(function(b){
    b.onclick=function(){
      var act=b.dataset.a; closeMenu();
      if(act==='play'){ playhead=t; movePlayhead(); play(); }
      else if(act==='start'){ markStart(t); }
      else if(act==='end'){ markEnd(t); }
      else if(act==='join'){ joinGap(t); }
      else if(act==='close'){ }
      else if(window.clipTextRun){ window.clipTextRun(act,t,cuEl); }
    };
  });
}
document.addEventListener('mousedown',function(ev){
  if(pbox&&!pbox.contains(ev.target)) closeMenu();
});

document.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
  if(e.code==='Space'){ e.preventDefault(); playing?stop():play(); }
  else if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='z'){ e.preventDefault(); e.shiftKey?redo():undo(); }
  else if((e.metaKey||e.ctrlKey)&&(e.key==='='||e.key==='+')){ e.preventDefault(); setZoom(pxPerSec*1.4); }
  else if((e.metaKey||e.ctrlKey)&&e.key==='-'){ e.preventDefault(); setZoom(pxPerSec/1.4); }
  /* S＝開始・E＝終了（原文 L17-18）。現在時刻バーの位置に効く。
     マウスが行の上にあるときはその位置を優先する（⌘D と同じ考え方） */
  else if(!e.metaKey&&!e.ctrlKey&&!e.altKey&&e.key.toLowerCase()==='s'){
    e.preventDefault(); markStart(hoverT!=null?hoverT:playhead); }
  else if(!e.metaKey&&!e.ctrlKey&&!e.altKey&&e.key.toLowerCase()==='e'){
    e.preventDefault(); markEnd(hoverT!=null?hoverT:playhead); }
  else if(e.key==='Delete'||e.key==='Backspace'){ e.preventDefault(); deleteSel(); }
  else if(e.key==='Escape'&&pendingStart!=null){ pendingStart=null; renderBars(); setStatus('開始指定を取り消しました'); }
});

function setZoom(v){
  pxPerSec=Math.max(20,Math.min(600,v));
  localStorage.setItem('tl_pps',pxPerSec);
  build();
}
if(elBtn) elBtn.onclick=function(){ playing?stop():play(); };
var zi=root.querySelector('.tlzin'), zo=root.querySelector('.tlzout');
if(zi) zi.onclick=function(){ setZoom(pxPerSec*1.4); };
if(zo) zo.onclick=function(){ setZoom(pxPerSec/1.4); };
var ub=root.querySelector('.tlundo'), rb=root.querySelector('.tlredo');
if(ub) ub.onclick=undo;
if(rb) rb.onclick=redo;
var sp=root.querySelector('.tlspeed');
if(sp){
  sp.value=localStorage.getItem('tl_rate')||'1';
  sp.onchange=function(){ localStorage.setItem('tl_rate',sp.value);
    if(audio) audio.playbackRate=parseFloat(sp.value); };
}
var rsz=null;
window.addEventListener('resize',function(){
  clearTimeout(rsz); rsz=setTimeout(function(){ if(built) build(); },200);
});
build();

/* 未保存の編集の検知と復元（1次編集と同じ作法。自動では書き換えない） */
(function(){
  var has=false;
  try{ has=!!(localStorage.getItem('clip_dirty_'+D.key)
        && JSON.parse(localStorage.getItem('clip_journal_'+D.key)||'[]').length); }catch(e){}
  if(!has) return;
  setStatus('未保存の編集があります');
  var rb2=document.createElement('button');
  rb2.textContent='未保存の編集を復元';
  rb2.onclick=function(){
    try{
      var jj=JSON.parse(localStorage.getItem('clip_journal_'+D.key)||'[]');
      if(!jj.length){ setStatus('復元できる編集がありません'); return; }
      pushUndo(); lastOp='restore-unsaved';
      var last=jj[jj.length-1];
      clips=(last.clips||[]).map(function(c){return [+c[0],+c[1]];});
      units=(last.units||[]).map(function(u){return {s:+u.s,e:+u.e,t:String(u.t)};});
      selCi=-1; afterEdit(true); rb2.remove();
    }catch(e){ setStatus('復元に失敗しました'); }
  };
  var bar=root.querySelector('.tlbar');
  if(bar) bar.appendChild(rb2);
})();

/* C-3〜C-5 が使う内部状態への窓口 */
window.clipTL={
  get clips(){ return clips; }, set clips(v){ clips=v; },
  get units(){ return units; }, set units(v){ units=v; },
  get pendingStart(){ return pendingStart; }, set pendingStart(v){ pendingStart=v; },
  get playhead(){ return playhead; }, get hoverT(){ return hoverT; },
  get selCi(){ return selCi; }, set selCi(v){ selCi=v; },
  D:D, refresh:function(){ renderBars(); styleUnits(); movePlayhead(); },
  rebuild:build, setStatus:setStatus, clipAt:clipAt,
  undoStack:undoStack, redoStack:redoStack,
  movePlayhead:movePlayhead, setPlayhead:function(t){ playhead=t; movePlayhead(); }
};
})();
"""

TIMELINE_JS = r"""
/* 1ページに複数のタイムラインが載る（セグメントごと）。重いので、画面に入ってから組む。
   再生は元音源の <audio id="orig"> を共有し、同時に鳴るのは1つだけにする。 */
(function(){
var EPS=0.01, MINW=0.02;
var audio=document.getElementById('orig');
var active=null;                      /* いま再生中のタイムライン */
var pxPerSec=parseFloat(localStorage.getItem('tl_pps'))||140;
var insts=[];
var hovered=null;   /* マウスが乗っているタイムライン。キー操作はここを最優先 */

function fmtJp(t){
  t=Math.round(t);
  var h=Math.floor(t/3600), m=Math.floor((t%3600)/60), s=t%60;
  return (h?h+'時間':'')+m+'分'+(s<10?'0':'')+s+'秒';
}
function fmtAbs(t){
  var h=Math.floor(t/3600), m=Math.floor((t%3600)/60), s=Math.floor(t%60);
  return (h?h+':':'')+((m<10&&h)?'0':'')+m+':'+(s<10?'0':'')+s;
}

function makeTimeline(root){
  var D=JSON.parse(root.querySelector('script[type="application/json"]').textContent);
  var keeps=complement(D.drops||[]);
  /* 前回の保存がサーバーに届かないまま閉じた/リロードした形跡（dirty）を検知する。
     自動では何も書き換えない。通知とボタンだけ出し、押されたときに限り復元する */
  var hasUnsaved=false;
  try{ hasUnsaved=!!(D.sid && localStorage.getItem('tl_dirty_'+D.sid)
        && JSON.parse(localStorage.getItem('tl_journal_'+D.sid)||'[]').length); }catch(e){}
  var undoStack=[], redoStack=[], playhead=D.segStart, selKi=-1;
  var rows=[], laneW=0, built=false, saveTimer=null;
  var dragging=null, pendingDrag=null;
  var host=root.querySelector('.tlrows');
  var elTime=root.querySelector('.tltime'), elKeep=root.querySelector('.tlkeep');
  var elStat=root.querySelector('.tlstat'), elZoom=root.querySelector('.tlzoom');
  var elBtn=root.querySelector('.tlplay');

  function complement(drops){
    var ks=[], t=D.segStart;
    (drops||[]).map(function(d){return [Math.max(D.segStart,+d[0]),Math.min(D.segEnd,+d[1])];})
      .filter(function(d){return d[1]-d[0]>EPS;})
      .sort(function(a,b){return a[0]-b[0];})
      .forEach(function(d){ if(d[0]-t>EPS) ks.push([t,d[0]]); t=Math.max(t,d[1]); });
    if(D.segEnd-t>EPS) ks.push([t,D.segEnd]);
    return ks;
  }
  function currentDrops(){
    var out=[], t=D.segStart;
    keeps.slice().sort(function(a,b){return a[0]-b[0];}).forEach(function(k){
      if(k[0]-t>EPS) out.push([+t.toFixed(3),+k[0].toFixed(3)]);
      t=Math.max(t,k[1]);
    });
    if(D.segEnd-t>EPS) out.push([+t.toFixed(3),+D.segEnd.toFixed(3)]);
    return out;
  }
  function fmt(t){
    t=Math.max(0,t-D.segStart);
    var m=Math.floor(t/60), s=t-m*60;
    return m+':'+(s<10?'0':'')+s.toFixed(2);
  }
  function X(R,t){ return (t-R.t0)*pxPerSec; }
  function T(R,x){ return R.t0 + x/pxPerSec; }
  function inKeep(t){ return keeps.some(function(k){return k[0]<=t&&t<k[1];}); }

  /* 象徴的セリフの単語番号を集合にしておく */
  var hlSet=(function(){ var st={}; (D.hl||[]).forEach(function(r){
    for(var i=r[0];i<=r[1];i++) st[i]=1; }); return st; })();

  function build(){
    host.innerHTML=''; rows=[];
    var probe=document.createElement('div'); probe.className='lane';
    host.appendChild(probe); laneW=probe.clientWidth||800; host.removeChild(probe);
    var rowSec=laneW/pxPerSec;
    var nRows=Math.ceil((D.segEnd-D.segStart)/rowSec);
    if(elZoom) elZoom.textContent=pxPerSec.toFixed(0)+'px/秒・1行'+rowSec.toFixed(1)+'秒';
    var wi=0;
    for(var r=0;r<nRows;r++){
      var t0=D.segStart+r*rowSec, t1=Math.min(D.segEnd,t0+rowSec);
      var row=document.createElement('div'); row.className='row';
      var lane=document.createElement('div'); lane.className='lane'; row.appendChild(lane);
      var strip=document.createElement('div'); strip.className='strip'; lane.appendChild(strip);
      var lastRight=-1e9, lastTsRight=-1e9, els=[], prevEnd=null, prevSpk=null;
      while(wi<D.words.length && D.words[wi].s < t1){
        var w=D.words[wi];
        if(w.e<=t0){ wi++; continue; }
        var x=(w.s-t0)*pxPerSec;
        if(x<lastRight) x=lastRight;
        /* 上の行に、発話ブロックの頭ならタイムスタンプ、
           会話相手のターンが始まったら「Speaker N」を出す。
           同じ位置に両方来ることがあるので、置いた幅を覚えて重なりを避ける。 */
        var newBlock=(prevEnd===null || w.s-prevEnd>=0.8);
        var newSpk=(w.p!==prevSpk);
        if(newBlock && x>=lastTsRight){
          var ts=document.createElement('div'); ts.className='ts2';
          ts.textContent=fmtAbs(w.s); ts.style.left=x+'px';
          lane.appendChild(ts); lastTsRight=x+ts.offsetWidth+8;
        }
        if(newSpk && w.p && w.p!==D.mainSpk){
          var sc=' s'+(w.p<=8?w.p:'x');
          var sl=document.createElement('div'); sl.className='spk'+sc;
          sl.textContent='Speaker '+w.p;
          sl.style.left=Math.max(x,lastTsRight)+'px';
          lane.appendChild(sl); lastTsRight=Math.max(x,lastTsRight)+sl.offsetWidth+8;
        }
        var el=document.createElement('span');
        el.className='w'+((w.p&&w.p!==D.mainSpk)?(' s'+(w.p<=8?w.p:'x')):'')
                        +(hlSet[wi]?' hl':'');
        el.textContent=w.t; el.style.left=x+'px';
        el.dataset.s=w.s; el.dataset.e=w.e;
        lane.appendChild(el); els.push(el);
        lastRight=x+el.offsetWidth; prevEnd=w.e; prevSpk=w.p; wi++;
      }
      host.appendChild(row);
      var R={t0:t0,t1:t1,strip:strip,els:els,bars:[]};
      rows.push(R); bindStrip(R);
    }
    built=true;
    renderBars(); styleWords(); movePlayhead();
  }
  function renderBars(){
    rows.forEach(function(R){
      R.strip.innerHTML=''; R.bars=[];
      /* 未決カットの帯とラベルは strip の外（lane）に置くので、ここで消さないと
         「残す」を押しても推奨マークが画面に残り続ける */
      R.strip.parentNode.querySelectorAll('.pend,.pcid').forEach(function(n){ n.remove(); });
      var W=X(R,R.t1);
      /* 1) 土台は発話色で全幅。バーは切っても消さない */
      var base=document.createElement('div'); base.className='barbase';
      base.style.left='0px'; base.style.width=W+'px'; R.strip.appendChild(base);
      /* 2) VAD の無音を黄で塗る */
      D.silence.forEach(function(sv){
        var a=Math.max(sv[0],R.t0), b=Math.min(sv[1],R.t1);
        if(b-a<=0) return;
        var d=document.createElement('div'); d.className='sil';
        d.style.left=X(R,a)+'px'; d.style.width=Math.max(1,X(R,b)-X(R,a))+'px';
        R.strip.appendChild(d);
      });
      /* 3) カット済み（keeps の隙間）を黒で塗る。黒が最優先 */
      var t=D.segStart;
      var ks=keeps.slice().sort(function(a,b){return a[0]-b[0];});
      var cuts=[];
      ks.forEach(function(k){ if(k[0]-t>EPS) cuts.push([t,k[0]]); t=Math.max(t,k[1]); });
      if(D.segEnd-t>EPS) cuts.push([t,D.segEnd]);
      cuts.forEach(function(c){
        var a=Math.max(c[0],R.t0), b=Math.min(c[1],R.t1);
        if(b-a<=0) return;
        var d=document.createElement('div'); d.className='cutz';
        d.style.left=X(R,a)+'px'; d.style.width=Math.max(1,X(R,b)-X(R,a))+'px';
        R.strip.appendChild(d);
      });
      /* 4) スプリット位置に縦線を出す。分割しただけでは両側とも「残す」なので
         線が無いと何も起きていないように見え、端を掴むこともできない。 */
      for(var i2=0;i2+1<ks.length;i2++){
        if(Math.abs(ks[i2][1]-ks[i2+1][0])>EPS) continue;
        var bt=ks[i2][1];
        if(bt<R.t0||bt>R.t1) continue;
        var sp2=document.createElement('div'); sp2.className='splitline';
        sp2.style.left=(X(R,bt)-6)+'px'; R.strip.appendChild(sp2);
      }
      /* 5) ドラッグできる端（keeps の境界）を記録。選択中は枠で示す */
      ks.forEach(function(k){
        var ki=keeps.indexOf(k);
        if(k[1]<=R.t0||k[0]>=R.t1) return;
        var x0=X(R,Math.max(k[0],R.t0)), x1=X(R,Math.min(k[1],R.t1));
        if(ki===selKi){
          var sel=document.createElement('div'); sel.className='edge on';
          sel.style.left=x0+'px'; sel.style.width=Math.max(1,x1-x0)+'px';
          sel.style.background='transparent';
          sel.style.boxShadow='inset 0 0 0 2px #2563eb';
          R.strip.appendChild(sel);
        }
        R.bars.push({ki:ki,x0:x0,x1:x1,edgeS:(k[0]>=R.t0-1e-9),edgeE:(k[1]<=R.t1+1e-9)});
      });
      /* 未決のカット候補をバーの下に細い帯で出す。押すとタイムライン上で黒くなる */
      (D.pend||[]).forEach(function(pd){
        if(pd.done) return;
        var a=Math.max(pd.a,R.t0), b=Math.min(pd.b,R.t1);
        if(b-a<=0) return;
        var pb=document.createElement('div'); pb.className='pend '+pd.cat;
        pb.style.left=X(R,a)+'px'; pb.style.width=Math.max(2,X(R,b)-X(R,a))+'px';
        pb.title=pd.cid+' '+pd.why;
        pb.onclick=function(ev){ ev.stopPropagation(); openPend(pd, ev.clientX, ev.clientY); };
        R.strip.parentNode.appendChild(pb);
        /* 理由を帯の直下に出す（旧 render_transcript の注釈行と同じ考え方）。
           C番号はボタンがあるので出さない。 */
        if(pd.a>=R.t0&&pd.a<R.t1){
          var CAT={gpt:'カット推奨',speaker:'会話相手',fact:'事実確認',other:'その他'};
          var lb=document.createElement('div'); lb.className='pcid '+pd.cat;
          lb.textContent=(CAT[pd.cat]||pd.cat)+(pd.why?('：'+pd.why):'');
          lb.style.left=X(R,pd.a)+'px';
          R.strip.parentNode.appendChild(lb);
        }
      });
      R.edge=document.createElement('div'); R.edge.className='edge'; R.strip.appendChild(R.edge);
      R.hover=document.createElement('div'); R.hover.className='hoverline'; R.strip.appendChild(R.hover);
      R.play=document.createElement('div'); R.play.className='playline'; R.strip.appendChild(R.play);
      R.tlab=document.createElement('div'); R.tlab.className='tlabel'; R.strip.appendChild(R.tlab);
    });
    showDragEdge();
  }
  function showDragEdge(){
    rows.forEach(function(R){ if(R.edge) R.edge.classList.remove('on'); });
    if(!dragging) return;
    var k=keeps[dragging.ki]; if(!k) return;
    var t=dragging.which===0?k[0]:k[1];
    var R=rows.find(function(R){return R.t0<=t&&t<=R.t1;});
    if(R&&R.edge){ R.edge.style.left=X(R,t)+'px'; R.edge.style.width='2px';
      R.edge.style.background='#e8e8e8'; R.edge.classList.add('on'); }
  }
  function styleWords(){
    rows.forEach(function(R){
      R.els.forEach(function(el){
        var mid=(+el.dataset.s + +el.dataset.e)/2;
        el.classList.toggle('cut', !inKeep(mid));
      });
    });
    var kept=keeps.reduce(function(a,k){return a+(k[1]-k[0]);},0);
    var m=Math.floor(kept/60), s=Math.round(kept-m*60);
    if(elKeep) elKeep.textContent='残り尺 '+m+'分'+(s<10?'0':'')+s+'秒';
    /* セグメント見出しの「元→編集後」もライブ更新する（静的なままだとバグに見える） */
    var hd=document.getElementById('dur'+D.index);
    if(hd){ var g=D.segEnd-D.segStart;
      hd.textContent=(g-kept>1)?(fmtJp(g)+'→'+fmtJp(kept)):fmtJp(g); }
  }
  function movePlayhead(){
    rows.forEach(function(R){ if(R.play) R.play.style.display='none'; });
    var R=rows.find(function(R){return R.t0<=playhead&&playhead<R.t1;})||rows[rows.length-1];
    if(R&&R.play){ R.play.style.left=X(R,playhead)+'px'; R.play.style.display='block'; }
    if(elTime) elTime.textContent=fmt(playhead);
  }
  function highlight(t){
    root.querySelectorAll('.w.playing').forEach(function(x){x.classList.remove('playing');});
    var R=rows.find(function(R){return R.t0<=t&&t<R.t1;});
    if(!R) return;
    var best=null;
    R.els.forEach(function(el){ if(+el.dataset.s<=t+0.01&&(!best||+el.dataset.s>+best.dataset.s)) best=el; });
    if(best&&t-(+best.dataset.s)<10) best.classList.add('playing');
  }

  var pbox=null;
  var hoverT=null;   /* マウスが行の上にあるときの時刻。⌘D はここで割る */
  function closePend(){ if(pbox){ pbox.remove(); pbox=null; } }
  function openCtx(R,t,cx,cy){
    /* 右クリックメニュー。即実行は誤操作しやすい（オーナー指示・2026-08-05）ので
       メニューから選んで実行する */
    closePend();
    pbox=document.createElement('div'); pbox.className='pbox';
    pbox.style.left=Math.min(cx,window.innerWidth-260)+'px';
    pbox.style.top=Math.min(cy+8,window.innerHeight-140)+'px';
    pbox.innerHTML='<b>'+fmtAbs(t)+'</b>'+
      '<div class="btns"><button data-a="split">ここでスプリット</button>'+
      '<button data-a="play">ここから再生</button>'+
      '<button data-a="close">閉じる</button></div>';
    document.body.appendChild(pbox);
    pbox.querySelectorAll('button').forEach(function(b){
      b.onclick=function(){
        var act=b.dataset.a; closePend();
        if(act==='split'){ playhead=t; movePlayhead(); splitAt(t); }
        else if(act==='play'){ selectInst(api); playhead=t; movePlayhead(); play(); }
      };
    });
  }
  function openPend(pd,cx,cy){
    closePend();
    var CAT={gpt:'カット推奨',speaker:'会話相手',fact:'事実確認',other:'その他'};
    pbox=document.createElement('div'); pbox.className='pbox';
    pbox.style.left=Math.min(cx,window.innerWidth-440)+'px';
    pbox.style.top=Math.min(cy+12,window.innerHeight-200)+'px';
    var sec=Math.round(pd.b-pd.a);
    pbox.innerHTML='<b>'+pd.cid+'　'+(CAT[pd.cat]||pd.cat)+'</b>　'+sec+'秒<br>'+
      esc(pd.why)+(pd.q?'<br><span class="q">「'+esc(pd.q)+'」</span>':'')+
      '<div class="btns"><button data-a="cut">カットする</button>'+
      '<button data-a="keep">残す</button>'+
      '<button data-a="close">閉じる</button></div>';
    document.body.appendChild(pbox);
    pbox.querySelectorAll('button').forEach(function(b){
      b.onclick=function(){ var act=b.dataset.a;
        if(act==='close'){ closePend(); return; }
        decidePend(pd, act); closePend(); };
    });
  }
  function esc(t){ return String(t).replace(/[&<>]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]; }); }
  function decidePend(pd, action){
    pd.done=true;
    if(action==='cut'){
      pushUndo();
      lastOp='pend-cut:'+pd.cid;
      dropRange(pd.a, pd.b);
      keeps.sort(function(a,b){return a[0]-b[0];});
      selKi=-1; afterEdit();
      setStatus(pd.cid+' をカットしました（端をドラッグして調整できます）');
    }else{
      renderBars();
      setStatus(pd.cid+' は残すことにしました');
    }
    /* cut_decisions.json の status だけ更新する。drops はタイムライン側が
       /edit_save で書くので、ここで両方書くと競合する。 */
    fetch(window.APP+'/decide?id='+encodeURIComponent(D.id)+'&cid='+encodeURIComponent(pd.cid)
          +'&action='+action+'&status_only=1');
  }
  var lastOp='';
  function pushUndo(){ undoStack.push(JSON.stringify(keeps)); if(undoStack.length>200)undoStack.shift(); redoStack=[]; }
  function afterEdit(){ renderBars(); styleWords(); movePlayhead(); scheduleSave(); }
  function setStatus(s){ if(elStat) elStat.textContent=s; }
  function journalNow(){
    /* 操作の瞬間に、手元のローカルへ同期的に履歴を書く。これが唯一の必須処理。
       サーバー送信は後追いで、失敗しても履歴は既にここに残っている */
    try{ var k='tl_journal_'+D.sid, j=JSON.parse(localStorage.getItem(k)||'[]');
         j.push({at:Date.now(),op:lastOp,drops:currentDrops()});
         try{ localStorage.setItem(k,JSON.stringify(j)); }
         catch(qe){ j=j.slice(Math.floor(j.length/2));
                    try{ localStorage.setItem(k,JSON.stringify(j)); }catch(e2){} }
         localStorage.setItem('tl_dirty_'+D.sid,'1');
    }catch(e){}
  }
  function scheduleSave(){ journalNow(); setStatus('未保存'); clearTimeout(saveTimer); saveTimer=setTimeout(doSave,0); }
  function doSave(){
    setStatus('保存中…');
    var rec={id:D.id,index:D.index,sid:D.sid,segStart:D.segStart,segEnd:D.segEnd,
             op:lastOp,drops:currentDrops()};
    lastOp='';
    fetch(window.APP+'/edit_save',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(rec)})
    .then(function(r){
      if(r.ok){ setStatus('保存済み'); try{ localStorage.removeItem('tl_dirty_'+D.sid); }catch(e){} }
      else{ setStatus('保存失敗（3秒後に再送します）'); clearTimeout(saveTimer); saveTimer=setTimeout(doSave,3000); }
    })
    .catch(function(){ setStatus('サーバーに接続できません（3秒後に再送します）');
      clearTimeout(saveTimer); saveTimer=setTimeout(doSave,3000); });
  }
  function splitAt(t){
    var ki=keeps.findIndex(function(k){return t>k[0]+MINW&&t<k[1]-MINW;});
    if(ki<0){
      setStatus('その位置では分割できません（バーの上をクリックして位置を決めてください）');
      return;
    }
    pushUndo(); var k=keeps[ki];
    lastOp='split@'+t.toFixed(1);
    keeps.splice(ki,1,[k[0],t],[t,k[1]]); selKi=-1; afterEdit();
    setStatus('分割しました（端をドラッグするとカットできます）');
  }
  function dropRange(a,b){
    var ki=keeps.findIndex(function(k){return k[0]<b-EPS&&a<k[1]-EPS;});
    if(ki<0) return false;
    var k=keeps[ki], parts=[];
    if(a-k[0]>MINW) parts.push([k[0],Math.max(a,k[0])]);
    if(k[1]-b>MINW) parts.push([Math.min(b,k[1]),k[1]]);
    keeps.splice.apply(keeps,[ki,1].concat(parts));
    return true;
  }
  function dropAllSilence(minSec){
    var t=D.silence.filter(function(sv){
      return sv[1]-sv[0]>=minSec && keeps.some(function(k){return k[0]<sv[1]-EPS&&sv[0]<k[1]-EPS;});
    });
    if(!t.length){ setStatus(minSec+'秒以上の無音はありません'); return; }
    pushUndo();
    t.slice().reverse().forEach(function(sv){ dropRange(sv[0],sv[1]); });
    keeps.sort(function(a,b){return a[0]-b[0];});
    selKi=-1; afterEdit(); setStatus(t.length+'箇所の無音を落としました');
  }

  /* ---- 再生。元音源を共有するので、鳴らす前に他を止める ---- */
  function tick(){
    if(active!==api) return;
    var t=audio.currentTime;
    if(t>=D.segEnd){ stop(); return; }
    if(!inKeep(t)){
      var nk=keeps.find(function(k){return k[0]>t;});
      if(!nk){ stop(); return; }
      audio.currentTime=nk[0]+0.001;
    }
    playhead=audio.currentTime; movePlayhead(); highlight(playhead);
    requestAnimationFrame(tick);
  }
  function applyRate(){ try{ audio.playbackRate=parseFloat(localStorage.getItem('tl_rate')||'1'); }catch(e){} }
  function play(){
    applyRate();
    if(!audio){ setStatus('元音源がありません'); return; }
    if(active&&active!==api) active.stop();
    if(!inKeep(playhead)){
      var nk=keeps.find(function(k){return k[0]>=playhead;});
      playhead=nk?nk[0]:(keeps[0]?keeps[0][0]:D.segStart);
    }
    var go=function(){
      try{ audio.currentTime=playhead; }
      catch(err){ setStatus('シークできません: '+err.name); return; }
      audio.play().then(function(){ active=api; if(elBtn) elBtn.textContent='∎ 停止';
        setStatus('再生中'); requestAnimationFrame(tick); })
        .catch(function(err){ setStatus('再生できません: '+err.name+' '+(err.message||'')); });
    };
    /* preload=metadata でも読み終わる前に currentTime を触ると失敗するので待つ */
    if(audio.readyState>=1){ go(); }
    else{
      setStatus('音源を読み込み中…');
      audio.addEventListener('loadedmetadata', go, {once:true});
      audio.addEventListener('error', function(){
        var c=audio.error&&audio.error.code;
        setStatus('音源を読み込めません（code '+c+'）。ブラウザが対応しない形式かもしれません');
      }, {once:true});
      audio.load();
    }
  }
  function stop(){
    if(audio) audio.pause();
    if(active===api) active=null;
    if(elBtn) elBtn.textContent='▶ 再生';
    root.querySelectorAll('.w.playing').forEach(function(x){x.classList.remove('playing');});
  }

  function edgesAt(R,x){
    var out=[];
    R.bars.forEach(function(b){
      if(b.edgeS&&Math.abs(x-b.x0)<8) out.push({ki:b.ki,which:0});
      if(b.edgeE&&Math.abs(x-b.x1)<8) out.push({ki:b.ki,which:1});
    });
    return out;
  }
  function bindStrip(R){
    R.strip.addEventListener('mousemove',function(ev){
      if(dragging||pendingDrag) return;
      var x=ev.clientX-R.strip.getBoundingClientRect().left;
      R.hover.style.left=x+'px'; R.hover.style.display='block';
      R.tlab.style.left=(x+4)+'px'; R.tlab.style.display='block';
      R.tlab.textContent=fmt(T(R,x));
      R.strip.style.cursor=edgesAt(R,x).length?'ew-resize':'crosshair';
    });
    R.strip.addEventListener('mouseleave',function(){
      R.hover.style.display='none'; R.tlab.style.display='none';
    });
    var lane=R.strip.parentNode;
    /* 行のどこ（文字の上でも）にマウスがあっても、その時刻を ⌘D 用に覚えておく */
    lane.addEventListener('mousemove',function(ev){
      hoverT=T(R, ev.clientX-R.strip.getBoundingClientRect().left);
      hovered=api;
    });
    lane.addEventListener('mouseleave',function(){ hoverT=null;
      if(hovered===api) hovered=null; });
    /* 右クリック＝メニュー（ここでスプリット／ここから再生）。文字の上でも効く */
    lane.addEventListener('contextmenu',function(ev){
      ev.preventDefault();
      selectInst(api);
      var t=T(R, ev.clientX-R.strip.getBoundingClientRect().left);
      openCtx(R, t, ev.clientX, ev.clientY);
    });
    R.strip.addEventListener('dblclick',function(ev){
      /* 黄（無音）をダブルクリック＝その無音だけ落とす */
      var x=ev.clientX-R.strip.getBoundingClientRect().left, t=T(R,x);
      var sv=D.silence.find(function(v){return v[0]<=t&&t<v[1];});
      if(sv&&R.bars.some(function(b){return x>=b.x0&&x<=b.x1;})){
        ev.preventDefault(); pushUndo(); lastOp='dropSilence@'+sv[0].toFixed(1); dropRange(sv[0],sv[1]); selKi=-1; afterEdit();
      }
    });
    R.strip.addEventListener('mousedown',function(ev){
      ev.preventDefault();
      selectInst(api);
      var x=ev.clientX-R.strip.getBoundingClientRect().left;
      var cand=edgesAt(R,x);
      if(cand.length===1){ pushUndo(); dragging={R:R,ki:cand[0].ki,which:cand[0].which}; }
      else if(cand.length>1){ pendingDrag={R:R,cand:cand,x0:ev.clientX}; }
      else{
        playhead=T(R,x);
        var hit=R.bars.find(function(b){return x>=b.x0&&x<=b.x1;});
        selKi=hit?hit.ki:-1;
        renderBars(); movePlayhead();
        if(active===api) audio.currentTime=playhead;
      }
    });
  }
  document.addEventListener('mousemove',function(ev){
    if(pendingDrag){
      var dx=ev.clientX-pendingDrag.x0;
      if(Math.abs(dx)>=3){
        var pick=null;
        pendingDrag.cand.forEach(function(c){
          if(dx>0&&c.which===0) pick=c;
          if(dx<0&&c.which===1&&!pick) pick=c;
        });
        pick=pick||pendingDrag.cand[0];
        pushUndo(); dragging={R:pendingDrag.R,ki:pick.ki,which:pick.which}; pendingDrag=null;
      }
      return;
    }
    if(!dragging) return;
    var R=dragging.R;
    var t=T(R, ev.clientX-R.strip.getBoundingClientRect().left);
    var k=keeps[dragging.ki];
    if(dragging.which===0){
      var lo=dragging.ki>0?keeps[dragging.ki-1][1]:D.segStart;
      k[0]=Math.min(Math.max(t,lo),k[1]-MINW);
    }else{
      var hi=dragging.ki<keeps.length-1?keeps[dragging.ki+1][0]:D.segEnd;
      k[1]=Math.max(Math.min(t,hi),k[0]+MINW);
    }
    renderBars(); styleWords(); movePlayhead();
  });
  document.addEventListener('mouseup',function(){
    if(pendingDrag) pendingDrag=null;
    if(dragging){ dragging=null; lastOp='trim'; scheduleSave(); }
  });
  host.addEventListener('click',function(ev){
    var el=ev.target.closest('.w'); if(!el) return;
    selectInst(api);
    playhead=+el.dataset.s; movePlayhead();
    if(active===api) audio.currentTime=playhead;
  });

  if(elBtn) elBtn.onclick=function(){ selectInst(api); (active===api)?stop():play(); };
  var zi=root.querySelector('.tlzin'), zo=root.querySelector('.tlzout');
  if(zi) zi.onclick=function(){ setZoomAll(pxPerSec*1.4); };
  if(zo) zo.onclick=function(){ setZoomAll(pxPerSec/1.4); };
  /* 「無音を一括で落とす」ボタンは廃止（オーナー指示・2026-08-05。
     一括操作は編集を全部飛ばす危険があるため。黄帯のダブルクリックで1箇所ずつは残す） */
  var sp=root.querySelector('.tlspeed');
  if(sp){
    sp.value=localStorage.getItem('tl_rate')||'1';
    sp.onchange=function(){ localStorage.setItem('tl_rate',sp.value);
      if(audio) audio.playbackRate=parseFloat(sp.value);
      /* 他のタイムラインのプルダウン表示も同期 */
      document.querySelectorAll('.tlspeed').forEach(function(s){ s.value=sp.value; }); };
  }
  var ub=root.querySelector('.tlundo'), rb=root.querySelector('.tlredo');
  if(ub) ub.onclick=function(){ selectInst(api); api.undo(); };
  if(rb) rb.onclick=function(){ selectInst(api); api.redo(); };

  if(hasUnsaved){
    setStatus('未保存の編集があります');
    var rb=document.createElement('button');
    rb.textContent='未保存の編集を復元';
    rb.onclick=function(){
      try{
        var jj=JSON.parse(localStorage.getItem('tl_journal_'+D.sid)||'[]');
        if(!jj.length){ setStatus('復元できる編集がありません'); return; }
        pushUndo(); lastOp='restore-unsaved';
        keeps=complement(jj[jj.length-1].drops||[]);
        selKi=-1; afterEdit(); rb.remove();
      }catch(e){ setStatus('復元に失敗しました'); }
    };
    var bar=root.querySelector('.tlbar');
    if(bar) bar.appendChild(rb);
  }
  var api={ root:root, sid:D.sid,
            state:function(){ return {id:D.id, sid:D.sid, index:D.index,
              segStart:D.segStart, segEnd:D.segEnd, drops:currentDrops()}; },
            build:build, isBuilt:function(){return built;}, rebuild:function(){ if(built) build(); },
            play:play, stop:stop,
            /* ⌘D: マウスが行の上にあればその位置、なければ再生位置で割る */
            splitAt:function(){ var t=(hoverT!=null)?hoverT:playhead;
              playhead=t; movePlayhead(); splitAt(t); },
            undo:function(){ if(!undoStack.length)return; redoStack.push(JSON.stringify(keeps));
              keeps=JSON.parse(undoStack.pop()); selKi=-1; lastOp='undo'; afterEdit(); },
            redo:function(){ if(!redoStack.length)return; undoStack.push(JSON.stringify(keeps));
              keeps=JSON.parse(redoStack.pop()); selKi=-1; lastOp='redo'; afterEdit(); },
            delSel:function(){ if(selKi<0) return; pushUndo(); lastOp='delete'; keeps.splice(selKi,1); selKi=-1; afterEdit(); },
            dropSil:function(){ dropAllSilence(1.0); } };
  return api;
}

var focused=null;
function selectInst(a){
  focused=a;
  insts.forEach(function(x){ x.root.classList.toggle('tlfocus', x===a); });
}
/* クリックしていなくても Space が効くように、画面の中央に一番近いものを対象にする。
   これが無いと focused も active も null のままで、キーが素通りしていた。 */
function pickVisible(){
  var cy=window.innerHeight/2, best=null, bd=1e9;
  insts.forEach(function(a){
    var r=a.root.getBoundingClientRect();
    if(r.bottom<0||r.top>window.innerHeight) return;
    var d=Math.abs((r.top+r.bottom)/2-cy);
    if(d<bd){ bd=d; best=a; }
  });
  return best;
}
function setZoomAll(v){
  pxPerSec=Math.max(20,Math.min(600,v));
  localStorage.setItem('tl_pps',pxPerSec);
  insts.forEach(function(a){ a.rebuild(); });
}

document.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
  /* ⌘D はタイムラインが拾えない場合でも先に抑止する。
     さもないとブラウザのブックマーク追加が開き「効かない」ように見える */
  if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='d') e.preventDefault();
  var a=hovered||active||focused||pickVisible();
  if(!a){ return; }
  if(a!==focused) selectInst(a);
  if(!a.isBuilt()) a.build();
  if(e.code==='Space'){ e.preventDefault(); (active===a)?a.stop():a.play(); }
  else if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='d'){ e.preventDefault(); a.splitAt(); }
  else if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='z'){ e.preventDefault(); e.shiftKey?a.redo():a.undo(); }
  else if((e.metaKey||e.ctrlKey)&&(e.key==='='||e.key==='+')){ e.preventDefault(); setZoomAll(pxPerSec*1.4); }
  else if((e.metaKey||e.ctrlKey)&&e.key==='-'){ e.preventDefault(); setZoomAll(pxPerSec/1.4); }
  else if(e.key==='Delete'||e.key==='Backspace'){ e.preventDefault(); a.delSel(); }
});

/* 画面に入ってから組む。7セグメントぶんの単語を最初に全部DOM化すると重いため */
document.querySelectorAll('.tl').forEach(function(root){
  var a=makeTimeline(root);
  insts.push(a);
  var io=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(en.isIntersecting&&!a.isBuilt()){ a.build(); io.disconnect(); }
    });
  },{rootMargin:'300px'});
  io.observe(root);
});
/* 書き出しは「ブラウザが今表示している状態」をそのまま使う（オーナー指示 2026-08-08。
   サーバー保存値を参照すると、見ているものと書き出されるものがズレる余地が残るため） */
window.tlState=function(sid){
  for(var i=0;i<insts.length;i++){ if(insts[i].sid===sid) return insts[i].state(); }
  return null;
};
var rsz=null;
window.addEventListener('resize',function(){
  clearTimeout(rsz);
  rsz=setTimeout(function(){ insts.forEach(function(a){ a.rebuild(); }); },200);
});
})();
"""


_QPUNCT = set(" 　、。，．・…！？!?「」『』（）()［］[]〈〉《》\"'\n\t")


def _quote_ranges(words, quotes):
    """highlight_quotes が本文のどの単語範囲にあたるかを返す（[[開始i, 終了i], ...]）。
    GPT/Claude の引用は表記が微妙に違うので、句読点を除いた文字列で最長一致を探す。"""
    from difflib import SequenceMatcher
    if not quotes or not words:
        return []
    idx, buf = [], []
    for i, w in enumerate(words):
        for ch in w["t"]:
            if ch in _QPUNCT:
                continue
            buf.append(ch)
            idx.append(i)
    hay = "".join(buf)
    out = []
    for q in quotes:
        qn = "".join(c for c in str(q) if c not in _QPUNCT)
        if len(qn) < 6:
            continue
        sm = SequenceMatcher(None, hay, qn, autojunk=False)
        m = sm.find_longest_match(0, len(hay), 0, len(qn))
        if m.size < 6:
            continue
        st = max(0, m.a - m.b)
        en = min(len(hay), st + len(qn))
        if en <= st:
            continue
        if SequenceMatcher(None, hay[st:en], qn, autojunk=False).ratio() < 0.6:
            continue
        out.append([idx[st], idx[en - 1]])
    return out


def timeline_block(idv, sg, tsegments, silence, main_spk=1, cutdecs=None, quotes=None):
    """文字起こしの場所に置くタイムライン。別ページは作らない（オーナー指示・2026-08-05）。"""
    idx = sg.get("index")
    s, e = float(sg["start_sec"]), float(sg["end_sec"])
    words = []
    for tseg in tsegments:
        for w in (tseg.get("words") or []):
            st, en = w.get("start"), w.get("end")
            if st is None or en is None or not (s <= st < e):
                continue
            tok = (w.get("word") or "").strip()
            if not tok:
                continue
            spk = w.get("speaker") or tseg.get("speaker") or ""
            try:
                pno = int(str(spk).split("_")[-1])
            except ValueError:
                pno = 0
            words.append({"t": tok, "s": round(float(st), 3),
                          "e": round(float(en), 3), "p": pno})
    words.sort(key=lambda w: w["s"])
    sil = [[max(a, s), min(b, e)] for a, b in silence if b > s and a < e]
    sil = [[round(a, 3), round(b, 3)] for a, b in sil if b - a > 0.01]

    # 未決のカット候補（D-013）。押したらタイムライン上で黒くなり、端をドラッグして調整できる。
    pend = []
    for cd in (cutdecs or []):
        if cd.get("status") != "pending":
            continue
        a, b = float(cd["start_sec"]), float(cd["end_sec"])
        if b <= s or a >= e:
            continue
        cat = cd.get("category") or "gpt"
        pend.append({"cid": cd.get("cid", ""), "a": round(max(a, s), 3), "b": round(min(b, e), 3),
                     "cat": cat if cat in ("gpt", "speaker", "fact") else "other",
                     "why": (cd.get("reason") or cd.get("note") or ""),
                     "q": cd.get("quote") or ""})
    pend.sort(key=lambda x: x["a"])

    # 象徴的セリフ（highlight_quotes）。本文中の該当語を太字にするため、
    # 文字列一致で単語インデックスの範囲を求めておく（表示は太字のみ・色は付けない）。
    hl = _quote_ranges(words, quotes or [])

    data = json.dumps({"id": idv, "index": idx, "sid": sg.get("sid") or "", "segStart": s, "segEnd": e,
                       "drops": sg.get("drops") or [], "words": words, "silence": sil,
                       "mainSpk": main_spk, "pend": pend, "hl": hl},
                      ensure_ascii=False).replace("</", "<\\/")
    vad_note = ("青緑＝発話・黄＝VADが検出した無音（黄をダブルクリックでその無音だけ落ちる）"
                if sil else "VAD 未実行のため無音の塗り分けなし（python scripts/detect_vad.py &lt;ID&gt;）")
    return (
        f"<div class='tl' id='tl{idx}'>"
        "<div class='tlbar'>"
        "<button class='tlplay'>▶ 再生</button>"
        "<span class='tltime'>0:00.00</span>"
        "<span class='tlkeep'></span>"
        "<button class='tlzout'>−</button><button class='tlzin'>＋</button>"
        "<select class='tlspeed'><option value='1'>1x</option>"
        "<option value='1.35'>1.35x</option><option value='1.5'>1.5x</option></select>"
        "<span class='tlzoom'></span>"
        "<button class='tlundo'>↩ 元に戻す</button><button class='tlredo'>↪ やり直す</button>"
        "<span class='tlstat'>保存済み</span>"
        "</div>"
        f"<div class='tlhelp'>文字は時間軸上の位置に置いてあるので、文字間の空白がそのまま無音の長さです。"
        f"バーは常に1本の帯で、{vad_note}、黒＝カット済み。"
        "Space 再生（カット部はスキップ）・<b>⌘D＝マウス位置でスプリット</b>・"
        "右クリック＝メニュー（スプリット/再生）・端をドラッグでトリム・"
        "クリックで選択して Delete で削除・⌘Z 取り消し・⌘± ズーム。自動保存されます。</div>"
        f"<div class='tlrows'><div class='tlwait'>スクロールすると組み上がります（単語 {len(words)}）…</div></div>"
        f"<script type='application/json'>{data}</script>"
        "</div>"
    )


def _queue_for_sync(*paths):
    """書いたファイルをコミット対象キューへ追記する（D-52 保存トリガー同期）。
    サーバーの flusher はこの明示リストに載ったファイルだけを git add する。
    手で消した・動かしたファイルはここに載らないので、事故が push されることはない。"""
    import datetime
    try:
        q = os.path.join(DATA_DIR, ".pending_sync.jsonl")
        with open(q, "a", encoding="utf-8") as f:
            for p in paths:
                if not p or not os.path.exists(p):
                    continue
                f.write(json.dumps({"at": datetime.datetime.now().isoformat(timespec="seconds"),
                                    "path": os.path.realpath(p)}, ensure_ascii=False) + "\n")
    except Exception:
        pass  # キューが書けなくても保存は続ける（次の保存で追いつく）


def apply_timeline_save(payload):
    """/edit_save: タイムライン編集の drops を segments.json に保存する。"""
    idv = str(payload.get("id") or "")
    if not idv or "/" in idv or idv.startswith("."):
        return False
    # 受信した保存内容は成否に関わらず全部記録する（復元用の受信箱・2026-08-08）。
    # 古いページの保存が拒否されても、ここに全編集データが残る。
    try:
        import datetime
        inbox = os.path.join(idpaths.edit_dir(os.path.join(DATA_DIR, idv)), "edit_save_journal.jsonl")
        with open(inbox, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.datetime.now().isoformat(timespec="milliseconds"),
                                "payload": payload}, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())   # ここがジャーナルの正本。適用より先に必ずディスクへ書き切る
    except Exception:
        pass
    base = os.path.join(DATA_DIR, idv)
    seg_path = idpaths.find(base, "segments.json")
    if not os.path.isfile(seg_path):
        return False
    try:
        idx = int(payload.get("index"))
    except (TypeError, ValueError):
        return False
    sid = str(payload.get("sid") or "")
    seg = _load_json(seg_path, {})
    changed = False
    for sg in seg.get("segments", []):
        # 対応づけは sid が正（index は細分化・並べ替えで変わるため。2026-08-08）。
        # sid が無い旧データだけ index で引く。
        if sid and sg.get("sid"):
            if sg["sid"] != sid:
                continue
        elif sg.get("index") != idx:
            continue
        # 保存は受け取ったまま書く。切り詰め・範囲外破棄はしない（オーナー指示 2026-08-08。
        # 整形はデータを壊すだけで意味がない。範囲の解釈は表示・書き出し側が読むときに行う）。
        # sid が無い旧ページの index 指定だけは、誤セグメント書き込み防止に区間一致を要求する。
        if not (sid and sg.get("sid") == sid):
            try:
                ps, pe = float(payload.get("segStart")), float(payload.get("segEnd"))
            except (TypeError, ValueError):
                return False
            if abs(ps - float(sg["start_sec"])) > 0.5 or abs(pe - float(sg["end_sec"])) > 0.5:
                return False
        clean = []
        for d in payload.get("drops") or []:
            try:
                a, b = float(d[0]), float(d[1])
            except (TypeError, ValueError, IndexError):
                return False
            if b > a:
                clean.append([round(a, 3), round(b, 3)])
        sg["drops"] = sorted(clean)
        changed = True
    if not changed:
        return False
    _append_history(base, seg_path)
    with open(seg_path, "w", encoding="utf-8") as f:
        json.dump(seg, f, ensure_ascii=False, indent=2)
    _queue_for_sync(seg_path, os.path.join(idpaths.edit_dir(base), "segments_history.jsonl"))
    return True


def _append_history(base, seg_path):
    """segments.json を上書きする前に、直前の内容を履歴へ退避する（保険）。
    edit/segments_history.jsonl に1行1スナップショットで貯める。最新200件だけ残す。"""
    import datetime
    try:
        with open(seg_path, encoding="utf-8") as f:
            prev = f.read()
        hist = os.path.join(idpaths.edit_dir(base), "segments_history.jsonl")
        lines = []
        if os.path.isfile(hist):
            with open(hist, encoding="utf-8") as f:
                lines = f.read().splitlines()
        lines.append(json.dumps({"at": datetime.datetime.now().isoformat(timespec="seconds"),
                                 "segments_json": prev}, ensure_ascii=False))
        with open(hist, "w", encoding="utf-8") as f:
            f.write("\n".join(lines[-200:]) + "\n")
    except Exception:
        pass  # 履歴が書けなくても保存自体は続ける


def esc(s):
    return html.escape(str(s if s is not None else ""))


def fmt_time(sec):
    sec = int(round(sec))
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def page(title, body):
    return (
        "<!doctype html><html lang='ja'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{esc(title)}</title><style>{PAGE_CSS}{TIMELINE_CSS}{CLIP_CSS}</style>"
        # 公開プレフィックス（本番 /podcast・ローカル 空）。JS の fetch はすべてこれ経由
        f"<script>window.APP='{approot()}';document.documentElement.dataset.theme="
        "localStorage.getItem('theme')||'light';</script></head>"
        f"<body><button class='theme-btn' onclick=\"var r=document.documentElement,"
        "t=r.dataset.theme==='dark'?'light':'dark';r.dataset.theme=t;"
        "localStorage.setItem('theme',t);\">dark / light</button>"
        f"{body}"
        "<script>"
        # クリックしてもスクロールはしない
        "function seekTo(id,t){var a=document.getElementById('orig');if(a)a.pause();"
        "var v=document.getElementById(id);if(!v)return;v.currentTime=t;v.play();}"
        # カット済み区間は元音源で再生して内容を確認する
        "function seekOrig(t){document.querySelectorAll('video').forEach(function(v){v.pause();});"
        "var a=document.getElementById('orig');if(!a)return;a.currentTime=t;a.play();}"
        "function decide(cid,action){var idv=new URLSearchParams(location.search).get('id');"
        "fetch(window.APP+'/decide?id='+encodeURIComponent(idv)+'&cid='+cid+'&action='+action)"
        ".then(function(){location.reload();});}"
        # 「この編集で書き出す」: 完了したらそのままダウンロードが落ちてくる
        "function nrToggle(cb){localStorage.setItem('nr_on',cb.checked?'1':'0');"
        "document.querySelectorAll('.nrtoggle').forEach(function(c){c.checked=cb.checked;});}"
        # 本番使用/配信済み: segments.json に保存し、その場で背景色を切り替える
        "function segFlag(field,idx,sid,cb){var idv=new URLSearchParams(location.search).get('id');"
        "fetch(window.APP+'/'+field+'?id='+encodeURIComponent(idv)"
        "+'&sid='+encodeURIComponent(sid)+'&on='+(cb.checked?'1':'0'))"
        ".then(function(r){if(!r.ok){cb.checked=!cb.checked;"
        "document.getElementById('rst'+idx).textContent='保存に失敗しました';return;}"
        "var seg=document.getElementById('seg'+idx);"
        "if(seg)seg.classList.toggle(field,cb.checked);})"
        ".catch(function(){cb.checked=!cb.checked;"
        "document.getElementById('rst'+idx).textContent='サーバーに接続できません';});}"
        "document.addEventListener('DOMContentLoaded',function(){"
        "var on=localStorage.getItem('nr_on')==='1';"
        "document.querySelectorAll('.nrtoggle').forEach(function(c){c.checked=on;});});"
        # 「切り抜きを作成」: 現在の編集状態を凍結して切り抜き編集画面へ（CLIP_PLAN C-1）
        "function clipCreate(sid,idx){var idv=new URLSearchParams(location.search).get('id');"
        "var el=document.getElementById('rst'+idx);el.textContent='凍結中…';"
        "fetch(window.APP+'/clip_create?id='+encodeURIComponent(idv)+'&sid='+encodeURIComponent(sid),"
        "{method:'POST'}).then(function(r){return r.text();}).then(function(t){"
        "if(t.indexOf('ok:')!==0){el.textContent='切り抜きを作成できません: '+t;return;}"
        "location.href=window.APP+'/clip?id='+encodeURIComponent(idv)"
        "+'&key='+encodeURIComponent(t.slice(3));})"
        ".catch(function(){el.textContent='サーバーに接続できません';});}"
        "function renderSeg(sid,idx){var idv=new URLSearchParams(location.search).get('id');"
        "var el=document.getElementById('rst'+idx);"
        "var st=window.tlState?window.tlState(sid):null;"
        "if(!st){el.textContent='タイムラインの状態を取得できません（リロードしてください）';return;}"
        "if(localStorage.getItem('nr_on')==='1')st.denoise=true;"
        "fetch(window.APP+'/render_seg',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify(st)}).then(function(r){return r.text();})"
        ".then(function(st){if(st!=='started'&&st!=='already_running'){el.textContent='開始できません: '+st;return;}"
        "el.textContent='書き出し中…（数分かかります。ページを開いたままで）';"
        "var iv=setInterval(function(){"
        "fetch(window.APP+'/render_status?id='+encodeURIComponent(idv)+'&sid='+encodeURIComponent(sid)).then(function(r){return r.text();})"
        ".then(function(s){if(s.indexOf('running:')===0){el.textContent='書き出し中… '+s.slice(8)+'%';}"
        "else if(s.indexOf('done')===0){clearInterval(iv);"
        "var fn=s.length>5?s.slice(5):'';"
        "if(fn){var a=document.createElement('a');"
        "a.href=window.APP+'/media/'+encodeURIComponent(idv)+'/contents/'+encodeURIComponent(fn);"
        "a.download=fn;document.body.appendChild(a);a.click();a.remove();"
        "el.textContent='完了: '+fn;}else{el.textContent='完了';}}"
        "else if(s.indexOf('failed')===0){clearInterval(iv);"
        "el.textContent='書き出し失敗（generated/render_'+sid+'.log を確認）';}});},2000);});}"
        # 再生中の箇所の背景ハイライト
        "document.addEventListener('timeupdate',function(e){var el=e.target,sel,attr;"
        "if(el.tagName==='VIDEO'){sel=\"[data-v='\"+el.id+\"']\";attr='data-t';}"
        "else if(el.id==='orig'){sel='[data-ot]';attr='data-ot';}else return;"
        "if(el.paused)return;var t=el.currentTime,best=null,bt=-1;"
        "document.querySelectorAll(sel).forEach(function(sp){"
        "var v=parseFloat(sp.getAttribute(attr));if(v<=t+0.01&&v>bt){bt=v;best=sp;}});"
        "document.querySelectorAll('.playing').forEach(function(x){x.classList.remove('playing');});"
        "if(best&&t-bt<90)best.classList.add('playing');},true);"
        "</script>"
        f"<script>{TIMELINE_JS}</script>"
        # 切り抜き編集画面用（#cliptl が無いページでは何もしない）
        f"<script>{CLIP_JS}</script>"
        "</body></html>"
    ).encode("utf-8")


# ---------- データ読み込み ----------
def _load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _main_speaker(tr):
    """最多話者の番号を返す。話者ラベルが無ければ 1 を返す。"""
    import collections
    c = collections.Counter()
    for w in (tr.get("word_segments") or []):
        spk = w.get("speaker")
        if spk:
            c[spk] += 1
    if not c:
        return 1
    try:
        return int(str(c.most_common(1)[0][0]).split("_")[-1])
    except ValueError:
        return 1


def list_ids():
    """data/ 直下の ID をすべて返す（未処理のものも含める）。"""
    out = []
    if not os.path.isdir(DATA_DIR):
        return out
    for name in sorted(os.listdir(DATA_DIR)):
        if name.startswith(".") or name.startswith("_"):
            continue
        if os.path.isdir(os.path.join(DATA_DIR, name)):
            out.append(name)
    return out


def id_status(idv):
    """ID の進み具合を返す (key, ラベル)。区分はオーナー指示 2026-09-17:
    未処理   … 文字起こしがまだ
    未編集   … 文字起こしはできたが、まだ何も編集していない（旧「処理済み」）
    編集中   … 編集に着手した（本番使用のチェックが付くまではずっと編集中）
    編集完了 … いずれかの切り出しに「本番使用」のチェックが付いた（一覧の背景も黄）
    """
    base = os.path.join(DATA_DIR, idv)
    if not os.path.exists(idpaths.find(base, "transcript.json")):
        return "none", "未処理"
    segs = _load_json(idpaths.find(base, "segments.json"), {}).get("segments", [])
    if any(sg.get("delivered") for sg in segs):
        return "sent", "配信済み"
    if any(sg.get("production") for sg in segs):
        return "done", "編集完了"
    cuts = _load_json(idpaths.find(base, "cut_decisions.json"), {}).get("cuts", [])
    decided = sum(1 for c in cuts if c.get("status") in ("cut", "keep"))
    has_drop = any(sg.get("drops") for sg in segs)
    started = has_drop or decided   # カット記録が最低1つ＝編集に着手（オーナー指示 2026-08-09）
    if not segs or not started:
        return "done0", "未編集"
    return "wip", "編集中"


def list_segments(idv):
    cdir = os.path.join(DATA_DIR, idv, "contents")
    if not os.path.isdir(cdir):
        return []
    return sorted(n for n in os.listdir(cdir) if os.path.isdir(os.path.join(cdir, n)))


def seg_dirname(idv, index, title):
    prefix = f"{index:02d}_"
    for n in list_segments(idv):
        if n.startswith(prefix):
            return n
    return None


def seg_audio_names(idv, index):
    """export_audio.py が書く {ID}_{INDEX}_{TITLE}{尺}{yymmddHHMM}.m4a を contents/ 直下から
    新しい順に全部返す（ファイル名でバージョンが分かれる・2026-08-08）。
    macOS はファイル名の Unicode 正規化（NFC/NFD）が混在するので、比較は NFC に揃える。"""
    import unicodedata
    cdir = os.path.join(DATA_DIR, idv, "contents")
    if not os.path.isdir(cdir):
        return []
    prefix = unicodedata.normalize("NFC", f"{idv}_{index}_")
    out = []
    for n in os.listdir(cdir):
        nn = unicodedata.normalize("NFC", n)
        if nn.startswith(prefix) and nn.endswith(".m4a") and not nn.endswith(".part.m4a"):
            out.append(n)
    out.sort(key=lambda n: os.path.getmtime(os.path.join(cdir, n)), reverse=True)
    return out


def load_id_data(idv):
    base = os.path.join(DATA_DIR, idv)
    segments = _load_json(idpaths.find(base, "segments.json"), {}).get("segments", [])
    cands = _load_json(idpaths.find(base, "candidates_raw.json"), [])
    cand_by_title = {c.get("title"): c for c in cands}
    sil = _load_json(idpaths.find(base, "silences.json"), {})
    sil_by_index = {s.get("index"): s for s in sil.get("segments", [])}
    ex = _load_json(idpaths.find(base, "exclude_zones.json"), {})
    tr = _load_json(idpaths.find(base, "transcript.json"), {})
    # カット候補リストは ID ごと（data/<ID>/cutlist.json）。CUTLIST 環境変数で上書き可。
    cutlist_path = os.environ.get("CUTLIST") or idpaths.find(base, "cutlist.json")
    cutlist = _load_json(cutlist_path, {"speakers": [], "manual": []})
    cutdec = _load_json(idpaths.find(base, "cut_decisions.json"), {"cuts": []})
    ratings = _load_json(idpaths.find(base, "ratings.json"), {"ratings": []})
    vad = _load_json(idpaths.find(base, "vad.json"), {})
    return {
        "segments": segments,
        "cand_by_title": cand_by_title,
        "sil_by_index": sil_by_index,
        "sil_meta": sil,
        "exclude_zones": ex.get("exclude_zones", []),
        "fact_checks": ex.get("fact_checks", []),
        "tsegments": tr.get("segments", []),
        "cut_speakers": cutlist.get("speakers", []),
        "cut_manual": cutlist.get("manual", []),
        "cut_decisions": cutdec.get("cuts", []),
        "ratings_by_index": {r.get("index"): r for r in ratings.get("ratings", [])},
        # VAD の無音区間。バーの中を緑(発話)/黄(無音)で塗り分けるのに使う。
        "silence_spans": [tuple(x) for x in vad.get("silence", [])],
        # メイン話者＝最多話者（docs/編集規則.md「Speaker 1 = 大塚さん（最多話者）」）。
        # この話者だけ既定色、他はオレンジ系にして会話相手を見分けられるようにする。
        "main_speaker": _main_speaker(tr),
    }


def media_url(idv, seg, fname):
    return approot() + "/media/" + urllib.parse.quote(f"{idv}/contents/{seg}/{fname}")


def trim_applied(idv, segments):
    base = os.path.join(DATA_DIR, idv)
    if os.path.isfile(idpaths.find(base, "trim_plan.json")):
        return True
    for sg in segments:
        d = seg_dirname(idv, sg.get("index"), sg.get("title"))
        if d and os.path.isfile(os.path.join(base, "contents", d, "final_orig.mp4")):
            return True
    return False


# ---------- 区間(region)計算 ----------
def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def _seg_speaker(tsegments, a, b):
    """[a,b] に最も重なる transcript セグメントの話者を返す。"""
    best, bestov = None, 0.0
    for ts in tsegments or []:
        t0, t1 = ts.get("start"), ts.get("end")
        if t0 is None or t1 is None:
            continue
        ov = _overlap(a, b, t0, t1)
        if ov > bestov:
            bestov, best = ov, ts.get("speaker")
    return best


def _drop_reason(a, b, tsegments, cut_manual):
    """カット済み区間の理由を簡潔に返す（手動カテゴリ優先、無ければ話者判定）。"""
    for m in cut_manual or []:
        span = min(b - a, m["end"] - m["start"])
        if _overlap(a, b, m["start"], m["end"]) >= 0.5 * max(0.1, span):
            c, r = m.get("category", ""), m.get("reason", "")
            return (c + "：" + r) if (c and r) else (c or r or "確定カット")
    spk = _seg_speaker(tsegments, a, b)
    if spk and not str(spk).endswith("01"):
        n = str(spk).split("_")[-1].lstrip("0") or "?"
        return f"会話相手(Sp{n})の発言"
    return "確定カット"


def to_final(t, s, drops):
    """元音源時刻 t を、その区間の final 動画時刻へ（区間開始を引き、途中のdrop分を差し引く）。"""
    ft = max(0.0, t - s)
    for d0, d1 in drops:
        lo, hi = max(d0, s), min(d1, t)
        if hi > lo:
            ft -= (hi - lo)
    return max(0.0, ft)


def build_regions(sg, cand, fact_checks, exclude_zones, cut_speakers=None, cut_manual=None, tsegments=None,
                  cut_decisions=None):
    """本文に重ねる時間区間を優先度付きで返す（元音源タイムライン）。
    優先度: done(7) > spk(6) > cutlist(6) > todo(4) > fact(3) > quote(2) > exclude(1)。"""
    s, e = sg["start_sec"], sg["end_sec"]
    idx = sg.get("index")
    drops = sg.get("drops") or []
    cand_cuts = (cand or {}).get("cuts") or []
    regions = []

    # 会話相手の発言（Notta話者。基本カット対象）
    spk_blocks = [b for b in (cut_speakers or []) if b.get("index") == idx]
    for b in spk_blocks:
        if _overlap(b["start"], b["end"], s, e) <= 0:
            continue
        regions.append({"s": max(b["start"], s), "e": min(b["end"], e), "kind": "spk",
                        "prio": 6, "label": "会話相手", "reason": ""})

    for d0, d1 in drops:
        reason = _drop_reason(d0, d1, tsegments, cut_manual)
        # 会話相手の発言カットは通常カットと表示を分ける（ラベルは「会話相手」のみ）
        if reason.startswith("会話相手"):
            regions.append({"s": max(d0, s), "e": min(d1, e), "kind": "donespk",
                            "prio": 7, "label": "会話相手", "reason": ""})
        else:
            regions.append({"s": max(d0, s), "e": min(d1, e), "kind": "done",
                            "prio": 7, "label": "カット", "reason": reason})

    # カット候補はすべて cut_decisions.json（C番号・分類・判断状況）から描く。
    # 初期状態は全件オープン（勝手にカットしない）。オーナーが カット/残す ボタンで確定する。
    # 確定＝見えにくいグレー / 未決＝分類ごとの色（gpt=ピンク, speaker=#30d8ff, その他=紫系）
    todo = []
    for cd in (cut_decisions or []):
        cs, ce = float(cd["start_sec"]), float(cd["end_sec"])
        if _overlap(cs, ce, s, e) <= 0:
            continue
        cid = cd.get("cid", "")
        status = cd.get("status", "pending")
        cat = cd.get("category", "gpt")
        if status == "keep":
            regions.append({"s": max(cs, s), "e": min(ce, e), "kind": "keep", "prio": 4,
                            "label": f"{cid} 残す(判断済)", "reason": cd.get("note", "")})
            continue
        if status == "cut":
            if any(_overlap(cs, ce, d0, d1) >= 0.5 * (ce - cs) for d0, d1 in drops):
                continue  # 既に drops で薄グレー表示されている
            regions.append({"s": max(cs, s), "e": min(ce, e), "kind": "done", "prio": 4,
                            "label": f"{cid} カット指示", "reason": cd.get("note", "")})
            continue
        # 未決: 分類ごとの色＋カット/残すボタン
        if cat == "speaker":
            kind, name, reason = "spkopen", "会話相手(未決)", ""
        elif cat == "gpt":
            kind, name, reason = "todo", "カット推奨(未決)", cd.get("reason", "")
        else:
            kind, name, reason = "other", f"{esc(cat)}(未決)", cd.get("reason", "")
        regions.append({"s": max(cs, s), "e": min(ce, e), "kind": kind, "prio": 4,
                        "label": f"{cid} {name}", "reason": reason, "cid": cid})
        todo.append(cd)

    facts = []
    for fc in fact_checks:
        if _overlap(fc["start_sec"], fc["end_sec"], s, e) <= 0:
            continue
        regions.append({"s": max(fc["start_sec"], s), "e": min(fc["end_sec"], e),
                        "kind": "fact", "prio": 3, "label": "⚠ 事実確認",
                        "reason": fc.get("issue", "")})
        facts.append(fc)

    # 候補外という分類は廃止（exclude_zones は assign_cut_ids がカット推奨として取り込む）

    return regions, todo, facts


def region_for(mid, regions):
    best = None
    for r in regions:
        if r["s"] <= mid < r["e"] and (best is None or r["prio"] > best["prio"]):
            best = r
    return best


# ---------- 単語モデル（インライン差し込みの土台） ----------
_PUNCT = set(" 　、。，．・…！？!?「」『』（）()［］[]〈〉《》\"'\n\t")


def _norm(s):
    """正規化文字列と、正規化index→元index の対応表。"""
    out, imap = [], []
    for i, ch in enumerate(s):
        if ch in _PUNCT:
            continue
        out.append(ch)
        imap.append(i)
    return "".join(out), imap


def build_word_model(tsegments, s, e):
    """[s,e] の単語を段落構造付きで集める。
    返り値: paras=[{ts, words:[gidx,...]}], toks[gidx], gmid[gidx](中点時刻),
            raw(全単語連結), char_gidx(各文字→gidx)"""
    paras, toks, gmid = [], [], []
    char_gidx, raw_parts = [], []
    for tseg in tsegments:
        ts0, ts1 = tseg.get("start"), tseg.get("end")
        if ts0 is None or ts1 is None or _overlap(ts0, ts1, s, e) <= 0:
            continue
        words = tseg.get("words") or []
        pw = []
        for w in words:
            wt = w.get("start")
            if wt is None or not (s <= wt < e):
                continue
            tok = w.get("word", "")
            gidx = len(toks)
            toks.append(tok)
            gmid.append((wt + w.get("end", wt)) / 2)
            for _ in tok:
                char_gidx.append(gidx)
            raw_parts.append(tok)
            pw.append(gidx)
        if not pw:
            txt = (tseg.get("text") or "").strip()
            if txt:
                paras.append({"ts": max(ts0, s), "words": None, "text": txt})
            continue
        paras.append({"ts": max(ts0, s), "words": pw, "text": None})
    return paras, toks, gmid, "".join(raw_parts), char_gidx


def assign_regions(toks, gmid, regions):
    """各 gidx に時間ベースの region を割り当て（無ければ None）。"""
    per = [None] * len(toks)
    for g in range(len(toks)):
        per[g] = region_for(gmid[g], regions)
    return per


def overlay_quotes(per, raw, char_gidx, quotes):
    """象徴的セリフを本文に重ねる。GPTのセリフはASRと表記が微妙に違うため、
    最長共通部分文字列をアンカーにして元文長ぶんを重ねる（一致率0.6以上のみ採用）。"""
    norm, imap = _norm(raw)
    quote_region = {"kind": "quote", "prio": 2, "label": "", "reason": ""}
    for q in quotes or []:
        qn, _ = _norm(q)
        if len(qn) < 6 or not norm:
            continue
        sm = SequenceMatcher(None, norm, qn, autojunk=False)
        a = sm.find_longest_match(0, len(norm), 0, len(qn))
        if a.size < 6:
            continue
        astart = max(0, a.a - a.b)
        aend = min(len(norm), astart + len(qn))
        if aend <= astart:
            continue
        if SequenceMatcher(None, norm[astart:aend], qn, autojunk=False).ratio() < 0.6:
            continue
        c0, c1 = imap[astart], imap[aend - 1]
        for c in range(c0, c1 + 1):
            if c < len(char_gidx):
                g = char_gidx[c]
                if per[g] is None:  # cut/fact/exclude を上書きしない
                    per[g] = quote_region


def locate_trims(raw, char_gidx, gaps, vid_id, applied):
    """詰めギャップを before+after のマッチで単語境界に割り付ける。
    表示は |← X.X秒 →| のみ（秒数以外の文字を出さない）。クリックでその直前から再生。
    候補=紫 / 詰め済み=緑（cssで区別）。返り値: dict gidx -> [chip_html,...]"""
    ins = {}
    for g in gaps:
        before, after = g.get("before", ""), g.get("after", "")
        if len(before) < 3 or len(after) < 3:
            continue
        pos = raw.find(before + after)
        if pos < 0:
            continue
        boundary = pos + len(before)
        if boundary >= len(char_gidx):
            continue
        gidx = char_gidx[boundary]
        t = max(0.0, g.get("start_sec", 0) - 1.0)          # 詰め位置(final時刻)の直前から
        cls = "trim done" if applied else "trim"
        onclick = (f" onclick=\"event.stopPropagation();seekTo('{vid_id}',{t:.2f})\"" if vid_id else "")
        chip = f"<span class='{cls}'{onclick}>|← {g.get('duration', 0):.1f}s →|</span>"
        ins.setdefault(gidx, []).append(chip)
    return ins


def render_transcript(tsegments, s, e, regions, quotes, gaps, drops=None, vid_id=None, applied=False,
                      seg_no=None):
    paras, toks, gmid, raw, char_gidx = build_word_model(tsegments, s, e)
    per = assign_regions(toks, gmid, regions)
    overlay_quotes(per, raw, char_gidx, quotes)
    trim_ins = locate_trims(raw, char_gidx, gaps, vid_id, applied)
    drops = drops or []
    emitted_chip = set()

    def seek_at(t, cls, inner):
        """inner をクリック可能spanで包む。カット済み区間内なら元音源(seekOrig)を、
        それ以外は final 動画を、原音時刻 t の少し前から再生する。
        data-v/data-t（動画）・data-ot（元音源）は再生位置ハイライト用。"""
        if not vid_id:
            return inner
        if any(d0 <= t < d1 for d0, d1 in drops):
            return (f"<span class='{cls}' data-ot='{t:.2f}'"
                    f" onclick=\"seekOrig({max(0.0, t - 1.0):.2f})\">{inner}</span>")
        ft = to_final(t, s, drops)
        return (f"<span class='{cls}' data-v='{vid_id}' data-t='{ft:.2f}'"
                f" onclick=\"seekTo('{vid_id}',{max(0.0, ft - 1.5):.2f})\">{inner}</span>")

    def emit(cur, buf):
        if not buf:
            return ""
        text = esc("".join(toks[g] for g in buf))
        if cur is None:
            return text
        if cur["kind"] == "quote":
            return f"<span class='r-quote'>{text}</span>"
        # 理由は該当語の“上の行間”に注釈として置く（同一regionは初回のみ）
        label = ""
        if id(cur) not in emitted_chip:
            emitted_chip.add(id(cur))
            rs = esc(cur.get("reason", ""))
            full = esc(cur["label"]) + (f"：{rs}" if rs else "")
            btn = ""
            if cur.get("cid"):  # 未決 → オーナーがその場で確定するボタン
                btn = ("<span class='dbtn'>"
                       f"<button onclick=\"decide('{cur['cid']}','cut')\">カット</button>"
                       f"<button onclick=\"decide('{cur['cid']}','keep')\">残す</button></span>")
            label = f"<span class='ann-label ann-{cur['kind']}' title=\"{full}\">{full}{btn}</span>"
        return f"<span class='ann'>{label}<span class='r-{cur['kind']}'>{text}</span></span>"

    def render_words(word_ids):
        pieces, cur, buf = [], None, []
        for gidx in word_ids:
            if gidx in trim_ins:
                pieces.append(emit(cur, buf)); buf = []
                pieces.extend(trim_ins[gidx])
            r = per[gidx]
            if r is not cur:
                pieces.append(emit(cur, buf)); buf = []; cur = r
            buf.append(gidx)
        pieces.append(emit(cur, buf))
        return "".join(pieces)

    def para_head(t, bno):
        """発言ブロック頭の [セグ番号-ブロック連番] ＋時刻表示。
        「[6-3] をカット」「⑥の 02:30 をカット」のように指示しやすくするためのもの。"""
        ft = to_final(t, s, drops)
        ftxt = fmt_time(ft)
        stxt = fmt_time(t)
        if vid_id and any(d0 <= t < d1 for d0, d1 in drops):
            # カット済みブロック → 元音源で頭出し（カット内容の確認用）
            link = (f"<span class='ts-link' onclick=\"seekOrig({max(0.0, t - 1.0):.2f})\">"
                    f"{ftxt}</span>")
        elif vid_id:
            link = (f"<span class='ts-link' onclick=\"seekTo('{vid_id}',{max(0.0, ft - 0.5):.2f})\">"
                    f"{ftxt}</span>")
        else:
            link = ftxt
        bn = f"<b>[{seg_no}-{bno}]</b>　" if seg_no is not None else ""
        return f"<span class='ts'>{bn}{link}　<span>({stxt})</span></span>"

    out = []
    bno = 0
    for para in paras:
        bno += 1
        if para["words"] is None:
            txt = seek_at(para["ts"], "txt", esc(para["text"]))
            out.append(f"<div class='tp'>{para_head(para['ts'], bno)}{txt}</div>")
            continue
        # 適当な長さ（文末。！？ または 40字）でチャンク化。各チャンクをクリック可能に。
        chunks, cur = [], []
        for gidx in para["words"]:
            cur.append(gidx)
            tok = toks[gidx]
            if (any(p in tok for p in "。！？") and len(cur) >= 8) or len(cur) >= 40:
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
        parts = []
        for ch in chunks:
            inner = render_words(ch)
            parts.append(seek_at(gmid[ch[0]], "txt", inner))
        body = "".join(parts)
        if body.strip():
            out.append(f"<div class='tp'>{para_head(para['ts'], bno)}{body}</div>")
    return "".join(out)


# ---------- ページ描画 ----------
def render_index():
    # （切り抜き）は一覧に出さない（オーナー指示 2026-09-17。旧方式の別IDフォルダは
    # 未着手のまま廃止方向。切り抜きは同じタイトルの最終編集版から同一メニュー内に
    # 生成する方式へ — 詳細は別途指示）。ID ページ自体は URL 直打ちでは開ける
    ids = [i for i in list_ids() if "（切り抜き）" not in i]
    if not ids:
        return page("音源一覧", f"<h1>音源一覧</h1><p class='meta'>data: {esc(DATA_DIR)}</p>")
    rows = []
    for i in ids:
        key, label = id_status(i)
        cls = {"done": " class='production'", "sent": " class='delivered'"}.get(key, "")
        rows.append(
            f"<li{cls}><a href='{approot()}/id?id={urllib.parse.quote(i)}'>{esc(i)}</a>"
            f"<span class='st st-{key}'>{label}</span></li>")
    return page("音源一覧", f"<h1>音源一覧</h1><ul class='ids'>{''.join(rows)}</ul>")




def render_id(idv):
    if idv not in list_ids():
        return None
    d = load_id_data(idv)
    segments = d["segments"]
    parts = [
        f"<div class='crumb'><a href='{approot()}/'>← 一覧</a></div>",
        f"<h1>{esc(idv)}</h1>",
    ]
    if not segments:
        # まだ処理していない ID。何が足りないかだけ出す
        base = os.path.join(DATA_DIR, idv)
        has_tr = os.path.exists(idpaths.find(base, "transcript.json"))
        parts.append(
            "<p class='meta'>"
            + ("切り出し区間がまだありません（segments.json 未作成）。"
               if has_tr else
               "文字起こしがまだです。<br>bash scripts/transcribe.sh " + esc(idv))
            + "</p>")
        return page(idv, "".join(parts))
    # 元音源（無編集）。カット済み区間のクリック時にここから再生して内容を確認できるようにする
    # 再生用は preview_audio.m4a を最優先。元音源が ALAC だと Chrome / Firefox が
    # 再生できないため（2026-08-05 実測）。作り方: python scripts/make_preview_audio.py <ID>
    _b = os.path.join(DATA_DIR, idv)
    names = sorted(os.listdir(_b))
    _pv = idpaths.find(_b, "preview_audio.m4a")
    src_name = os.path.relpath(_pv, _b) if os.path.exists(_pv) else None
    if not src_name:
        src_name = next((n for n in names if n.lower().endswith(".m4a")), None)
    if not src_name:
        src_name = next((n for n in names if n.lower().endswith(".mp4")), None)
    if src_name:
        # preload='none' だと尺が分からずシークできない。タイムラインは 800秒などの
        # 絶対時刻へ飛ぶので metadata まで読ませる。
        parts.append(f"<audio id='orig' src='{approot()}/media/{urllib.parse.quote(idv + '/' + src_name)}'"
                     " preload='metadata' style='display:none'></audio>")
    # 並び順: オーナー評価の★が高い順。未評価は★1.5相当（★2以上の下・★0〜1の上）。同順位は index 順。
    def seg_order(sg):
        rt = d["ratings_by_index"].get(sg.get("index"))
        stars = float(rt["stars"]) if rt and rt.get("stars") is not None else 1.5
        is_full = "全編" in (sg.get("title") or "")
        # 全編を必ず先頭に（オーナー指示 2026-08-09）。残りは★順→番号順
        return (0 if is_full else 1, -stars, sg.get("index", 0))
    ordered = sorted(segments, key=seg_order)

    # 目次: タイトル・尺・オーナー評価(★と根拠)を縦に並べる
    def _jp(sec):
        m, s = divmod(int(round(sec)), 60)
        h, m = divmod(m, 60)
        return f"{h}時間{m}分{s}秒" if h else f"{m}分{s:02d}秒"

    def dur_jp_of(sg):
        """尺は「元→編集後」で出す（例: 49分43秒→25分21秒）。カットが無ければ元だけ。"""
        s0, e0 = sg["start_sec"], sg["end_sec"]
        gross = e0 - s0
        dsec = sum(max(0.0, min(d1, e0) - max(d0, s0)) for d0, d1 in (sg.get("drops") or []))
        if dsec < 1:
            return _jp(gross)
        return f"{_jp(gross)}→{_jp(gross - dsec)}"

    toc = []
    for sg in ordered:
        i = sg["index"]
        rt = d["ratings_by_index"].get(i)
        st_html = ""
        if rt and rt.get("stars") is not None:
            st_n = max(0, min(5, int(rt["stars"])))
            st_html = f"　<span class='stars'>{'★' * st_n}{'☆' * (5 - st_n)}</span>"
            if rt.get("quote"):  # 理由を述べた評価だけ根拠が入っている（直接指定は空）
                st_html += f"　<span class='rq'>「{esc(rt['quote'])}」</span>"
        _lbl = "＊" if "全編" in (sg.get("title") or "") else str(i)
        toc.append(f"<div class='toc-item'><a href='#seg{i}'>{_lbl} {esc(sg.get('title') or '')}</a>"
                   f"　{dur_jp_of(sg)}{st_html}</div>")
        # 要約（現在の切り出し内容ベース）→ ハイライト原文 の順に下へ並べる
        tcand = d["cand_by_title"].get(sg.get("title"))
        summary = sg.get("summary") or (tcand or {}).get("summary")
        if summary:
            toc.append(f"<div class='toc-sum'>{esc(summary)}</div>")
        for q in sg.get("highlight_quotes") or (tcand or {}).get("highlight_quotes") or []:
            toc.append(f"<div class='toc-q'>・{esc(q)}</div>")
    parts.append("<div class='toc'>" + "".join(toc) + "</div>")

    for sg in ordered:
        idx = sg.get("index")
        title = sg.get("title", "")
        cand = d["cand_by_title"].get(title)
        s, e = sg["start_sec"], sg["end_sec"]
        drops = sg.get("drops") or []
        drop_sec = sum(max(0.0, min(d1, e) - max(d0, s)) for d0, d1 in drops)
        dur = (e - s) - drop_sec
        gross = e - s

        regions, todo, facts = build_regions(sg, cand, d["fact_checks"], d["exclude_zones"],
                                             d["cut_speakers"], d["cut_manual"], d["tsegments"],
                                             d["cut_decisions"])
        segfolder = seg_dirname(idv, idx, title)
        silseg = d["sil_by_index"].get(idx)
        # 自然詰めが実際に触るギャップ＝ likely_dropped(取りこぼし) を除き 1.5秒以上
        gaps = [g for g in (silseg or {}).get("gaps", [])
                if g.get("flag") != "likely_dropped" and g.get("duration", 0) >= 1.5]

        _full = "全編" in (title or "")
        _prod = " production" if sg.get("production") else ""
        _dlv = " delivered" if sg.get("delivered") else ""
        parts.append(f"<div class='seg{' fullep' if _full else ''}{_prod}{_dlv}' id='seg{idx}'>")
        rank = cand.get("rank") if cand else None
        # オーナー評価（★5段階＋根拠の発言を併記。分割したら評価はリセットされる）
        rt = d["ratings_by_index"].get(idx)
        if rt and rt.get("stars") is not None:
            st_n = max(0, min(5, int(rt["stars"])))
            rate_html = (f"<div class='rating'><b>オーナー評価:</b> "
                         f"<span class='stars'>{'★' * st_n}{'☆' * (5 - st_n)}</span> {st_n}/5")
            if rt.get("quote"):
                rate_html += (f"　<span class='rq'>根拠:「{esc(rt['quote'])}」"
                              f"{('(' + esc(rt.get('date') or '') + ')') if rt.get('date') else ''}</span>")
            rate_html += "</div>"
        else:
            rate_html = "<div class='rating unrated'><b>オーナー評価:</b> ☆☆☆☆☆ 未評価</div>"
        def _jp2(sec):
            m2, s2 = divmod(int(round(sec)), 60)
            h2, m2 = divmod(m2, 60)
            return f"{h2}時間{m2}分{s2}秒" if h2 else f"{m2}分{s2:02d}秒"
        dur_jp = _jp2(gross) if drop_sec < 1 else f"{_jp2(gross)}→{_jp2(dur)}"
        parts.append(
            "<div class='seghd'>"
            f"<h2><span class='rank'>{'＊' if _full else idx}</span>　{esc(title)}</h2>"
            + rate_html +
            f"<div class='meta'><span id='dur{idx}'>{dur_jp}</span> [{fmt_time(s)}〜{fmt_time(e)}]</div></div>"
        )

        if segfolder and os.path.isfile(os.path.join(DATA_DIR, idv, "contents", segfolder, "final.mp4")):
            parts.append(f"<video id='vid{idx}' src='{media_url(idv, segfolder, 'final.mp4')}' controls preload='metadata'></video>")
            links = [f"<a href='{media_url(idv, segfolder, fn)}'>{esc(lb)}</a>"
                     for fn, lb in MEDIA_FILES
                     if os.path.isfile(os.path.join(DATA_DIR, idv, "contents", segfolder, fn))]
            if links:
                parts.append("<div class='dl'>" + "".join(links) + "</div>")
        # ボタンは1つ。完了したらブラウザのダウンロードとして自動で落ちてくる
        # （リンク列・プレーヤーは出さない。オーナー指示・2026-08-08）
        _sid = sg.get("sid") or ""
        # 切り抜きボタンは本番使用チェックが付いたものにだけ出す（CLIP_PLAN・原文 L08-09。
        # 文言とスタイルはオーナー指示 2026-09-28・原文 L96-97）
        _clip_btn = (f"　<button class='gbtn' onclick=\"clipCreate('{_sid}',{idx})\">"
                     "このバージョンの切り抜き編集画面へ</button>"
                     if sg.get("production") else "")
        parts.append(
            f"<p class='meta'><button onclick=\"renderSeg('{_sid}',{idx})\">この編集で書き出す（m4a）</button>"
            f"　<label><input type='checkbox' class='nrtoggle' onchange='nrToggle(this)'> ノイズ除去</label>"
            f"　<label><input type='checkbox'{' checked' if sg.get('production') else ''}"
            f" onchange=\"segFlag('production',{idx},'{_sid}',this)\"> 本番使用</label>"
            f"　<label><input type='checkbox'{' checked' if sg.get('delivered') else ''}"
            f" onchange=\"segFlag('delivered',{idx},'{_sid}',this)\"> 配信済み</label>"
            f"{_clip_btn}"
            f"　<span id='rst{idx}' class='meta'></span></p>")
        # 凍結版の一覧。1次編集を変えた後でも古い切り抜き編集へここから到達できる
        if sg.get("production"):
            vers = list_clip_versions(idv, _sid)
            if vers:
                links = "　".join(
                    f"<a href='{approot()}/clip?id={urllib.parse.quote(idv)}&key={urllib.parse.quote(v['key'])}'>"
                    f"切り抜き編集 {esc((v['created_at'] or '')[:16].replace('T', ' '))}"
                    f"（{v['nclips']}本）</a>" for v in vers)
                parts.append(f"<p class='meta editlink'>{links}</p>")

        # 要約: segments.json の summary（現在の切り出し内容から作り直したもの）を優先。
        # レビューは表示しない。見出しラベルも付けず本文だけ。
        summary = sg.get("summary") or (cand or {}).get("summary")
        if summary:
            parts.append(f"<div class='box summary'>{esc(summary)}</div>")

        # 切り出し全文（すべての注釈を本文中に）
        quotes = sg.get("highlight_quotes") or (cand or {}).get("highlight_quotes") or []
        trim_done = bool(segfolder) and os.path.isfile(
            os.path.join(DATA_DIR, idv, "contents", segfolder, "final_orig.mp4"))
        # 文字起こしの場所はタイムラインにする（オーナー指示・2026-08-05）。
        # 別ページを開かず、この画面で切る。
        parts.append("<div class='transcript'>"
                     + timeline_block(idv, sg, d["tsegments"], d["silence_spans"],
                                      d["main_speaker"], d["cut_decisions"], quotes)
                     + "</div>")
        parts.append("</div>")

    return page(f"{idv} 生成物", "".join(parts))


def apply_decision(idv, cid, action, status_only=False):
    """カット/残す ボタンの確定処理。cut_decisions.json の status を更新する。
    status_only=True のときは segments.json に触らない。タイムラインから押された場合は
    drops をタイムライン自身が /edit_save で書くので、二重に書くと競合するため。
    動画への反映は render.py の再実行時。"""
    import datetime
    if idv not in list_ids() or action not in ("cut", "keep"):
        return False
    base = os.path.join(DATA_DIR, idv)
    dec_path = idpaths.find(base, "cut_decisions.json")
    dec = _load_json(dec_path, {"cuts": []})
    target = None
    for c in dec.get("cuts", []):
        if c.get("cid") == cid:
            c["status"] = action
            c["decided"] = datetime.date.today().isoformat()
            target = c
            break
    if target is None:
        return False
    if status_only:
        with open(dec_path, "w", encoding="utf-8") as f:
            json.dump(dec, f, ensure_ascii=False, indent=2)
        _queue_for_sync(dec_path)
        return True
    seg_path = idpaths.find(base, "segments.json")
    seg = _load_json(seg_path, {})
    st, en = float(target["start_sec"]), float(target["end_sec"])
    for sg in seg.get("segments", []):
        s0, e0 = sg["start_sec"], sg["end_sec"]
        cs, ce = max(st, s0), min(en, e0)
        if ce - cs <= 0:
            continue
        drops = sg.get("drops") or []
        if action == "cut":
            if not any(abs(d0 - cs) < 0.3 and abs(d1 - ce) < 0.3 for d0, d1 in drops):
                drops.append([cs, ce])
                sg["drops"] = sorted(drops)
        else:
            sg["drops"] = [d for d in drops
                           if not (abs(d[0] - cs) < 0.3 and abs(d[1] - ce) < 0.3)]
    with open(dec_path, "w", encoding="utf-8") as f:
        json.dump(dec, f, ensure_ascii=False, indent=2)
    with open(seg_path, "w", encoding="utf-8") as f:
        json.dump(seg, f, ensure_ascii=False, indent=2)
    _queue_for_sync(dec_path, seg_path)
    return True


# チェックボックスで立てるセグメントの印（オーナー指示 2026-09-17）。
# production=本番使用（黄背景・編集完了）/ delivered=配信済み（薄紫背景・ラベル配信済み）
SEG_FLAGS = ("production", "delivered")


def set_seg_flag(idv, sid, field, on):
    """セグメントの印の保存。segments.json の該当セグメントにフラグを立てる/外す。
    編集データなので他の保存と同じ作法で扱う（受信ジャーナル→履歴退避→書き込み→同期キュー）。"""
    import datetime
    if idv not in list_ids() or not sid or field not in SEG_FLAGS:
        return False
    base = os.path.join(DATA_DIR, idv)
    try:
        journal = os.path.join(idpaths.edit_dir(base), "edit_save_journal.jsonl")
        with open(journal, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.datetime.now().isoformat(timespec="milliseconds"),
                                "payload": {"op": field, "id": idv, "sid": sid, "on": on}},
                               ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass
    seg_path = idpaths.find(base, "segments.json")
    seg = _load_json(seg_path, {})
    changed = False
    for sg in seg.get("segments", []):
        if sg.get("sid") == sid:
            if on:
                sg[field] = True
            else:
                sg.pop(field, None)
            changed = True
    if not changed:
        return False
    _append_history(base, seg_path)
    with open(seg_path, "w", encoding="utf-8") as f:
        json.dump(seg, f, ensure_ascii=False, indent=2)
    _queue_for_sync(seg_path, os.path.join(idpaths.edit_dir(base), "segments_history.jsonl"))
    return True


# ---------- 切り抜き（CLIP_PLAN）----------
# 設計の正本は podcast/CLIP_PLAN.md、仕様原文は docs/CLIP_SPEC_20260928_原文.md。
# 「切り抜きを作成」を押した瞬間の1次編集状態（区間+drops）を凍結し、
# clipkey = <sid>_<hash8> に紐づける。1次編集を後から変えても既存の切り抜き編集には
# 影響しない（別の clipkey = 別の切り抜き編集画面になる。原文 L73-78）。
# 既存の segments.json には一切書き込まない（大原則1）。

CLIP_UNIT_GAP = 0.8        # 字幕ユニットの区切り: この秒数以上の間隔（オーナー裁定 2026-09-28）
CLIP_UNIT_PUNCT = "。．！？!?"


def clip_key_of(sg):
    """凍結キー。1次編集の状態（区間+drops）が変わると別のキーになる。"""
    import hashlib
    canon = json.dumps({"segStart": round(float(sg["start_sec"]), 3),
                        "segEnd": round(float(sg["end_sec"]), 3),
                        "drops": sorted([round(float(a), 3), round(float(b), 3)]
                                        for a, b in (sg.get("drops") or []))},
                       sort_keys=True)
    h8 = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:8]
    return f"{sg.get('sid')}_{h8}"


def build_clip_source(idv, sg):
    """凍結スナップショット（clip_<key>_source.json の中身）を作る。
    transcript の単語を drops で間引き、編集後時間軸（カットを詰めた連続時間）へ再配置し、
    字幕ユニット（0.8秒以上の間隔または句読点で区切った文字のまとまり）にまとめる。"""
    import datetime
    base = os.path.join(DATA_DIR, idv)
    tr = _load_json(idpaths.find(base, "transcript.json"), {})
    s, e = float(sg["start_sec"]), float(sg["end_sec"])
    drops = sorted([[max(s, float(a)), min(e, float(b))] for a, b in (sg.get("drops") or [])
                    if float(b) > s and float(a) < e])
    # keep 区間と、各 keep の編集後開始オフセット
    keeps, t = [], s
    for a, b in drops:
        if a - t > 0.01:
            keeps.append([t, a])
        t = max(t, b)
    if e - t > 0.01:
        keeps.append([t, e])
    kmap, acc = [], 0.0
    for a, b in keeps:
        kmap.append((a, b, acc))
        acc += b - a

    def remap(t0):
        for a, b, off in kmap:
            if a <= t0 <= b:
                return off + (t0 - a)
        return None

    words = []
    for tseg in tr.get("segments", []):
        for w in (tseg.get("words") or []):
            st, en = w.get("start"), w.get("end")
            if st is None or en is None or not (s <= st < e):
                continue
            tok = (w.get("word") or "").strip()
            if not tok:
                continue
            mid = (float(st) + float(en)) / 2
            if remap(mid) is None:      # カットされた単語は落とす
                continue
            ns, ne = remap(float(st)), remap(float(en))
            if ns is None:
                ns = remap(mid) - (mid - float(st))
            if ne is None:
                ne = ns + (float(en) - float(st))
            words.append({"t": tok, "s": round(max(0.0, ns), 3), "e": round(max(0.0, ne), 3)})
    words.sort(key=lambda w: w["s"])
    units, cur = [], None
    for w in words:
        if cur is not None and w["s"] - cur["e"] >= CLIP_UNIT_GAP:
            units.append(cur)
            cur = None
        if cur is None:
            cur = {"s": w["s"], "e": w["e"], "t": w["t"]}
        else:
            cur["t"] += w["t"]
            cur["e"] = w["e"]
        if cur["t"] and cur["t"][-1] in CLIP_UNIT_PUNCT:
            units.append(cur)
            cur = None
    if cur is not None:
        units.append(cur)
    return {"id": idv, "sid": sg.get("sid") or "", "key": clip_key_of(sg),
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "seg": {"index": sg.get("index"), "title": sg.get("title") or "",
                    "start_sec": s, "end_sec": e, "drops": drops},
            "duration": round(acc, 3), "units": units}


# 凍結音源の生成プロセス。key=(ID, clipkey) → subprocess.Popen
CLIP_SOURCE_RENDERS = {}


def start_clip_source_render(idv, key):
    """凍結音源（generated/clip_<key>_source.m4a）をバックグラウンド生成する。"""
    import subprocess
    base = os.path.join(DATA_DIR, idv)
    if os.path.isfile(idpaths.find(base, f"clip_{key}_source.m4a")):
        return "done"
    k = (idv, key)
    p = CLIP_SOURCE_RENDERS.get(k)
    if p is not None and p.poll() is None:
        return "already_running"
    root = os.path.dirname(HERE)
    py = os.path.join(root, "venv", "bin", "python")
    if not os.path.isfile(py):
        py = _sys.executable
    gen = idpaths.gen_dir(base)
    logf = open(os.path.join(gen, f"clip_{key}_source.log"), "w", encoding="utf-8")
    CLIP_SOURCE_RENDERS[k] = subprocess.Popen(
        [py, os.path.join(root, "scripts", "make_clip_source.py"), idv, "--key", key],
        cwd=root, stdout=logf, stderr=subprocess.STDOUT)
    return "started"


def create_clip(idv, sid):
    """「切り抜きを作成」。現在の1次編集状態を凍結して clipkey を返す。
    同じ状態の凍結が既にあればそれをそのまま使う（再凍結しない）。"""
    import datetime
    if idv not in list_ids() or not sid:
        return None
    base = os.path.join(DATA_DIR, idv)
    seg = _load_json(idpaths.find(base, "segments.json"), {})
    sg = next((x for x in seg.get("segments", []) if x.get("sid") == sid), None)
    # ボタンは本番使用にしか出ないが、サーバー側でも守る（原文 L08-09）
    if sg is None or not sg.get("production"):
        return None
    key = clip_key_of(sg)
    src_path = idpaths.find(base, f"clip_{key}_source.json")
    if not os.path.isfile(src_path):
        try:
            journal = os.path.join(idpaths.edit_dir(base), "edit_save_journal.jsonl")
            with open(journal, "a", encoding="utf-8") as f:
                f.write(json.dumps({"at": datetime.datetime.now().isoformat(timespec="milliseconds"),
                                    "payload": {"op": "clip_create", "id": idv, "sid": sid,
                                                "key": key}}, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass
        source = build_clip_source(idv, sg)
        sp = idpaths.save(base, f"clip_{key}_source.json")
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(source, f, ensure_ascii=False, indent=2)
        # 編集の現在状態。units は source のコピーから修正していく
        cur = {"id": idv, "key": key, "sid": source["sid"], "title": source["seg"]["title"],
               "created_at": source["created_at"], "clips": [],
               "units": source["units"], "video": {}}
        cp = idpaths.save(base, f"clip_{key}.json")
        with open(cp, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
        _queue_for_sync(sp, cp)
    start_clip_source_render(idv, key)
    return key


def apply_clip_save(payload):
    """/clip_save: 切り抜き編集（セグメント・テキスト・動画設定）の全量保存。
    作法は apply_timeline_save と同型: 受信ジャーナル(fsync) → 履歴退避 → 全量書き →
    同期キュー（大原則3）。既存の segments.json には触れない。"""
    import datetime
    idv = str(payload.get("id") or "")
    key = str(payload.get("key") or "")
    if idv not in list_ids() or not re.fullmatch(r"[0-9a-f]{12}_[0-9a-f]{8}", key):
        return False
    base = os.path.join(DATA_DIR, idv)
    try:
        journal = os.path.join(idpaths.edit_dir(base), f"clip_{key}_journal.jsonl")
        with open(journal, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.datetime.now().isoformat(timespec="milliseconds"),
                                "payload": payload}, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass
    path = idpaths.find(base, f"clip_{key}.json")
    if not os.path.isfile(path):
        return False
    cur = _load_json(path, {})
    changed = False
    if "clips" in payload:
        clean = []
        for c in payload.get("clips") or []:
            try:
                a, b = float(c[0]), float(c[1])
            except (TypeError, ValueError, IndexError):
                return False
            if b > a:
                clean.append([round(a, 3), round(b, 3)])
        cur["clips"] = sorted(clean)
        changed = True
    if "units" in payload:
        clean_u = []
        for u in payload.get("units") or []:
            try:
                s, e = float(u["s"]), float(u["e"])
                t = str(u.get("t") or "")
            except (TypeError, ValueError, KeyError):
                return False
            clean_u.append({"s": round(s, 3), "e": round(e, 3), "t": t})
        cur["units"] = sorted(clean_u, key=lambda u: u["s"])
        changed = True
    if "video" in payload and isinstance(payload.get("video"), dict):
        cur["video"] = payload["video"]
        changed = True
    if not changed:
        return False
    # 上書き前の内容を履歴へ退避（segments_history と同じ考え方・200件）
    try:
        with open(path, encoding="utf-8") as f:
            prev = f.read()
        hist = os.path.join(idpaths.edit_dir(base), f"clip_{key}_history.jsonl")
        lines = []
        if os.path.isfile(hist):
            with open(hist, encoding="utf-8") as f:
                lines = f.read().splitlines()
        lines.append(json.dumps({"at": datetime.datetime.now().isoformat(timespec="seconds"),
                                 "clip_json": prev}, ensure_ascii=False))
        with open(hist, "w", encoding="utf-8") as f:
            f.write("\n".join(lines[-200:]) + "\n")
    except Exception:
        pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)
    _queue_for_sync(path, os.path.join(idpaths.edit_dir(base), f"clip_{key}_history.jsonl"))
    return True


def list_clip_versions(idv, sid):
    """このセグメントの凍結版一覧（新しい順）。1次編集を変えた後でも古い切り抜き編集へ
    ここから到達できる（原文 L76-77 の「版ごとに別画面」の入口）。"""
    base = os.path.join(DATA_DIR, idv)
    ed = os.path.join(base, idpaths.EDIT_DIR)
    if not os.path.isdir(ed):
        return []
    out = []
    for n in sorted(os.listdir(ed)):
        if n.startswith(f"clip_{sid}_") and n.endswith("_source.json"):
            key = n[len("clip_"):-len("_source.json")]
            src = _load_json(os.path.join(ed, n), {})
            cur = _load_json(os.path.join(ed, f"clip_{key}.json"), {})
            out.append({"key": key, "created_at": src.get("created_at") or "",
                        "nclips": len(cur.get("clips") or [])})
    out.sort(key=lambda v: v["created_at"], reverse=True)
    return out


ASSETS_DIR = os.path.join(os.path.dirname(HERE), "assets")

# 動画の生成・書き出しは当面ローカル(mac)のみ（オーナー裁定 2026-09-28。
# フォントのライセンスとサーバー負荷のため）。サーバー機は hostname で見分ける
# （web1-stg = staging / web1 = 本番。workspace CLAUDE.md の規約）。
CLIP_RENDER_ENABLED = os.uname().nodename.split(".")[0] not in ("web1", "web1-stg")

# 切り抜き動画の生成プロセス。key=(ID, clipkey, seg) → subprocess.Popen
CLIP_VID_RENDERS = {}


def start_clip_video_render(idv, key, seg, sizes, export=False):
    """make_clip_video.py をバックグラウンドで走らせる（C-8 生成 / C-9 書き出し）。"""
    import subprocess
    if not CLIP_RENDER_ENABLED:
        return "disabled"
    if idv not in list_ids() or not re.fullmatch(r"[0-9a-f]{12}_[0-9a-f]{8}", key or ""):
        return "bad_id"
    try:
        seg = int(seg)
    except (TypeError, ValueError):
        return "bad_seg"
    if not sizes:
        return "no_sizes"
    k = (idv, key, seg, export)
    p = CLIP_VID_RENDERS.get(k)
    if p is not None and p.poll() is None:
        return "already_running"
    root = os.path.dirname(HERE)
    py = os.path.join(root, "venv", "bin", "python")
    if not os.path.isfile(py):
        py = _sys.executable
    base = os.path.join(DATA_DIR, idv)
    gen = idpaths.gen_dir(base)
    logf = open(os.path.join(gen, f"clip_{key}_render_{seg}{'_export' if export else ''}.log"),
                "w", encoding="utf-8")
    cmd = [py, os.path.join(root, "scripts", "make_clip_video.py"), idv,
           "--key", key, "--seg", str(seg), "--sizes", ",".join(sizes)]
    if export:
        cmd.append("--export")
    CLIP_VID_RENDERS[k] = subprocess.Popen(cmd, cwd=root, stdout=logf,
                                           stderr=subprocess.STDOUT)
    return "started"


def clip_video_render_status(idv, key, seg, export=False):
    try:
        seg = int(seg)
    except (TypeError, ValueError):
        return "bad_seg"
    p = CLIP_VID_RENDERS.get((idv, key, seg, export))
    if p is None:
        return "none"
    if p.poll() is None:
        return "running"
    if p.returncode != 0:
        return f"failed({p.returncode})"
    return "done"


def load_clip_styles():
    """スタイル定義の正本 config/clip_styles.json（C-7）。コードにスタイル値を埋め込まない
    （原文 L53）。make_clip_video.py も同じファイルを読む。"""
    return _load_json(os.path.join(os.path.dirname(HERE), "config", "clip_styles.json"), {})


def list_clip_fonts():
    """assets/fonts/ のフォントファイル一覧（選択肢はフォルダの中身そのまま。原文 L41）。"""
    d = os.path.join(ASSETS_DIR, "fonts")
    if not os.path.isdir(d):
        return []
    return sorted(n for n in os.listdir(d)
                  if n.lower().endswith((".otf", ".ttf", ".ttc")))


def list_clip_backgrounds():
    """assets/clip_backgrounds/ の背景動画一覧（原文 L61）。"""
    d = os.path.join(ASSETS_DIR, "clip_backgrounds")
    if not os.path.isdir(d):
        return []
    return sorted(n for n in os.listdir(d)
                  if n.lower().endswith((".mp4", ".mov", ".m4v", ".webm")))


def clip_full_text(units, cs, ce):
    """切り抜き区間に重なる字幕ユニットのテキスト全文。"""
    return "".join(u.get("t") or "" for u in units
                   if float(u["e"]) > cs and float(u["s"]) < ce)


def render_clip_videos(idv, key):
    """動画作成画面（CLIP_PLAN C-6）。切り抜きが時系列順に並び、コンテンツごとに
    テキスト全文・設定ウインドウ・生成・再生・書き出しを持つ（原文 L66-69）。
    生成・書き出しの実処理は C-8/C-9。"""
    if idv not in list_ids():
        return None
    base = os.path.join(DATA_DIR, idv)
    src = _load_json(idpaths.find(base, f"clip_{key}_source.json"), None)
    if not src:
        return None
    cur = _load_json(idpaths.find(base, f"clip_{key}.json"), {})
    clips = sorted(cur.get("clips") or [])
    units = cur.get("units") or []
    styles = load_clip_styles()
    fonts = list_clip_fonts()
    bgs = list_clip_backgrounds()
    video = cur.get("video") or {}
    per = video.get("clips") or {}
    sizes = styles.get("sizes") or []
    sub_style = (styles.get("subtitle_styles") or [{}])[0]
    title_styles = styles.get("title_styles") or []
    parts = [
        f"<div class='crumb'><a href='{approot()}/clip?id={urllib.parse.quote(idv)}&key={urllib.parse.quote(key)}'>"
        f"← 切り抜き編集</a></div>",
        f"<h1>動画の作成　{esc(src['seg'].get('title') or '')}</h1>",
        f"<p class='meta'>凍結版 {esc((src.get('created_at') or '')[:16].replace('T', ' '))}"
        f"　切り抜き {len(clips)}本（タイムラインの時系列順）</p>",
    ]
    if not fonts:
        parts.append("<p class='meta'>フォントがありません。assets/fonts/ にフォントファイル"
                     "（.otf/.ttf/.ttc）を置いてください。</p>")
    if not bgs:
        parts.append("<p class='meta'>背景動画がありません。assets/clip_backgrounds/ に動画"
                     "（.mp4 等）を置いてください。</p>")
    if not clips:
        parts.append("<p class='meta'>切り抜きがまだありません。切り抜き編集画面で S / E で"
                     "区間を指定してください。</p>")
    default_sizes = [s["key"] for s in sizes if s.get("default_on")]
    for n, (cs, ce) in enumerate(clips):
        cfg = per.get(str(n)) or {}
        dur = ce - cs
        m2, s2 = divmod(int(round(dur)), 60)
        text = clip_full_text(units, cs, ce)
        checked_sizes = cfg.get("sizes") if cfg.get("sizes") is not None else default_sizes
        size_boxes = "".join(
            f"<label style='margin-right:14px'><input type='checkbox' class='cvsize' value='{esc(s['key'])}'"
            f"{' checked' if s['key'] in checked_sizes else ''} onchange='cvSave({n})'> "
            f"{esc(s['label'])}</label>"
            for s in sizes)
        font_opts = "".join(
            f"<option value='{esc(f2)}'{' selected' if cfg.get('font') == f2 else ''}>{esc(f2)}</option>"
            for f2 in fonts) or "<option value=''>（assets/fonts が空）</option>"
        bg_opts = "".join(
            f"<option value='{esc(b)}'{' selected' if cfg.get('background') == b else ''}>{esc(b)}</option>"
            for b in bgs) or "<option value=''>（assets/clip_backgrounds が空）</option>"
        tstyle_opts = "".join(
            f"<option value='{esc(t['key'])}'{' selected' if cfg.get('title_style') == t['key'] else ''}>"
            f"{esc(t.get('label') or t['key'])}</option>" for t in title_styles)
        size_pct = cfg.get("size_pct") or sub_style.get("font_size_pct") or 4.7
        parts.append(
            f"<div class='seg' id='cv{n}' data-cs='{cs}' data-ce='{ce}'>"
            f"<div class='seghd'><h2><span class='rank'>{n + 1}</span>　"
            f"{fmt_time(cs)}〜{fmt_time(ce)}　{m2}分{s2:02d}秒</h2></div>"
            f"<div class='box summary'>{esc(text) or '（この区間にテキストがありません）'}</div>"
            "<p class='meta'>"
            f"タイトル <input type='text' class='cvtitle' value=\"{esc(cfg.get('title') or '')}\""
            f" placeholder='動画の見出し（全編表示）' style='width:340px' onchange='cvSave({n})'>"
            f"　スタイル <select class='cvtstyle' onchange='cvSave({n})'>{tstyle_opts}</select></p>"
            "<p class='meta'>"
            f"フォント <select class='cvfont' onchange='cvSave({n})'>{font_opts}</select>"
            f"　字幕サイズ <button onclick='cvStep({n},-1)'>−</button>"
            f"<input type='number' class='cvsizepct' value='{size_pct}' step='0.1' min='1' max='12'"
            f" style='width:60px' onchange='cvSave({n})'>"
            f"<button onclick='cvStep({n},1)'>＋</button>（高さ%）"
            f"　背景 <select class='cvbg' onchange='cvSave({n})'>{bg_opts}</select></p>"
            f"<p class='meta'>書き出しサイズ {size_boxes}</p>")
        # 生成済みプレビュー（動画の再生ウインドウ。原文 L68）。生成のたびに ?v= で更新
        previews = []
        for s in sizes:
            pv = os.path.join(base, "generated", f"clip_{key}_preview_{n}_{s['key']}.mp4")
            if os.path.isfile(pv):
                rel = f"{idv}/generated/clip_{key}_preview_{n}_{s['key']}.mp4"
                previews.append(
                    f"<div style='flex:1;min-width:200px;max-width:320px'>"
                    f"<div class='meta'>{esc(s['key'])}</div>"
                    f"<video class='cvpv' data-size='{esc(s['key'])}' controls preload='metadata'"
                    f" style='width:100%;max-width:320px'"
                    f" src='{approot()}/media/{urllib.parse.quote(rel)}?v={int(os.path.getmtime(pv))}'>"
                    "</video></div>")
        if CLIP_RENDER_ENABLED:
            gen_btn = f"<button class='gbtn' onclick='cvRender({n})'>生成</button>"
            exp_btn = f"<button class='gbtn' onclick='cvExport({n})'>書き出し</button>"
        else:
            note = "動画の生成・書き出しはローカル(mac)で行います（オーナー裁定 2026-09-28）"
            gen_btn = f"<button class='gbtn' disabled title='{note}'>生成</button>"
            exp_btn = f"<button class='gbtn' disabled title='{note}'>書き出し</button>"
        # 書き出し済みファイル（このカードのタイトルで始まるもの）
        exp_dir = os.path.join(base, "contents", "clip", key)
        prefix = safe_name((cfg.get("title") or f"クリップ{n + 1}").strip())
        exports = []
        if os.path.isdir(exp_dir):
            for fn2 in sorted(os.listdir(exp_dir)):
                if fn2.startswith(prefix) and fn2.endswith(".mp4"):
                    rel = f"{idv}/contents/clip/{key}/{fn2}"
                    exports.append(f"<a href='{approot()}/media/{urllib.parse.quote(rel)}'"
                                   f" download>{esc(fn2)}</a>")
        exp_html = ("<p class='meta dl'>書き出し済み: " + "　".join(exports) + "</p>") if exports else ""
        parts.append(
            f"<p class='meta'>{gen_btn}　{exp_btn}"
            f"　<span class='cvstat meta'></span></p>"
            f"<div class='cvpvs' style='display:flex;gap:12px;flex-wrap:wrap'>{''.join(previews)}</div>"
            f"{exp_html}"
            "</div>")
    step = styles.get("subtitle_size_step_pct") or 0.3
    parts.append(
        "<script>"
        f"var CV_STEP={step};"
        "function cvCollect(){var out={};"
        "document.querySelectorAll('[id^=cv]').forEach(function(card){"
        "if(!/^cv\\d+$/.test(card.id))return;var n=card.id.slice(2);"
        "out[n]={title:card.querySelector('.cvtitle').value,"
        "title_style:card.querySelector('.cvtstyle').value,"
        "font:card.querySelector('.cvfont').value,"
        "size_pct:parseFloat(card.querySelector('.cvsizepct').value)||4.7,"
        "background:card.querySelector('.cvbg').value,"
        "sizes:[].slice.call(card.querySelectorAll('.cvsize:checked')).map(function(c){return c.value;})};});"
        "return out;}"
        "function cvSave(n){var q=new URLSearchParams(location.search);"
        "var card=document.getElementById('cv'+n);"
        "var el=card?card.querySelector('.cvstat'):null;if(el)el.textContent='保存中…';"
        "fetch(window.APP+'/clip_save',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({id:q.get('id'),key:q.get('key'),op:'video-settings',"
        "video:{clips:cvCollect()}})})"
        ".then(function(r){if(el)el.textContent=r.ok?'保存済み':'保存失敗';})"
        ".catch(function(){if(el)el.textContent='サーバーに接続できません';});}"
        "function cvStep(n,d){var card=document.getElementById('cv'+n);"
        "var inp=card.querySelector('.cvsizepct');"
        "inp.value=(Math.round(((parseFloat(inp.value)||4.7)+d*CV_STEP)*10)/10);cvSave(n);}"
        # 生成: 設定を保存 → make_clip_video をバックグラウンド実行 → 完了でリロード
        # （プレビューの <video> はサーバー側がファイルの有無で組むため）
        "function cvRender(n){var q=new URLSearchParams(location.search);"
        "var card=document.getElementById('cv'+n);var el=card.querySelector('.cvstat');"
        "var sizes=[].slice.call(card.querySelectorAll('.cvsize:checked')).map(function(c){return c.value;});"
        "if(!sizes.length){el.textContent='書き出しサイズを選んでください';return;}"
        "el.textContent='設定を保存中…';"
        "fetch(window.APP+'/clip_save',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({id:q.get('id'),key:q.get('key'),op:'video-settings',"
        "video:{clips:cvCollect()}})}).then(function(){"
        "el.textContent='生成を開始しています…';"
        "return fetch(window.APP+'/clip_render',{method:'POST',"
        "headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({id:q.get('id'),key:q.get('key'),seg:n,sizes:sizes})});})"
        ".then(function(r){return r.text();}).then(function(st){"
        "if(st!=='started'&&st!=='already_running'){el.textContent='開始できません: '+st;return;}"
        "el.textContent='生成中…（サイズごとに数十秒〜数分）';"
        "var iv=setInterval(function(){"
        "fetch(window.APP+'/clip_render_status?id='+encodeURIComponent(q.get('id'))"
        "+'&key='+encodeURIComponent(q.get('key'))+'&seg='+n)"
        ".then(function(r){return r.text();}).then(function(s){"
        "if(s==='done'){clearInterval(iv);location.reload();}"
        "else if(s.indexOf('failed')===0){clearInterval(iv);"
        "el.textContent='生成失敗（generated/clip_…_render_'+n+'.log を確認）';}});},3000);})"
        ".catch(function(){el.textContent='サーバーに接続できません';});}"
        # 書き出し: チェック済みの全規格を contents/clip/<key>/ へ（原文 L70-71）
        "function cvExport(n){var q=new URLSearchParams(location.search);"
        "var card=document.getElementById('cv'+n);var el=card.querySelector('.cvstat');"
        "var sizes=[].slice.call(card.querySelectorAll('.cvsize:checked')).map(function(c){return c.value;});"
        "if(!sizes.length){el.textContent='書き出しサイズを選んでください';return;}"
        "el.textContent='設定を保存中…';"
        "fetch(window.APP+'/clip_save',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({id:q.get('id'),key:q.get('key'),op:'video-settings',"
        "video:{clips:cvCollect()}})}).then(function(){"
        "el.textContent='書き出しを開始しています…';"
        "return fetch(window.APP+'/clip_render',{method:'POST',"
        "headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({id:q.get('id'),key:q.get('key'),seg:n,sizes:sizes,export:1})});})"
        ".then(function(r){return r.text();}).then(function(st){"
        "if(st!=='started'&&st!=='already_running'){el.textContent='開始できません: '+st;return;}"
        "el.textContent='書き出し中…（サイズごとに数十秒〜数分）';"
        "var iv=setInterval(function(){"
        "fetch(window.APP+'/clip_render_status?id='+encodeURIComponent(q.get('id'))"
        "+'&key='+encodeURIComponent(q.get('key'))+'&seg='+n+'&export=1')"
        ".then(function(r){return r.text();}).then(function(s){"
        "if(s==='done'){clearInterval(iv);location.reload();}"
        "else if(s.indexOf('failed')===0){clearInterval(iv);"
        "el.textContent='書き出し失敗（generated/clip_…_render_'+n+'_export.log を確認）';}});},3000);})"
        ".catch(function(){el.textContent='サーバーに接続できません';});}"
        "</script>")
    return page(f"動画の作成 {idv}", "".join(parts))


# セグメント参考(C-12)の生成プロセス。key=(ID, clipkey) → subprocess.Popen
CLIP_SUGGESTS = {}


def start_clip_suggest(idv, key):
    """セグメント参考（AI 候補）の生成を開始する。再実行＝再生成で丸ごと差し替え（原文 L95）。"""
    import subprocess
    if idv not in list_ids() or not re.fullmatch(r"[0-9a-f]{12}_[0-9a-f]{8}", key or ""):
        return "bad_id"
    k = (idv, key)
    p = CLIP_SUGGESTS.get(k)
    if p is not None and p.poll() is None:
        return "already_running"
    root = os.path.dirname(HERE)
    # openai SDK は README 規約の .venv-openai を優先（無ければ他で試し、
    # スクリプト側が明示エラーを出す）
    cands = [os.path.join(root, ".venv-openai", "bin", "python"),
             os.path.join(root, "venv", "bin", "python"), _sys.executable]
    py = next((c for c in cands if os.path.isfile(c)), _sys.executable)
    base = os.path.join(DATA_DIR, idv)
    gen = idpaths.gen_dir(base)
    logf = open(os.path.join(gen, f"clip_{key}_suggest.log"), "w", encoding="utf-8")
    CLIP_SUGGESTS[k] = subprocess.Popen(
        [py, os.path.join(root, "scripts", "suggest_clips.py"), idv, "--key", key],
        cwd=root, stdout=logf, stderr=subprocess.STDOUT)
    return "started"


def clip_suggest_status(idv, key):
    p = CLIP_SUGGESTS.get((idv, key))
    if p is None:
        return "none"
    if p.poll() is None:
        return "running"
    if p.returncode != 0:
        # 失敗理由（キー無し・SDK無し等）はログの最終行をそのまま UI に見せる
        try:
            gen = idpaths.gen_dir(os.path.join(DATA_DIR, idv))
            with open(os.path.join(gen, f"clip_{key}_suggest.log"), encoding="utf-8") as f:
                lines = [ln for ln in f.read().splitlines() if ln.strip()]
            return "failed:" + (lines[-1][-200:] if lines else str(p.returncode))
        except Exception:
            return f"failed({p.returncode})"
    return "done"


def render_clip_suggestions(idv, key):
    """切り抜き編集画面の見出し直下に出す「セグメント参考」（C-12・原文 L86-95）。"""
    base = os.path.join(DATA_DIR, idv)
    sug = _load_json(idpaths.find(base, f"clip_{key}_suggestions.json"), None)

    def ts2(t):
        m3 = int(t // 60)
        return f"{m3}:{t - m3 * 60:05.2f}"

    items = []
    for it in (sug or {}).get("suggestions", []):
        try:
            s3, e3 = float(it["s"]), float(it["e"])
        except (KeyError, TypeError, ValueError):
            continue
        dm, ds = divmod(int(round(e3 - s3)), 60)
        items.append(
            "<div class='sugitem'>"
            f"<div class='sugtitle'>・{esc(it.get('title'))}</div>"
            f"<div class='sugtime'><a onclick='window.clipTL&&clipTL.setPlayhead({s3:.3f})'>"
            f"{ts2(s3)}〜{ts2(e3)}（{dm}分{ds:02d}秒）</a></div>"
            f"<div class='sugtext'>{esc(it.get('text'))}</div></div>")
    label = "再生成" if items else "セグメント参考を生成"
    body = "".join(items) if items else (
        "<div class='meta'>AI による切り抜き候補（5〜10件・見出し/範囲/全文）をここに出します。</div>")
    js = (
        "<script>"
        "function clipSuggest(){var q=new URLSearchParams(location.search);"
        "var el=document.getElementById('sugstat');var b=document.getElementById('sugbtn');"
        "b.disabled=true;el.textContent='生成中…（1分前後かかります）';"
        "fetch(window.APP+'/clip_suggest?id='+encodeURIComponent(q.get('id'))"
        "+'&key='+encodeURIComponent(q.get('key')),{method:'POST'})"
        ".then(function(r){return r.text();}).then(function(st){"
        "if(st!=='started'&&st!=='already_running'){b.disabled=false;"
        "el.textContent='開始できません: '+st;return;}"
        "var iv=setInterval(function(){"
        "fetch(window.APP+'/clip_suggest_status?id='+encodeURIComponent(q.get('id'))"
        "+'&key='+encodeURIComponent(q.get('key')))"
        ".then(function(r){return r.text();}).then(function(s){"
        "if(s==='done'){clearInterval(iv);location.reload();}"
        "else if(s.indexOf('failed')===0){clearInterval(iv);b.disabled=false;"
        "el.textContent='生成できません: '+s.slice(7);}});},3000);})"
        ".catch(function(){b.disabled=false;el.textContent='サーバーに接続できません';});}"
        "</script>")
    return (
        "<div class='sugbox'><div class='sughd'><b>セグメント参考</b>"
        f"<button class='gbtn' id='sugbtn' onclick='clipSuggest()'>{label}</button>"
        "<span id='sugstat' class='meta'></span></div>"
        f"{body}</div>{js}")


def render_clip(idv, key):
    """切り抜き編集画面（CLIP_PLAN C-2〜C-4）。機能はセグメント決定とテキスト修正の
    2つだけに絞る（原文 L64）。タイムラインは凍結版の編集後時間軸で隙間なく連続。"""
    if idv not in list_ids():
        return None
    base = os.path.join(DATA_DIR, idv)
    src = _load_json(idpaths.find(base, f"clip_{key}_source.json"), None)
    if not src:
        return None
    cur = _load_json(idpaths.find(base, f"clip_{key}.json"), {})
    audio = idpaths.find(base, f"clip_{key}_source.m4a")
    audio_ok = os.path.isfile(audio)
    dur = src.get("duration") or 0
    m, s2 = divmod(int(round(dur)), 60)
    parts = [
        f"<div class='crumb'><a href='{approot()}/id?id={urllib.parse.quote(idv)}'>← 1次編集（{esc(idv)}）</a></div>",
        f"<h1>切り抜き編集　{esc(src['seg'].get('title') or '')}</h1>",
        f"<p class='meta'>凍結版 {esc((src.get('created_at') or '')[:16].replace('T', ' '))}"
        f"　尺 {m}分{s2:02d}秒"
        f"　<a class='gbtn' href='{approot()}/clip_videos?id={urllib.parse.quote(idv)}"
        f"&key={urllib.parse.quote(key)}'>動画の作成 →</a></p>",
        # 見出し直下に AI のセグメント参考（C-12・原文 L86-95）
        render_clip_suggestions(idv, key),
    ]
    if not audio_ok:
        parts.append("<p class='meta' id='srcwait'>凍結音源を生成中です…（できあがると自動で表示が変わります）</p>")
        parts.append(
            "<script>var _iv=setInterval(function(){"
            "fetch(window.APP+'/clip_source_status?id='+encodeURIComponent(new URLSearchParams(location.search).get('id'))"
            "+'&key='+encodeURIComponent(new URLSearchParams(location.search).get('key')))"
            ".then(function(r){return r.text();}).then(function(s){"
            "if(s==='done'){clearInterval(_iv);location.reload();}"
            "else if(s.indexOf('failed')===0){clearInterval(_iv);"
            "document.getElementById('srcwait').textContent='凍結音源の生成に失敗しました"
            "（generated/clip_…_source.log を確認）';}});},3000);</script>")
    else:
        rel = os.path.relpath(audio, DATA_DIR)
        parts.append(f"<audio id='orig' src='{approot()}/media/{urllib.parse.quote(rel)}'"
                     " preload='metadata' style='display:none'></audio>")
    data = json.dumps({"id": idv, "key": key, "duration": dur,
                       "units": cur.get("units") or [],
                       "clips": cur.get("clips") or []},
                      ensure_ascii=False).replace("</", "<\\/")
    parts.append(
        "<div class='cliptl' id='cliptl'>"
        "<div class='tlbar'>"
        "<button class='tlplay'>▶ 再生</button>"
        "<span class='tltime'>0:00.00</span>"
        "<span class='tlkeep'></span>"
        "<button class='tlzout'>−</button><button class='tlzin'>＋</button>"
        "<select class='tlspeed'><option value='1'>1x</option>"
        "<option value='1.35'>1.35x</option><option value='1.5'>1.5x</option></select>"
        "<span class='tlzoom'></span>"
        "<button class='tlundo'>↩ 元に戻す</button><button class='tlredo'>↪ やり直す</button>"
        "<span class='tlstat'>保存済み</span>"
        "</div>"
        "<div class='tlhelp'>Space 再生/停止・<b>S＝切り抜きの開始</b>・<b>E＝終了</b>・"
        "右クリック＝メニュー（再生/開始/終了/この間を詰める/テキスト削除・挿入）・"
        "文字クリックで編集・切り抜きをクリックで選択して Delete で解除・⌘Z 取り消し・⌘± ズーム。"
        "自動保存されます。</div>"
        f"<div class='tlrows'><div class='tlwait'>組み上げ中…（字幕ユニット {len(cur.get('units') or [])}）</div></div>"
        f"<script type='application/json'>{data}</script>"
        "</div>")
    return page(f"切り抜き編集 {idv}", "".join(parts))


# 書き出し中のプロセス。key=(ID, index) → subprocess.Popen
RENDERS = {}


def _seg_index_by_sid(idv, sid):
    seg = _load_json(idpaths.find(os.path.join(DATA_DIR, idv), "segments.json"), {})
    for sg in seg.get("segments", []):
        if sg.get("sid") == sid:
            return sg.get("index")
    return None


def start_render_spec(spec):
    """ブラウザが表示している状態（sid・区間・全カット）をそのまま書き出す。
    segments.json は参照しない＝見ているもの以外が書き出されることは構造的にない。"""
    import subprocess, datetime
    idv = str(spec.get("id") or "")
    sid = str(spec.get("sid") or "")
    if idv not in list_ids() or not sid:
        return "bad_id"
    # 何を書き出したかも受信箱へ完全記録
    try:
        inbox = os.path.join(idpaths.edit_dir(os.path.join(DATA_DIR, idv)), "edit_save_journal.jsonl")
        with open(inbox, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.datetime.now().isoformat(timespec="milliseconds"),
                                "payload": dict(spec, op="export")}, ensure_ascii=False) + "\n")
            f.flush(); os.fsync(f.fileno())
    except Exception:
        pass
    key = (idv, sid)
    p = RENDERS.get(key)
    if p is not None and p.poll() is None:
        return "already_running"
    gen = idpaths.gen_dir(os.path.join(DATA_DIR, idv))
    specp = os.path.join(gen, f"export_spec_{sid}.json")
    with open(specp, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False)
    root = os.path.dirname(HERE)
    py = os.path.join(root, "venv", "bin", "python")
    if not os.path.isfile(py):
        py = _sys.executable
    logf = open(os.path.join(gen, f"render_{sid}.log"), "w", encoding="utf-8")
    cmd = [py, os.path.join(root, "scripts", "export_audio.py"), idv, "--spec", specp]
    if spec.get("denoise"):
        cmd.append("--denoise")
    RENDERS[key] = subprocess.Popen(cmd, cwd=root, stdout=logf, stderr=subprocess.STDOUT)
    return "started"


def start_render(idv, sid):
    """export_audio.py を1セグメントだけバックグラウンドで走らせる。
    対応づけは sid（index は細分化で変わるため。2026-08-08）。"""
    import subprocess
    if idv not in list_ids() or _seg_index_by_sid(idv, sid) is None:
        return "bad_id"
    key = (idv, sid)
    p = RENDERS.get(key)
    if p is not None and p.poll() is None:
        return "already_running"
    root = os.path.dirname(HERE)
    py = os.path.join(root, "venv", "bin", "python")
    if not os.path.isfile(py):
        py = _sys.executable
    logdir = idpaths.gen_dir(os.path.join(DATA_DIR, idv))
    logf = open(os.path.join(logdir, f"render_{sid}.log"), "w", encoding="utf-8")
    RENDERS[key] = subprocess.Popen(
        [py, os.path.join(root, "scripts", "export_audio.py"), idv, "--sid", sid],
        cwd=root, stdout=logf, stderr=subprocess.STDOUT)
    return "started"


def render_status(idv, sid):
    p = RENDERS.get((idv, sid))
    if p is None:
        return "none"
    if p.poll() is None:
        # export_audio.py が書く進捗ファイルから % を返す
        try:
            gen = idpaths.gen_dir(os.path.join(DATA_DIR, idv))
            meta = json.load(open(os.path.join(gen, f"export_progress_{sid}.json")))
            txt = open(os.path.join(gen, f"export_progress_{sid}.txt")).read()
            us = [ln.split("=")[1] for ln in txt.splitlines() if ln.startswith("out_time_us=")]
            done = (int(us[-1]) / 1e6) if us else 0.0
            net = max(0.1, float(meta.get("net") or 0.1))
            stage = meta.get("stage")
            if stage == 1:
                pct = min(45, int(done / net * 45))
            elif stage == 2:
                pct = 55   # ノイズ除去中（進捗が取れないので固定表示）
            else:
                pct = min(99, 70 + int(min(29, done / net * 29)))
            return f"running:{pct}"
        except Exception:
            return "running"
    if p.returncode != 0:
        return f"failed({p.returncode})"
    # 完了したら最新の書き出しファイル名を返す。ページ側はこれで自動ダウンロードさせる
    index = _seg_index_by_sid(idv, sid)
    names = seg_audio_names(idv, index) if index is not None else []
    return "done:" + names[0] if names else "done"


def safe_media_path(rel):
    full = os.path.realpath(os.path.join(DATA_DIR, rel or ""))
    if (full == DATA_DIR or full.startswith(DATA_DIR + os.sep)) and os.path.isfile(full):
        return full
    return None




# ---------- ルーティング ----------
mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("audio/mp4", ".m4a")


def _text(body, code=200):
    return Response(body, status=code, mimetype="text/plain")


def _html(data, code=200):
    return Response(data, status=code, content_type="text/html; charset=utf-8")


@app.get("/")
def route_index():
    return _html(render_index())


@app.get("/id")
def route_id():
    content = render_id(request.args.get("id") or "")
    if content is None:
        return _html(page("404", f"<h1>404</h1><a href='{approot()}/'>一覧へ</a>"), 404)
    return _html(content)


@app.get("/decide")
def route_decide():
    ok = apply_decision(request.args.get("id") or "",
                        request.args.get("cid") or "",
                        request.args.get("action") or "",
                        request.args.get("status_only") == "1")
    return _text("ok" if ok else "ng", 200 if ok else 400)


@app.get("/production")
def route_production():
    ok = set_seg_flag(request.args.get("id") or "", request.args.get("sid") or "",
                      "production", request.args.get("on") == "1")
    return _text("ok" if ok else "ng", 200 if ok else 400)


@app.get("/delivered")
def route_delivered():
    ok = set_seg_flag(request.args.get("id") or "", request.args.get("sid") or "",
                      "delivered", request.args.get("on") == "1")
    return _text("ok" if ok else "ng", 200 if ok else 400)


@app.post("/clip_create")
def route_clip_create():
    key = create_clip(request.args.get("id") or "", request.args.get("sid") or "")
    return _text("ok:" + key if key else "ng", 200 if key else 400)


@app.get("/clip")
def route_clip():
    content = render_clip(request.args.get("id") or "", request.args.get("key") or "")
    if content is None:
        return _html(page("404", f"<h1>404</h1><a href='{approot()}/'>一覧へ</a>"), 404)
    return _html(content)


@app.post("/clip_suggest")
def route_clip_suggest():
    st = start_clip_suggest(request.args.get("id") or "", request.args.get("key") or "")
    return _text(st)


@app.get("/clip_suggest_status")
def route_clip_suggest_status():
    return _text(clip_suggest_status(request.args.get("id") or "",
                                     request.args.get("key") or ""))


@app.post("/clip_render")
def route_clip_render():
    try:
        d = request.get_json(force=True) or {}
        st = start_clip_video_render(str(d.get("id") or ""), str(d.get("key") or ""),
                                     d.get("seg"), [str(s) for s in (d.get("sizes") or [])],
                                     export=bool(d.get("export")))
    except Exception:
        st = "bad_request"
    return _text(st)


@app.get("/clip_render_status")
def route_clip_render_status():
    return _text(clip_video_render_status(request.args.get("id") or "",
                                          request.args.get("key") or "",
                                          request.args.get("seg"),
                                          request.args.get("export") == "1"))


@app.get("/clip_videos")
def route_clip_videos():
    content = render_clip_videos(request.args.get("id") or "", request.args.get("key") or "")
    if content is None:
        return _html(page("404", f"<h1>404</h1><a href='{approot()}/'>一覧へ</a>"), 404)
    return _html(content)


@app.post("/clip_save")
def route_clip_save():
    try:
        ok = apply_clip_save(request.get_json(force=True) or {})
    except Exception:
        ok = False
    return _text("ok" if ok else "ng", 200 if ok else 400)


@app.get("/clip_source_status")
def route_clip_source_status():
    idv, key = request.args.get("id") or "", request.args.get("key") or ""
    if idv not in list_ids() or not key:
        return _text("ng", 400)
    base = os.path.join(DATA_DIR, idv)
    if os.path.isfile(idpaths.find(base, f"clip_{key}_source.m4a")):
        return _text("done")
    p = CLIP_SOURCE_RENDERS.get((idv, key))
    if p is not None and p.poll() is None:
        return _text("running")
    if p is not None and p.returncode != 0:
        return _text(f"failed({p.returncode})")
    return _text("none")


@app.get("/render_status")
def route_render_status():
    return _text(render_status(request.args.get("id") or "",
                               request.args.get("sid") or ""))


@app.get("/media/<path:rel>")
def route_media(rel):
    # 本番は nginx が /podcast/media/ を直接配信するのでここへは来ない。
    # ローカル(Flask 単体)用。conditional=True で Range(音源シーク)に応える
    full = safe_media_path(rel)
    if full is None:
        return _text("not found", 404)
    return send_file(full, conditional=True)


@app.post("/render_seg")
def route_render_seg():
    try:
        st = start_render_spec(request.get_json(force=True) or {})
    except Exception:
        st = "bad_request"
    return _text(st)


@app.post("/edit_save")
def route_edit_save():
    try:
        ok = apply_timeline_save(request.get_json(force=True) or {})
    except Exception:
        ok = False
    return _text("ok" if ok else "ng", 200 if ok else 400)


if __name__ == "__main__":
    print(f"[podcast-web] http://127.0.0.1:{PORT}/  (data: {DATA_DIR})")
    app.run(host="127.0.0.1", port=PORT, threaded=True)
