# monorepo 取り込み計画書(M トラック) v1.0

対象: thinkx-system ワークスペース全体の monorepo 化。正本はこの1箇所。
方式: **ファイルコピー**(裁定済み: 歴史は運ばない。歴史の調査は旧リポジトリ(凍結アーカイブ)で行う)。
構成: 現ワークスペースのフォルダ構成を**ほぼそのまま**1つの git リポジトリにする。

## 目的

polyrepo + vendoring 構成を単一リポジトリに集約し、
「staging EC2 で全サイト run → 全ゴールデン green → master マージ = EC2 カットオーバー」
の器を作る。以後のサイト編集(セッションブランチ → PR → rebase マージ → prod)は
この monorepo 上で行う。

## 前提(開始条件)

- S2 トラック完了(transformism vendoring + ゴールデン green)
- thinkx / kazukiotsukacom / transformism / libcommon / simplicity / auth / infra の
  取り込み元 ref を人間が指定する(既定: サイト群と libcommon は `2026refactor` HEAD。
  それ以外は人間が明示。**実行者は勝手に ref を仮定しない**)
- 取り込み対象外: quantz-web(裁定済み: 後続。新システム設計時に判断)

## 禁止事項

- 取り込み時のコード変更。コピーは無加工(例外は M-3 の submodule メタデータ除去のみ)
- 旧リポジトリへのあらゆる書き込み(凍結宣言 README の追加も人間作業)
- ゴールデンの再生成(sweep が落ちたら記録して停止 — コピー起因の欠落を疑う)
- tfvars / pem / credentials / tfstate の monorepo への持ち込み(M-4 で機械検査)

## 手順

### M-0: 出所の確定と記録

- [ ] 各リポジトリの取り込み ref と HEAD SHA を一覧化し、人間の承認を得る
- [ ] 各リポジトリの作業ツリーが clean(未コミット変更なし)であることを確認。
      dirty なら停止して報告

### M-1: 器の作成

- [ ] 新規ディレクトリで `git init`(ブランチ名 master)
- [ ] ワークスペース制御文書(ルート CLAUDE.md / docs/ROADMAP.md / docs/DECISIONS.md /
      .claude/settings.json / bootstrap.sh 等)をルートに配置し、最初のコミットとする
- [ ] `ARCHIVE.md` をルートに新設: フォルダ → 旧リポジトリ URL・取り込み ref・SHA・日付の
      対応表(M-2 で1行ずつ埋める)。CLAUDE.md に「歴史の調査は ARCHIVE.md の旧リポジトリで行う」
      と1行追記

### M-2: リポジトリごとの取り込み(1リポジトリ = 1コミット)

各リポジトリについて順に:

- [ ] 指定 ref の作業ツリーを `.git` を除いてコピー(`rsync -a --exclude=.git`)
- [ ] submodule(thinkx/playbooks・transformism/www/playbooks)は**実体ファイルとして焼き込む**
      (ピン先 SHA の作業ツリーをコピー。未 populate なら populate してからコピー —
      旧リポジトリ側での populate は読み取り扱いで許可)
- [ ] コミットメッセージに出所を刻む: `import <repo> @ <ref> <sha>`
- [ ] ARCHIVE.md に対応行を追記(同一コミットに含める)

### M-3: submodule メタデータの除去と整合

- [ ] 各フォルダ内の `.gitmodules` を削除(monorepo に submodule は存在しない)
- [ ] 各リポジトリ由来の `.gitignore` を確認し、monorepo で衝突・過剰無視が
      ないか点検(パス前提が変わるため)。修正は最小限・findings に記録
- [ ] 旧リポジトリ内で相互参照している相対パス・URL(あれば)を grep で洗い、
      発見のみ記録(修正は人間判断)

### M-4: 秘密情報の機械検査(初 push 前・必須)

- [ ] `git ls-files` 全件に対し tfvars / pem / key / credentials / .env / tfstate を検査
- [ ] `.env.example` 等の雛形は許可、実体は検出したら即停止・報告
- [ ] ルート .gitignore に秘密パターンを集約

### M-5: 全サイト一括 sweep

- [ ] thinkx / kazukiotsukacom / transformism をローカル起動し、
      各 `web-server/tests/golden/` の全ルートを curl 照合、全 green を確認
- [ ] simplicity / libcommon / auth の既存テストゲートを実行、green を確認
- [ ] 落ちた場合: ゴールデンは触らず、コピー欠落・パス前提の破れを疑って findings に記録・停止

### M-6: GitHub へ push(人間の承認後)

- [ ] 人間が GitHub に新リポジトリ(private)を作成(人間作業 — 実行可能形式の手順を
      完了報告に含めること)
- [ ] remote 設定 → push、成否を報告冒頭に明記
- [ ] PR マージ方式を Rebase and merge のみに設定(人間作業・同上)

### M-7: 完了処理

- [ ] 完了報告: 取り込み一覧(ARCHIVE.md 全文)・sweep 結果・秘密検査結果・残課題
- [ ] 旧リポジトリの凍結(README への凍結宣言 + GitHub の Archive 設定)は人間作業 —
      実行可能形式の手順を完了報告に含めること。**凍結の実施タイミングは
      EC2 カットオーバー完了後**(それまで旧本番の緊急修正余地を残す)

## 完了判定

M-5 全 green + M-6 push 完了 + ARCHIVE.md 全行記入。

## この計画の後工程(参考・範囲外)

staging EC2 で monorepo を clone → 全サイト run → sweep green →
EC2 カットオーバー(DNS 切替)→ 旧リポジトリ凍結 →
以後のサイト編集は E トラック(編集ワークフロー規範)に従う。
