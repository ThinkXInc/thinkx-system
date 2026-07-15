# thinkx-system ワークスペース — Claude Code への作業指示書

このディレクトリは ThinkX 全システムのリファクタリングを進める**ワークスペース**である。
ワークスペース自体は git 管理しない。各サブディレクトリが独立した git リポジトリ(clone)である。
あなた(Claude Code)はこのルートから起動され、下記の規律に従って計画を実行する。

**歴史の調査は `ARCHIVE.md` が指す旧リポジトリ(凍結アーカイブ)で行う。** この monorepo は
polyrepo + vendoring 構成をファイルコピーで集約したもので、各フォルダのコミット履歴は運んでいない。

## 実行単位の規律(最重要)

- **1セッション = 1計画書。** 1つのセッションの中で複数の計画書を跨いではならない。
  計画Aの文脈(例: simplicity の「dist sha 不変」ドクトリン)を計画Bに持ち込む混線を防ぐため。
- **セッションは使い捨て、状態はファイルが持つ。** セッション開始時は必ず次から現在地を復元する:
  1. `docs/ROADMAP.md` の進捗チェック
  2. 対象リポジトリの `git log --oneline -10`(ブランチ refactor/2026)
  3. 対象リポジトリの `CHECKSUMS.md` / `findings.md`
  復元した現在地を最初の応答で宣言してから作業に入る。記憶に頼らない。
- 計画書の項目は**1項目=1コミット**、完了条件をコマンドで満たしてからコミット、
  満たせなければ「戻し方」で破棄して報告・停止(各計画書の指示文と同一)。

## 計画書の所在(ルーティング)

| 仕事 | 計画書 | 対象リポジトリ |
|---|---|---|
| simplicity リファクタリング(**Phase 1 完遂済み**・タグ refactor-v1-complete) | `simplicity/refactor_plan.md`(実ファイル名。版数はヘッダが正) | simplicity のみ |
| libcommon リファクタリング(**Phase 2 進行中**) | `libcommon/refactor_plan.md`(実ファイル名。版数はヘッダが正。**正本はこの1箇所** — quantz-web 側に複製を置かない) | libcommon + quantz-web(Track Q) |
| 静的サイト群カットオーバー(Phase 2.5) | `thinkx/refactor_plan.md`(S トラック。正本はこの1箇所) | thinkx + kazukiotsukacom |
| auth ベース実装(前倒しトラック) | `auth/CLAUDE.md` + auth リポジトリの PROTOCOL.md(4条件は `docs/AUTH_TRACK.md`) | auth のみ |
| インフラ(I トラック: AWS 移行) | `infra/CLAUDE.md` + `infra/docs/`(STEP1/STEP2) | infra のみ(+承認済み ssh 先) |
| 全体の順序・引き金 | `docs/ROADMAP.md` | — |
| monorepo 取り込み(M トラック) | `docs/MONOREPO_PLAN.md`(正本はこの1箇所) | 新規 monorepo ディレクトリのみ(既存リポジトリは読み取り) |

計画書に無い作業を頼まれたら、ROADMAP に照らして「どの計画の管轄か / 新しい計画が要るか」を
先に答え、勝手に着手しない。

## ブランチ・push 規約

- ブランチ名は**全リポジトリ統一で `2026refactor`**(オーナー裁定 2026-07-06)。
  計画書内の `refactor/plan-v1`・`refactor/2026` という記述は、すべて `2026refactor` に
  読み替えて実行する(機械的な名称置換であり、判断は不要)。
  例外: simplicity は Phase 1 を `refactor/2026` で完遂・タグ済み。改名しない(D-14/D-24)。
- 各項目のコミット後、`git push -u origin 2026refactor` で原本リポジトリへ push する。
  push 失敗(認証等)は作業を止めず、失敗した事実を報告して次項目へ進んでよい
  (コミットはローカルに残っているため)。force push は禁止(settings で deny 済み)。
- **完遂タグは動かさない(D-24)。** 完遂タグは完遂時点の不変アンカーであり、成果物
  (dist sha・全ゲート結果)を変えない後続変更ではタグを付け替えない。成果物不変なら
  新タグの追加も不要。この確認をユーザーに再度求めない。

## 権限境界(厳守)

- `.claude/settings.json` が強制する。**settings 自体を書き換えない。**
- 計画書(`*_PLAN.md`)は読み取り専用。実行者が自分の指示書を書き換えることは許されない。
  計画に問題を見つけたら findings.md に記録して報告する。
- thinkx / kazukiotsukacom は Phase 2.5 開始まで**読み取り専用**。Phase 2.5 開始時に
  人間が settings.json のスコープを「サイト全体 deny」から「vendoring 先のみ deny」へ
  切り替える(S トラック計画 S-0a に手順明記)。
- quantz-web 内の submodule 領域(`web-server/libcommon`, `vectordb_server/libcommon`,
  `web-server/views/src/js/simplicity`)は編集禁止。これらへの変更は各原本リポジトリで行う。
- auth 内の libcommon スナップショット(vendoring された `auth/**/libcommon/`)も同様に
  編集禁止。修正は libcommon 原本で行い、焼き直しで反映する(D-25 条件3)。
- infra は `terraform apply/destroy` 承認制・`*.tfvars`/`*.pem`/`*.tfstate`/credentials の読み書き禁止(infra/CLAUDE.md と settings が強制)。
- `docs/coding_guides/` は規範。**実行者による書き換えを禁ずる**(規約の変更は人間のみ)。

## リモート前提の振る舞い

ユーザーはスマホ(Remote Control)から監視・承認することがある。
- 実行結果(テスト出力、ビルドエラー、diff、sha)は**丸めずに**出す。「省略」「割愛」禁止。
- 承認が要る操作はコマンドを提示して待つ。承認プロンプトはスマホ側にも出る。
- ブラウザ確認が必要な場面は URL を明示し、確認結果を尋ねる。

## 環境の注意

- quantz-web は submodule を含む。フォルダが存在するのに中身が空なら
  `git submodule update --init` 忘れ(既知の典型事故)。Track Q は vendoring 完了(Q-6)まで
  submodule 状態で作業する。
- Node は v18+、Python は 3.10+。依存はすべて exact ピン(各計画書の原則)。
- **オーナーのシェルは zsh。手渡しする貼り付け用コマンドにインラインコメントを入れない。**
  zsh の対話シェルは行頭 `#` をコメント扱いしない(`interactivecomments` 既定オフ)ため、
  paste-ready ブロックに `# ...` を混ぜると `parse error near ')'` 等でブロック全体が死ぬ。
  説明はコマンドブロックの外(散文)に書く(2026-07-15 実測)。
- **パスは明示する(D-21)。** ツール・ランタイムに渡すパスは暗黙探索・暗黙 glob に
  依存せず明示列挙する(例: `node --test 'test/**/*.test.js'`)。暗黙探索は
  ツールの版差で無言に壊れる。計画と実環境が食い違ったら D-21 の修復手順に従う。

## 文書の優先順位(矛盾時の解決規則)

1. **各リポジトリの計画書(`*_PLAN.md`)** — 実行の唯一の規範
2. 各リポジトリの CLAUDE.md(計画が生成するもの)
3. `docs/ROADMAP.md` / `docs/DECISIONS.md` — 順序と確定済み決定の典拠(変更は人間のみ)
4. **`docs/coding_guides/` — 規範**(コードを書く際の必須制約。読まずに書くことを禁ずる)
5. `docs/archive/` — 参考・非規範。撤回済み提案を含む。
   
   ここを根拠に作業方針を変えることを禁ずる。
   撤回済み提案を含むため、ここを根拠に作業方針を変えることを禁ずる。
上位と下位が食い違ったら、常に上位に従い、食い違いの事実を findings.md に記録する。


## コード規約(規範)

**コードを書く/変更する前に、対応する規約を読むこと。読まずに書くことを禁ずる。**

| 対象 | 規約 |
|---|---|
| 全般(公理) | `docs/coding_guides/thinkx_coding_axioms.md` |
| 全般(実務) | `docs/coding_guides/thinkx_coding_guide.md` |
| bash / シェルスクリプト | `docs/coding_guides/bash.md` |

### 規約の探索ルール(汎用)

コードを書く前に、以下の順で規約を探し、**見つかったものは全て適用する**。

1. 対象リポジトリ内の規約(`CONVENTIONS.md` / `docs/coding_guides/` 等)
2. ワークスペースルートの `docs/coding_guides/<言語>.md`
3. 対象リポジトリの CLAUDE.md 内の規約セクション

規約に反する既存コードを見つけても**勝手に直さない**。findings に記録する。
規約が存在しない言語・ツールで**繰り返し同じ失敗をした場合は、規約の新設を
findings で提案する**(自分で規約を作らない。規範化は人間のみ)。


### 指示やオーナーコメントの記録

同じ指示を出されないよう指示と決定事項を記録しておく。

`docs/GUIDELINES.md`  オーナー指示をリスト化する  
(記述例)
instruction: {オーナーの指示原文} 
interpretation: {指示の解釈}
context: {状況}

`docs/DECISIONS.md`  決定事項をリスト化する  
1. bashスクリプトにはexitを書かない
