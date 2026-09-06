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
- `ask` も `deny` も、素の `Bash` が allow である限り機械的な境界ではない(前置一致は先頭語しか見ず、subprocess から ssh を呼ぶ新規スクリプトは書けてしまう)。**機械的な境界が要る操作は ssh の forced command か GitHub 権限(L2b と同じ考え)で担保する。** settings の規則は、回避しうる目安であって機械的な保証ではないと扱う。

## オーナー指示(承認削減の設計方針・原文)

原文・解釈・文脈で残す(GUIDELINES と同じ形式)。表現はオーナーのものに忠実に。

- **原文**:「addとcommitくらいだったら勝手にやってほしい そこには破壊的なことは何もないからだし、戻せるからだ」
  - 解釈: 非破壊で元に戻せる操作(git add / commit)は無承認にする。
  - 文脈: 1 項目 1 コミットで毎回承認が出るのを冗長と感じた(2026-09-05)。

- **原文**:「記事の原稿の修正を依頼した時点で承認しているのにさらに承認プロセスがあるのは冗長だ」
  - 解釈: 依頼した編集は、その依頼が承認。編集ごとに別の承認を重ねない。残すのは公開の承認。
  - 文脈: 記事見出しの書き換えで、編集の承認と公開の承認を分ける議論。

- **原文**:「localhostをcurlするのは安全だろう」
  - 解釈: localhost への読み取り(GET)は安全で無承認の対象にしてよい。外部・本番の curl は承認を残す。
  - 文脈: ローカルの dev サーバーの表示確認。

- **原文**:「問題はEditツールでなくBashを使っていることと言えないか」
  - 解釈: 専用ツール(編集は Edit)があるのに Bash を使うのが、承認が出る原因であり変更が見えない原因。作業に合う道具を使う。
  - 文脈: build スクリプトを Python の heredoc で書き換えていた例。

- **原文**:「一度許可したサイトは、サイトと同じドメインのサイトは安全だから、それを記録しておけば、もう再び許可を求める必要がないだろう」
  - 解釈: WebFetch は一度許可したドメイン(と同一ドメイン)を記録し、以後聞かない。
  - 文脈: フェッチのたびにドメイン承認が出る件。

- **原文**:「小さくversion1を作ってみる それで私の承認が軽くなりかつ安全であることがわかったら増やしていく」
  - 解釈: 最小の v1 を作り、承認が軽くなること・安全なことを実地で確認してから対象を広げる。
  - 文脈: 承認削減の実装方針。

- **原文**:「(小さくと言っているのは)まだ実例集合は部分でしかなく、今から実装しようとするスクリプトもより細かな場合わけがさらに発生することが予想されるから」
  - 解釈:「小さく」の理由。実例もスクリプトの場合分けも未完なので、v1 は小さく始めて成長させる。対象を git だけに絞る意味ではなく、安全と確認できた集合を小さく出す。
  - 文脈: v1 の scope についての補足。

- **原文**:安全性の説明を「この製品の商品説明にも使用される」/「hooksの中身をなぜそうしてどうなるか説明せよ」
  - 解釈: 安全性の説明とフックの動作は、KOBITO サーバークラウドの製品説明の元にする。1 か所にまとめる。
  - 文脈: 下の「承認削減の安全モデル」節。

- **原文**:「簡潔かつ論理的で必要十分に独自の未定義用語を使わず書け」
  - 解釈: 設計文書は造語・比喩を使わず、簡潔・論理的・必要十分に書く。
  - 文脈: 安全モデル節の書き方への指摘。

- **原文**:「approval_casesはversion 1でかつアーカイブされる前提だ ... それでコマンドを作ってから運用はじめてversion 2をストックする」
  - 解釈: approval_cases はバージョン管理する。v1 は構築の材料で、作り終えたら archive。運用中の新規事例は v2 に貯める。
  - 文脈: `docs/approval_cases_v1.md` の位置づけ。

## 承認削減の安全モデル(設計・製品説明にも使う)

「承認を減らす」と「安全」を両立させる根拠。KOBITO サーバークラウドの安全性説明の元にする。
実装: `hooks/check_git_command.py`(v1)、材料: `docs/approval_cases_v1.md`。

### 前提: Claude Code の許可判定は 2 段階

1. PreToolUse フック(登録した外部コマンド)が走る。フックは `allow` / `deny` / `ask` を返せる。
2. settings のルールを deny → ask → allow の順に評価する。最初に当たったもので決まる。

フックの結果とルールの優先関係は決まっている:

- deny ルールに当たるコマンドは、フックが `allow` を返しても実行されない。
- ask ルールに当たるコマンド(`ssh` / `curl`)は、フックが `allow` を返しても承認プロンプトが出る。
- どのルールにも当たらないコマンドは、フックの `allow` で承認プロンプトなしに実行される。

### フックにできること・できないこと

- できない: deny のコマンドを実行させること。ask のコマンド(ssh / curl)を無承認にすること。
- できる: deny にも ask にも当たらないコマンド(git add / commit / push など)を無承認にすること。

curl / ssh の無承認化はフックでは行えない。localhost の読み取りなど安全な curl / ssh は、固定
スクリプト(`python3 infra/scripts/…`)にまとめる。可視のコマンドが `python3` になり ask に
当たらないため承認が出ない(例: `stg.py`)。

### 安全性は 2 つの独立した仕組みで保つ

1. settings の deny(force push・reset --hard・clean・rm -rf・sudo・鍵 / tfstate / tfvars / pem の
   読み書き等)は、フックの内容に関係なく常に実行を止める。
2. フック `check_git_command.py` は、その上で git add / commit / push(非 force)だけを無承認にする。
   フックが誤って広く許可しても、deny のコマンドは止まる。

### フック自身の判定も限定する

- `allow` を返すのは、コマンドが git add / commit / push(非 force)だけで構成されると確認できたときだけ。
- コマンド置換 `$(...)`・バッククォート・リダイレクト `>` `<` を含むものには `allow` を返さない。
- 解析できないもの・例外は `allow` を返さない。判定できないときは通常の許可フローに任せる
  (= 必要なら承認プロンプト)。フックは `deny` を返さない(止めるのは settings の deny の役割)。

### 無承認にする範囲

- 対象は、失敗しても元に戻せる操作に限る。観測(状態を変えない読み取り)と、依頼済みで可逆な編集。
- 変更系(本番反映・terraform apply/destroy・破壊操作)は無承認にしない。terraform を
  `-auto-approve` で実行して prod/staging 4 台を破壊再作成した事故(2026-08-06・事例 K)が、
  変更系を無承認にしてはいけない実例。

### 段階的に広げる

- 承認が出た実例を `docs/approval_cases_v{n}.md` に貯め、安全を確認してから対象を一段ずつ広げる。
- 実例集合はまだ部分的で、スクリプト化を進めるとさらに細かい場合分けが出る。だから v1 は小さく始める。

### settings への登録(hooks ブロック)

`.claude/settings.json` の `hooks` に登録する。中身と理由:

```json
"hooks": {
  "PreToolUse": [
    { "matcher": "Bash",
      "hooks": [ { "type": "command",
                   "command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/check_git_command.py\"" } ] }
  ],
  "PostToolUse": [
    { "matcher": "Edit|Write",
      "hooks": [ { "type": "command",
                   "command": "\"$CLAUDE_PROJECT_DIR/infra/scripts/cost-hook.sh\"" } ] }
  ]
}
```

- `hooks`: Claude Code がライフサイクルの各時点で走らせる script の登録表。
- `PreToolUse`: ツール実行の前(承認プロンプトの前)に走る。承認の有無を変えられる唯一の時点なので、自動承認はここに置く。`PostToolUse` は実行後なので承認には使えない。
- `matcher: "Bash"`: このフックを Bash ツール呼び出しのときだけ走らせる。git add / commit / push は Bash だから。Edit / Read などでは走らせない。
- `type: "command"` と `command`: 走らせるシェルコマンド。`$CLAUDE_PROJECT_DIR` は repo 直下(起動場所に依らず解決)。`python3` 起動なので実行権限(chmod)は不要。Claude Code はツール呼び出しの JSON をこの command の stdin に渡し、stdout を読む。
- `PostToolUse` の cost ブロックは別物: Edit / Write の後に `.tf` が変わったときだけ terraform コストを見積もる。時点(後)も目的(観測)も承認とは無関係。terraform 専用なので infra/ に置く。

### 実行時の流れ(1 コマンド)

1. エージェントが Bash コマンドを出す。
2. Claude Code が `check_git_command.py` にコマンドの JSON を渡す。
3. フックは、git add / commit / push(非 force)だけなら `allow` を返し、それ以外は何も返さない。
4. Claude Code が deny → ask → allow を評価する。deny と ask はフックの `allow` より優先。
5. deny に当たれば止まる。ask に当たれば承認プロンプト。フックが `allow` かつ deny / ask に
   当たらなければ無承認で実行。フックが何も返さなければ通常どおり判定する。
