# 一般コーディング規約(infra)

原則は同ディレクトリの `thinkx_coding_axioms.md` / `thinkx_coding_guide.md`。重複は書かず参照する。
コメント量は guide「コメントはどの程度書くべきか」に従う(名前で語らせ、空白行で区切った塊の頭に短いコメント)。
本書は infra 固有の追加のみ。bash は bash.md、python は python.md。

## コメントの書き方
原則は guide「コメントはどの程度書くべきか」。見出しコメントは**短い動詞句だけ**。
理由・凡例・別名の解説を括弧で足さない。補足が要るなら行を分け最小限に。

```
# NG
# verify  (緑=active / 赤=それ以外。未セットアップのサービスは赤=未起動として出る)
# restart web (supercom2)  — uwsgi + nginx を restart し、末尾に色で各サービスの状態を出す
# COPYFILE_DISABLE=1: Mac の ._ 拡張属性を tar に入れない(Linux 側 xattr 警告の抑止)

# OK
# verify
# restart web
# COPYFILE_DISABLE: Mac 拡張属性を除く
```

## 手順(そのまま上から実行できる形)
- 実行マシン/ディレクトリの切替は実行行(`cd` / `ssh host '…'`)で示す。地の文で示さない。先頭に起点。
- 結果は最終行に出す(人はログを追わない)。
- 複数行ペーストは行が結合し得る → 壊れて困るものは単一行にする。

## 秘密
- 鍵・.env は `infra/{deploykeys,certs,env}/`(.gitignore)に置き、`etc/push_secrets.sh` で配る。名前で隠さない。

## シェルの罠
- `cmd > file` は cmd 失敗時も file を 0 byte に truncate する → temp に受け `[ -s tmp ] && mv`。
