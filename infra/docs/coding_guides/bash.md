# bash 規約(infra)

観測系/変更系の基本はワークスペース規範 `../../../docs/coding_guides/bash.md`。重複は書かず参照する。
一般原則は genral.md。本書は infra 固有の追加のみ。

## setup_*.sh(最重要・オーナー裁定)
- 元 raw doc(docs/raw)をほぼ逐語で実行ファイル化。1 script = 1 元 doc。
- 上から流すだけの linear。**if / for / case / 関数 / set -e を使わない**。→ ほぼそのまま Dockerfile の RUN に変換できるように。
- ロジックが要るなら bash でなく python(python.md)。逐語から外す変更は勝手にやらず理由付きで尋ねる。
- ヘッダは 名前1行 + prerequisites 箇条書きのみ。見出しは短い動詞句(`# clone repository` `# systemd`)。

## verify(末尾に色で成否)
setup_ と run/ の末尾に `# verify`。本質的な成功条件を判定し色付きで出す(冒頭に何をするかの echo も)。
- 緑=OK / 赤=FAIL / 黄=WARN。基本は緑/赤の2色。
- Dockerfile 移植可のため `printf` リテラル ANSI + インライン `&&/||` のみ(if/for/関数/set -e/exit なし・echo -e 不可)。
- 常に終了コード 0(色は情報表示)。
```
systemctl is-active --quiet nginx && printf '\033[32mOK: nginx\033[0m\n' || printf '\033[31mFAIL: nginx %s\033[0m\n' "$(systemctl is-active nginx)"
```
- uwsgi は is-active=active でもアプリ未ロードのことがある → restart/run では journal 末尾も出す(`journalctl -u <svc> -n 15 --no-pager`)。
