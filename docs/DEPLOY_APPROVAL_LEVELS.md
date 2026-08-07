# 本番反映の承認レベル(DEPLOY_APPROVAL_LEVELS)

本番へ出す操作を「誰が引き金を引けるか」で段階化した定義。正本はこの1箇所。
デプロイ手順そのものは `infra/docs/デプロイ手順書.md`、経路の索引は `CLAUDE.md`
「デプロイ経路のルーティング」にある。ここが決めるのは**引き金の権限だけ**である。

現在のレベル: **L2**(オーナー裁定 2026-08-07)。

## なぜレベルにするか

2026-08-07 まで本番へ出せるのはオーナー機だけだった(L3)。理由は
`docs/SITE_EDIT_WORKFLOW.md` の「本番反映は GitHub マージ権限(人間のアカウント)が
必須のため、URL 共有相手は本番に触れない(構造的ゲート)」である。
一方でオーナー機が常時ネットに繋がっている保証はなく、スマホから承認できないと
反映が止まる。**固定の強度ではなく、状況に応じて上下させる**ためにレベル化する。

## レベル

| Lv | 名前 | 本番へ出せる主体 | 承認の形式 |
|---|---|---|---|
| L3 | 隔離 | オーナー機のみ | オーナーが自ら `deploy_production_from_staging.sh` を叩く |
| **L2** | **セッション承認** | **staging の Claude Code セッション** | **そのセッション内でのオーナーの明示承認。承認の無い実行は禁止** |
| L1 | 自動(検証付き) | 検証が green なら主体を問わず自動 | 事前承認(このレベルを選んだこと自体が承認) |
| L0 | 直結 | 誰でも即時 | なし |

L1 / L0 は**現時点で採用しない**。定義だけ置く。将来 L1 へ下げる場合は、受け入れ
sweep が全 green のときだけ merge する条件を先に実装してからにする(条件なしの
自動反映は L0 であり、L1 を名乗ってはいけない)。

## レベルを決めるスイッチは1つだけ

**staging(`web1-stg`)の GitHub deploy key に write 権があるかどうか。** ここだけで
L3 と L2 が切り替わる。スクリプトも設定ファイルも変えない。

| | deploy key | 結果 |
|---|---|---|
| L3 | read-only | `git push origin develop` が拒否され、staging からは何も出せない |
| L2 | write | staging から develop を push でき、以降の経路が開く |

**上げ方(L2 → L3)**: GitHub の当該 deploy key の write を外す。それだけで staging は
即座に本番へ触れなくなる。スクリプトを消す必要も、この文書を書き換える必要もない
(「現在のレベル」行だけ直す)。staging のセッション URL を非開発者に渡す期間は
L3 に戻すこと。

**下げ方(L3 → L2)**: 同じ設定で write を付ける。

## L2 の運用規律(実行者=Claude Code が守る)

1. **承認なしに本番へ出さない。** オーナーが「本番反映」と明示した場合にのみ実行する。
   過去の承認は次回に持ち越さない(1 反映 = 1 承認)。
2. **承認を求める時は、出す内容を丸ごと見せる。** 対象 sha、`origin/production..origin/develop`
   のコミット一覧、再起動されるサービス名。丸めない・省略しない。
3. **実行前に宣言する。** 宣言と実行を同一メッセージで行わない
   (`docs/GUIDELINES.md`「状態を変える操作は実行前に宣言する」)。
4. **staging で目視できる状態にしてから承認を求める。** 確認 URL
   (`https://staging.thinkxinc.com/...`)を必ず添える。見ていないものを承認させない。
5. **反映後は本番 URL に対して実測し、結果を報告する。** 「出しました」で終えない。
6. **失敗したら戻す。** 手順書「戻し方」で直前の release を production に入れ直す。
   production を直接巻き戻さない。

## L2 で残る歯止め

権限を下げても次は残る。これらを外す場合は L1 以下の別の決定が要る。

- `production` は protected branch とし、直接 push を禁じて PR 経由に限る
  (誤操作で履歴が飛ぶのを防ぐ。承認の強度とは別の話)
- 反映は release ブランチとして凍結される(`deploy_production_from_staging.sh` の設計)。
  何を出したかが後から特定でき、戻せる
- 反映は Discord に通知される(`infra/run/sync_from_origin.sh`)。オーナーが見ていない
  時間帯の反映も記録に残る
- staging の write 権は **develop への push に限る**。`production` へ直接 push させない

## 未実装(L2 を実際に使うために要るもの)

2026-08-07 時点で staging には次が無い。deploy key に write を付けただけでは動かない。

1. `gh` が未導入。既存の `pr_develop_and_merge_to_monorepo.sh` /
   `deploy_production_from_staging.sh` は冒頭の `command -v gh` で FAIL する
2. 上記2本は本番へ ssh する前提だが、staging から `supercom-web1` は名前解決できない。
   ただし本番には `deploy-timer@prod.timer` が 60 秒ごとに `origin/production` を追う
   仕組みがあるため、**origin/production を進めれば ssh は不要**

したがって staging 用の経路は「push → GitHub API で develop→production を merge →
timer が 60 秒以内に反映 → 本番 URL を実測」となる。`curl` は staging にあるので
`gh` の導入は必須ではない。実装は deploy key に write を付けた後に行う
(付ける前は疎通確認ができず、検証していないものを本番経路に置かないため)。
