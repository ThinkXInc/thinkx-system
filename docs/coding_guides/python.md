# python 規約(infra)

一般的な python スタイルは `thinkx_coding_guide.md`(Python 節・Google Style)。重複は書かず参照する。
一般原則は genral.md。本書は infra 固有の追加のみ。

## いつ python にするか
- 分岐・ループ・状態・検証・エラー処理が要るものは bash に書かず python にする。bash は読みにくくエラーを頻発させる。
- setup_*.sh は linear の bash のまま。そこに要るロジックだけ python の小ツールに切り出し、setup の前段(preflight)や別ツールとして実行する。

## preflight パターン(例: check_deploykey.py)
- 外部依存(人手の GitHub 登録等)は「文書に前提として書く」でなく機械的に検証し、不足を表示。
- setup 本体に埋め込まず独立コマンドで実行 → 出力の最終行が結果(埋もれさせない)。
- 戻り値 0/1。`sys.exit(main())` は自プロセスの終了コード設定で ssh は切らない。呼び出し側 bash は `|| { …; false; }`。

## 実務メモ(踏んだ罠)
- `subprocess.run` は `input=` と `stdin=` を併用できない → input を渡す呼びだけ stdin を付けない。
- 型注釈で `X | None` を使うなら `from __future__ import annotations`(EC2/Mac の python3.9 互換)。
