#!/usr/bin/env python3
"""data/ のファイル・フォルダ名を NFC に正準化する(D-52・2026-09-17)。

なぜ: macOS はファイル名を NFD(分解形)で保存し、git は NFC(合成形)に変換して運ぶ。
2つの経路(git = edit/、tar 同期 = 音源・生成物)で形が違うと、Linux サーバー上で
「見た目同名・実体別」のフォルダに分裂する(2026-09-17 に実際に起きた)。
源流(この data/)を NFC に揃えれば、git も tar も同じ名前を運ぶ。

usage:
  python3 scripts/normalize_data_names.py --check <dir>   NFD 名を列挙(あれば exit 1)
  python3 scripts/normalize_data_names.py --fix   <dir>   NFC へリネーム(衝突があれば exit 1)

衝突(NFC 形の名前が既に存在する)は自動では畳まない。中身の統合は人間の判断が要る。
"""
import os
import sys
import argparse
import unicodedata


def find_non_nfc(root):
    """NFC でない名前を (親ディレクトリ, 名前) で深い順に返す(リネームは深い方から)。"""
    out = []
    for r, dirs, files in os.walk(root):
        for name in files + dirs:
            if unicodedata.normalize("NFC", name) != name:
                out.append((r, name))
    out.sort(key=lambda t: t[0].count(os.sep), reverse=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("root")
    args = ap.parse_args()
    if args.check == args.fix:
        print("--check か --fix のどちらかを指定する")
        return 2
    root = os.path.realpath(args.root)
    if not os.path.isdir(root):
        print(f"[nfc] {root} が無い")
        return 2

    targets = find_non_nfc(root)
    if not targets:
        if args.check:
            print("[nfc] すべて NFC(問題なし)")
        return 0

    conflicts = []
    for r, name in targets:
        nfc = unicodedata.normalize("NFC", name)
        src, dst = os.path.join(r, name), os.path.join(r, nfc)
        rel = os.path.relpath(src, root)
        # 衝突判定は exists() を使わない。macOS の APFS は NFC/NFD を同一視して照合する
        # ため、NFC 名の問い合わせが NFD の実体に命中して常に「存在する」と誤検出する。
        # 実体が別かどうかは、親フォルダの一覧に NFC のバイト列が実際に載っているかで見る
        if nfc in os.listdir(r):
            conflicts.append(rel)
            print(f"[nfc] 衝突(NFC形の別実体が存在・手動で統合が必要): {rel}")
            continue
        if args.check:
            print(f"[nfc] NFD: {rel}")
        else:
            # macOS は同一視のため直接 rename では保存形が変わらないことがある。
            # 一時名を経由して確実に NFC のバイト列で保存し直す
            tmp = os.path.join(r, ".nfc_tmp__" + nfc)
            os.rename(src, tmp)
            os.rename(tmp, dst)
            print(f"[nfc] 正規化: {rel}")

    if conflicts:
        return 1
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
