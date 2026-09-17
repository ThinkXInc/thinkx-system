# thinkx-system/infra/docs/discussion/discussion-2026-09-17-plan-summary-wording.md

2026-09-17 plan-summary の図・月額概算から supercom 移行関連を削除し見出しを改名(生ログ)

引用(太字)がオーナーの発言で、原文のまま。続く地の文が Claude の応答(実際に返した内容。
冗長な部分のみ圧縮)。時系列。成果物は `infra/runbooks/diagram.md`(plan-summary が表示する図の原本)、
`infra/scripts/cost-estimate.sh`、`infra/scripts/README.md`。コミットは monorepo ブランチ
b400be5 → 280dae0 → e415ab0。同セッションの 09-11 分(イベントページ)は
`thinkx/docs/discussion/discussion-2026-09-11-event-page.md`。

---

## 1. 実機リストと Cisco の注記を消す

> **infra plansummary から以下のsupercom移行関連は消して**
>
> **────────────────────────────────────────────────────────────────────────────────**
> **  実機リスト**
> **────────────────────────────────────────────────────────────────────────────────**
> **   - supercom3a  (実機)**
> **   - 4124GS-TNR**
> **   - EPYC 7313 ×2 / 512GB**
> **   - PM9A3 1.92TB NVMe**
>
> **   \*売却予定**
> **   supercom3b   4124GS-TNR**
> **   RTX5000 Ada / 15TB×2=30TB**
> **   supercom3c   SYS-220GP-TNR**
>
> ** ════════════════════════════════════════════════════════════════════════════════**
> ** (Cisco C1111-8P も役割終了)      │   月額 (1USD≒162円 / オンデマンド)**
> **════════════════════════════════════════════════════════════════════════════════**

出どころは `infra/runbooks/diagram.md`(plan-summary.sh はこの図を env 置換して表示)。実機リストの節と
Cisco 注記を削除し、月額の見出し(═══ / 月額 (1USD≒162円 / オンデマンド) / ═══)だけ残した。
`infra/scripts/README.md` の説明からも「実機リスト」の語を落とした。staging で plan-summary を流して、
ストレージの節の直後が月額になることを確認。コミット b400be5。
残したもの: ストレージ節の「コールドデータ(売却SSD分 約37TB)…」の 1 行と `infra/docs/architecture.md` の
supercom3a / Cisco の表(指示の範囲外)。

## 2. 見出し 5 か所の改名

> ** AWS 移行構成図 -> AWS構成図**
> **ドメイン → バックエンド 振り分け表 (LB nginx) -> ドメインごとのアドレス**
> **ストレージ所在まとめ -> ストレージ容量と中身**
> ** ThinkX インフラ月額概算 -> インフラ月額概算**
> **内訳は稼働率 60% 基準(compute のみ稼働率に比例。EBS/EIP/Route53 は固定) -> 稼働率60%(EC2のみ稼働率に比例。EBS/EIP/Route53は固定)**

前 3 つは diagram.md、後 2 つは cost-estimate.sh の echo。図の 1 行目は「AWS 移行構成図」の語だけ変え、
「supercom ─」と括弧内は据え置き。60 は変数 STD_UTIL から出る。plan-summary の実出力で 5 か所を確認。コミット 280dae0。

> **EC2のみ稼働率に比例 -> computeのみ稼働率に比例**

「稼働率60%(computeのみ稼働率に比例。EBS/EIP/Route53は固定)」。コミット e415ab0。

## 3. セッション終了

> **このセッションは閉じる 記録して claude generalに下着**

`CLAUDE_GENERAL.md`「記録・議事録」節に従い、議事録(本ファイルと thinkx 側)・findings・GUIDELINES を記録。
DECISIONS は新規決定なし。
