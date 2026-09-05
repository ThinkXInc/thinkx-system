# 本番反映の承認レベル(DEPLOY_APPROVAL_LEVELS)

本番へ出す操作を「誰が引き金を引けるか」で段階化した定義。正本はこの1箇所。
デプロイ手順そのものは `infra/docs/デプロイ手順書.md`、経路の索引は `CLAUDE.md`
「デプロイ経路のルーティング」にある。ここが決めるのは**引き金の権限だけ**である。

現在のレベル: **L2b**(オーナー裁定 2026-08-07)。

## なぜレベルにするか

2026-08-07 まで本番へ出せるのはオーナー機だけだった(L3)。理由は
`docs/SITE_EDIT_WORKFLOW.md` の「本番反映は GitHub マージ権限(人間のアカウント)が
必須のため、URL 共有相手は本番に触れない(構造的ゲート)」である。
一方でオーナー機が常時ネットに繋がっている保証はなく、スマホから承認できないと
反映が止まる。**固定の強度ではなく、状況に応じて上下させる**ためにレベル化する。

## レベル

| Lv | staging がやること | マージする人 | staging に置く credential | 承認の担保 |
|---|---|---|---|---|
| L3 | 何もしない | オーナー(自機) | なし | — |
| **L2b** | **push まで。マージ用 URL を提示** | **オーナー(GitHub 上・スマホ可)** | **deploy key(write) のみ** | **GitHub の権限による強制** |
| L2a | push + PR 作成 + マージ | staging のセッション | deploy key(write) + API token | セッション内の承認(規律) |
| L1 | 上記 + 検証 green で自動マージ | 誰も(自動) | L2a と同じ | 事前承認(レベル選択自体) |
| L0 | 検証なしで即時 | 誰も(自動) | L2a と同じ | なし |

**L2a / L1 / L0 は現時点で採用しない。** 定義だけ置く。L1 へ下げる場合は、受け入れ
sweep が全 green のときだけ merge する条件を先に実装してからにする(条件なしの
自動反映は L0 であり、L1 を名乗ってはいけない)。

### なぜ L2a でなく L2b か(オーナー裁定 2026-08-07)

1. **承認が規律でなく権限で強制される。** L2a の「セッション内で承認を得る」は実行者が
   守る約束にすぎず、破れば通る。L2b はオーナーのアカウントでしかマージできない
2. **staging に置く秘密が減る。** PR の作成・マージは GitHub REST API であり、SSH の
   deploy key では**呼べない**(deploy key は git 操作専用)。L2a には別途 API token が要り、
   staging が侵害されたときリポジトリ全体を操作できる鍵になる。L2b は deploy key だけ
3. **オーナーの手数がほぼ変わらない。** スマホの GitHub でマージを押すだけで、以降は
   本番の `deploy-timer@prod.timer` が 60 秒以内に反映する。オーナー機を開く必要はない

## レベルを決めるスイッチ

**write 権は「PR を出すだけ」の運用でも必要である。** PR を作るにはブランチが origin に
存在しなければならず、push はリポジトリへの書き込みだからである。要否を分けるのは
「マージするか」ではなく「push するか」。

さらに **deploy key はブランチを限定できない**(権限はリポジトリ単位)。「develop にだけ
push 可」という設定は存在しないので、**`production` の保護は branch protection 側で行う**。

| | staging の deploy key | `production` の branch protection | 結果 |
|---|---|---|---|
| L3 | read-only | 任意 | staging は何も push できない |
| **L2b** | **write** | **Require a pull request before merging** | staging は develop / release を push できるが production には直接 push できない。マージはオーナーのみ |
| L2a | write + API token | 同上 | staging がマージまで行える |

**上げ方(L2b → L3)**: 当該 deploy key の write を外す(GitHub の UI では既存キーの
権限を変更できないため、削除して read-only で登録し直す)。それだけで staging は
即座に本番へ触れなくなる。スクリプトを消す必要も、この文書を書き換える必要もない
(「現在のレベル」行だけ直す)。**staging のセッション URL を非開発者に渡す期間は
L3 に戻すこと。**

**下げ方(L3 → L2b)**: 先に `production` の branch protection を入れ、**その後で** write を
付ける。逆順だと、保護が無い状態で write が付いている時間ができる。

## L2b の運用規律(実行者=Claude Code が守る)

1. **勝手に出さない。** オーナーが「本番反映」と明示した場合にのみ push する。
   過去の指示は次回に持ち越さない(1 反映 = 1 指示)。最終承認はオーナーのマージであり、
   実行者は**マージ可能な状態を用意するところまで**を担う。
2. **マージを求める時は、出す内容を丸ごと見せる。** 対象 sha、
   `origin/production..origin/develop` のコミット一覧、再起動されるサービス名。
   丸めない・省略しない。
3. **実行前に宣言する。** 宣言と push を同一メッセージで行わない
   (`docs/GUIDELINES.md`「状態を変える操作は実行前に宣言する」)。
4. **staging で目視できる状態にしてからマージを求める。** 確認 URL
   (`https://staging.thinkxinc.com/...`)を必ず添える。見ていないものをマージさせない。
5. **release ブランチを切ってからマージ URL を出す。** develop を直接マージ対象にしない。
   凍結と巻き戻しの単位が失われるため(オーナー機の
   `deploy_production_from_staging.sh` と同じ形にそろえる)。
   **URL は markdown のリンクで出す。コードブロックに入れない**
   (コードブロックの中はコピー用でタップできない。オーナーはスマホで開く)。
   staging・本番の確認 URL も同じ。
6. **マージ後は本番 URL に対して実測し、結果を報告する。** 「出しました」で終えない。
   反映は本番の `deploy-timer@prod.timer` が 60 秒以内に行う。
7. **失敗したら戻す。** 手順書「戻し方」で直前の release を production に入れ直す。
   production を直接巻き戻さない。

## L2b で残る歯止め

権限を下げても次は残る。これらを外す場合は L2a 以下の別の決定が要る。

- **マージはオーナーのアカウントでしか行えない**(GitHub の権限。規律ではなく強制)
- `production` は protected branch とし、直接 push を禁じて PR 経由に限る
- 反映は release ブランチとして凍結される。何を出したかが後から特定でき、戻せる
- 反映は Discord に通知される(`infra/run/sync_from_origin.sh`)。オーナーが見ていない
  時間帯の反映も記録に残る
- staging に API token を置かない。侵害されても git 操作以上のことはできない

## L2b の経路(staging から)

`gh` も ssh も要らない。既存の `pr_develop_and_merge_to_monorepo.sh` /
`deploy_production_from_staging.sh` は冒頭の `command -v gh` で FAIL し、かつ本番へ
ssh する前提だが(staging から `supercom-web1` は名前解決できない)、本番には
`deploy-timer@prod.timer` が 60 秒ごとに `origin/production` を追う仕組みがあるため、
**origin/production さえ進めば ssh は不要**である。

```
1. commit(develop)
2. git push origin develop
3. release/<日付> を origin/develop の sha で切って push
4. オーナーへマージ URL を提示
   https://github.com/ThinkXInc/thinkx-system/compare/production...release/<日付>?expand=1
5. オーナーが GitHub でマージ(スマホ可) ← 承認
6. 本番の timer が 60 秒以内に反映
7. 実行者が本番 URL を curl で実測して報告
```

3〜4 はスクリプト1本に落とす(`docs/GUIDELINES.md`「コマンドの束はスクリプトに落とす」)。
実装は deploy key に write を付けた後に行う。付ける前は疎通確認ができず、
検証していないものを本番経路に置かないため。

## 承認削減の判定基準(オーナー裁定 2026-09-05)

Claude Code の承認プロンプト(`.claude/settings.json` の `ask`)を減らしたくなったら、
対象の操作を次の3分類に当てて処方を決める。毎回議論しない。

| 分類 | 例 | 処方 |
|---|---|---|
| **観測系**(高頻度・失敗しても状態を変えない) | staging への ssh 観測、curl での外形確認 | **固定リテラルのスクリプトに落とす → レビュー → Edit/Write deny で保護 → 承認対象から外れる。** リモートで走る文字列を引数で受けない(任意コマンド引数は作らない)。第1号: `infra/scripts/stg.py`(`infra/docs/STG_OBSERVE_PLAN.md`) |
| **文書系**(`docs/` `runbooks/` の Edit/Write) | findings の追記、runbook の更新 | ask の理由は危険だからでなく内容を見たいから。**承認のタイミングを保存時から commit 前の `git diff` に移す(allow に変える)か、現状維持を選ぶ。** スクリプト化はしない |
| **変更系**(不可逆・状態を変える) | terraform apply/destroy、git restore、本番反映、send-keys | **減らさない。** 頻度が低く、承認コストとして払うのが正しい |

- 昇格の入口は「同じ形の ssh/curl を **3回** 書いたら観測系スクリプトのサブコマンドにする」。1回きりの調査は素の ssh を書いて承認1回で済ませる。
- 承認削減のための一般フレームワークを先に作らない。事例(スクリプト)を1本ずつ足し、判断はこの表で再利用する。
- `ask` も `deny` も、素の `Bash` が allow である限り機械的な境界ではない(前置一致は先頭語しか見ず、subprocess から ssh を呼ぶ新規スクリプトは書けてしまう)。**機械的な境界が要る操作は ssh の forced command か GitHub 権限(L2b と同じ考え)で担保する。** settings の規則は減速帯として扱う。
