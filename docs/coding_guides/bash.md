# bash コード規約

## 分類（これを最初に決める）
スクリプトは2種類。**どちらかを冒頭コメントで宣言する。**

- **観測系**(status / plan-summary / logs / check): 見るだけ。状態を変えない
- **変更系**(setup / deploy / restart): 状態を変える

## 観測系の規則（落とさないことが最優先）

- **`exit` 禁止** → 全処理を関数に包み `return` を使う
  理由: `source` されると `exit` は呼び出し元のシェルを終了させる
- **`set -e` / `set -u` / `set -o pipefail` 禁止**
  理由: source 時に呼び出し元シェルに残る。かつ1コマンドの失敗で全体が死ぬ
- **`cd` はサブシェルに閉じる** `(cd dir && cmd)`
  理由: source 時に呼び出し元の pwd を変えてしまう
- 外部コマンド呼び出しは失敗を握りつぶす: `cmd 2>/dev/null || true`
- 依存コマンドは `command -v x >/dev/null || { echo "..."; return 0; }` で確認
- スクリプトパスは `${BASH_SOURCE[0]:-$0}`(source/直接実行の両対応)
- パイプで変数を失わない: `while ... done < <(cmd)` (プロセス置換)

## 変更系の規則（失敗したら止まることが最優先）

- **`set -euo pipefail` を使う**(観測系と逆)
- ただし `source` されない前提。冒頭に `#!/usr/bin/env bash` と実行前提を明記
- 破壊的操作の前に確認・バックアップ

## 共通

- 冒頭に用途・使い方・分類をコメントで書く
- shellcheck を通す
- 問題があるなら黙って何もしないのでなく何かヒントを出力
- 引数を自然に (英語の動詞への目的語のようなSVOCなどに照らして不自然にならないよう)

## 移植性(macOS 対応)

**macOS の標準 bash は 3.2**(ライセンス上 Apple が更新していない)。
bash 4+ の機能は使えないとき:
- **連想配列 `declare -A`** → `case` 関数で代替する
```bash
  __hourly() { case "$1" in t3.micro) echo 0.0104 ;; *) echo 0 ;; esac; }
```
- `${var,,}` / `${var^^}`(大文字小文字変換) → `tr` を使う
- `mapfile` / `readarray` → `while read` を使う
- `&>>`(追記リダイレクト) → `>> file 2>&1`

## 数値計算

- **`$(( ))` は整数のみ**。金額・レート等の小数は必ず `bc -l` を使う
  (`$(( 0.0104 * 730 ))` は落ちる)

## 1スクリプト1操作 / 引数で指定する

**指示原文(2026-07-21)**

> というか、実際に起きていることはかなりもっと複雑なので、そのまま名前に反映させるべきです。というか、そのスクリプトはいろいろな操作が混ざりすぎている。
> pr_and_merge_to_develop.sh monorepo と打つとまず monorepoからdevelopへのprが作成されmergeまで行われる ここまでが1スクリプト
> 次に deploy_staging_from.sh monorepo を叩くと staging web , LB をdevelopに合わせる

> ローカルの作業ブランチ取り込みたいのが必ずしもモノレポブランチとは限らない。というか、そういう話だったか。モノレポブランチを必ず経由するという議論は特にしていないように記録しているが。デプロイステージングフロム、ローカルブランチとして、そのブランチの名前は指定するようにした方がいいんじゃないのか。

> これらをまず作ってから、それらを統合したスクリプトとしてdeploy_staging_from_monorepo.sh とし そこでの説明は
> bash pr_and_merge_to_develop.sh monorepo
> bash deploy_staging_from.sh monorepo
> を実行する
> とシンプルにする

> いっぺんに全部リスタートはやめた方がいいので、全部やるなら全部引数に指定して直列で叩くということを唯一の方法とすべきだろう。引数が何もなかったら指定してくれとアラートを出すべきだろう。

**NG**

```bash
# 1本に戻し・PR・merge・サーバー反映・確認が入っている
bash deploy_staging_from_monorepo.sh
```

```bash
# 既定値を置いて branch を省略できるようにする
local src="${1:-monorepo}"
```

```bash
# 引数が無いと全部を対象にする
[ "$#" -eq 0 ] && set -- thinkx transformism kazukiotsukacom
```

**OK**

```bash
# 操作ごとに1本。branch は必ず引数で指定する
bash pr_and_merge_to_develop.sh monorepo
bash deploy_staging_from.sh monorepo
```

```bash
# まとめたいときは、上の2本を呼ぶだけの薄い1本にする
deploy_staging_from_monorepo() {
  bash infra/scripts/pr_and_merge_to_develop.sh monorepo || return 1
  bash infra/scripts/deploy_staging_from.sh monorepo || return 1
}
```

```bash
# 引数が無ければ何もせず、指定を促す
if [ "$#" -eq 0 ]; then
  printf '%b\n' "${Y}branch を指定してください。${Z}"
  echo "  使い方: bash infra/scripts/deploy_staging_from.sh <branch>"
  echo "  例:     bash infra/scripts/deploy_staging_from.sh monorepo"
  return 1
fi
```
