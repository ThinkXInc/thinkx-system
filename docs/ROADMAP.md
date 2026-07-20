<!-- 配置: thinkx-system/monorepo/docs/ROADMAP.md -->

# ThinkX システム統合ロードマップ

目的: citywalk / ilrsa / quantz として別々に構築してきたサービスを、共通アカウント(apps/auth)・
共通UI(simplicity)・共通契約層(libcommon)の上に統合する。規模が大きくなっても
AI 駆動開発で詰まらないこと(独立した軽量モジュール+機械オラクル)を最優先とする。

## フェーズと現在地

- [x] **Phase 0: ワークスペース構築**(bootstrap.sh 実行、計画書の各リポジトリへの配置、
      ブランチ 2026refactor 作成)
- [x] **Phase 1: simplicity 計画の完遂(版数は計画書ヘッダが正)**(対象: simplicity のみ)
- [x] **Phase 2: libcommon 計画の完遂(版数は計画書ヘッダが正)**(対象: libcommon + quantz-web。
      L-8 で v2.0.0 タグ + bake.sh、Q-6 で quantz-web の vendoring カットオーバー)
- [x] **Phase 2.5: 静的サイト群の vendoring カットオーバー**(規範: thinkx/refactor_plan.md
      = S トラック計画。対象: thinkx + kazukiotsukacom。サイトコードは無変更 —
      submodule→vendoring の配線切り替え+スモークオラクル+各サイト CLAUDE.md 新設のみ。
      前提: Phase 2 完了(v2.0.0 + bake.sh)+ settings.json のスコープ切り替え(計画 S-0a)。
      **Phase 4b と並行実行可**(対象リポジトリの重なりゼロ・前提は同一)。
      本番デプロイは計画外・人間がスケジュール)
- [x] **Phase 2.5-S2: transformism vendoring カットオーバー**(規範: transformism/refactor_plan.md v1.1。2026-07 完遂: v2.1.0 焼き込み・ルートゴールデン新設・CLAUDE.md 新設。静的サイト群 3 サイト全て vendoring 済み)
- [x] **Phase 3: バグ修正計画の実行**(規範: libcommon/bugfix_plan.md v1.0・起草済み。入力: 両計画で蓄積された findings.md 全項目。
      前提: Phase 1・2 完了 = 全リポジトリに検証の床がある状態。
      起草時の規則: 各項目を「修正する / 仕様として凍結する / 次期送り」に仕分けし、
      修正する項目は**修正パッチ+挙動変化を意図として固定する新ゴールデン+テスト**の
      3点セット・1項目=1コミットで定義する。既知の対象: simplicity F-1〜F-12、
      libcommon/quantz F-2〜F-11 のうち計画内未修正分、および実行中の新発見。
      仕分け時の優先度注記(1): Validator 群(postal_code_format の case 欠落=郵便番号検証が全入力で無効、
      notCorresponding の存在しないメソッド呼び出し、_validateMaxLength の null ガード欠落 —
      Phase 1 の T-06 特性テストが発見)は「入力検証の静かな無効化」クラスであり最優先。
      仕分け時の優先度注記(2): simplicity F-5(リスナー/タイマー解放不均衡)は可用性・二重送信・
      予期しない再実行に直結するため優先度高。特に async task・フォーム submit・再接続の周辺)
- [x] **Phase 4a: auth ベース実装(前倒し並行トラック・D-25)**(PROTOCOL.md v1 に従い、
      thinkx-system/auth で Phase 1・2 と並行開発する。必須4条件と GPT 実装の層別統合の
      扱いは docs/AUTH_TRACK.md が規範。libcommon は pre-v2.0.0 スナップショットを
      vendoring(編集禁止)。コーディングガイドの正規化(D-19)はこのトラックの前提作業。
      **【2026-07 訂正】ここで「完成」としたのは旧 PROTOCOL v1 に基づく起動可能な scaffold で
      あり、production 品質の auth ではない。確定仕様(auth-spec / D-38〜D-46)による本実装は
      下記 Phase 4d で行う。**)
- [x] **Phase 4b: auth 追随**(前提: Phase 2 完了。bake.sh v2.0.0 で焼き直し、
      L-1 の注入 API へ配線替え、auth テスト一式 green。Q-4 と同型の機械的追随。
      **【2026-07 訂正】この追随は旧 scaffold と libcommon の整合のためのもの。Phase 4d で
      Session 拡張版(L 計画)へ再追随する。**)
- [ ] **Phase 4c: citywalk 再構築**(規範: monorepo/citywalk/refactor_plan.md v3.0。
      トラック規約: monorepo/docs/CITYWALK_TRACK.md。対象: citywalk(旧 citywalkservers)のみ。
      内容: 二等級制([UI不変=知覚面]/[再構築])の rebuild — monorepo 取り込み(M 同型)・
      simplicity 化・libcommon.web 形式化・auth 単一アカウント化(ビジネスアカウント廃止 D-48)・
      PNG→SVG・構成の既存サービス同型化。vendoring は B案(D-35)。
      citywalk は未稼働のため破壊的改善が安く、auth 統合の先行事例を兼ねる(Phase 5 に先行)。
      **citywalk は auth の client(RP)実装を作る。auth 側の正本は Phase 4d の auth-spec に従う。**
      前提裁定: 計画 §7(旧 public リポ対応・データ移行 ほか)。§7-4 裁定前に C-3 着手禁止。
      本番デプロイ・データ移行の実行は計画外・人間/I トラックがスケジュール)
- [ ] **Phase 4d: auth production 実装(auth-spec 準拠)**(規範: **monorepo/auth/docs/auth-spec/**。
      Phase 4a/4b の旧 PROTOCOL v1 scaffold を、確定仕様(DECISIONS D-38〜D-46)の production 品質
      OIDC auth へ再実装する。OpenID Connect Core の Authorization Code Flow + PKCE(S256)、
      ID Token(RS256)、JWKS、OpenID Provider metadata、authorization code の検証後削除、
      auth_generation による失効、browser_context_id、logout 3種を含む。
      1セッション1計画の規律により4計画に分割し順に完遂する:
        L: libcommon Session 拡張(id / browser_context_id / clear_current / revoke_all /
           start(..., browser_context_id))。canonical libcommon の再 bake hash 照合が前提。
        A: auth server 本体(OIDC authorize/token/userinfo/jwks/metadata、
           signup/verification/password reset、失効/logout、データモデル、seed)。
        C: reference client(auth/reference-client/。旧 quantz-web は不触。E2E 疎通の受け皿・
           将来のサービス実装リファレンス。ClientTransactionStore / AuthClient /
           IDTokenVerifier / ServicePrincipal)。
        I: staging/production infra(staging 集約1台、production は定義のみで apply しない)。
      完了条件は auth-spec 05(2層テスト[論理層 + HTTP クライアント E2E] + negative test 一覧 +
      JWKS/metadata 公開 + 鍵ローテーションの staging 検証)。OIDF conformance suite 通過は
      初版に含めず、外部 RP 開放段階の完了条件とする。
      実 quantz 統合は C の green 後の後続(Phase 5)へ分ける。
      前提: 制御文書更新(DECISIONS D-38〜D-48・auth/CLAUDE.md・test_conventions.py・本 ROADMAP)完了。)
- [ ] **Phase 5: 残る各サイトの auth 統合**(quantz-web から。simplicity 計画 §1.7 の接点
      A-1〜A-3 のレビューを含む。citywalk は Phase 4c で統合済みのため対象外 —
      citywalk の C-5 契約テストが auth client 設計の実地検証を先行して担う。
      auth 側の正本は Phase 4d の auth-spec。)

Phase 4c は対象サブディレクトリが他フェーズと重ならないため、他の稼働トラック(I / E)と
**並行実行可**(別セッション)。libcommon v2.1.0 完成済みのため Phase 2 完了待ちの追随項目は持たない。
Phase 4d は L 計画で libcommon Session を拡張するため、Phase 4c(citywalk の client 実装)とは
libcommon の版で依存する。C 計画(reference client)の完了が Phase 4c/Phase 5 の client 実装の
参照となる。

## セッション運用

- 1セッション = 1計画書(ルート CLAUDE.md の規律)。
- フェーズ間の移行(計画完了の判定、次フェーズの開始)は人間が承認する。
  完了の定義は各計画書の最終項目(R-12 / 全ゲート green)。
- 完了したらこのファイルのチェックボックスを人間が更新する(実行者は書き換え不可)。

## インフラトラック(I。Phase 系と独立・並行可)

- [x] **I-STEP1: 最小インフラのリハーサル**(staging の VPC/EC2 を terraform で構築・経路確認。
      2026-07: destroy せず実運用 staging へ昇格 — 全サイト(transformism 含む)の
      staging 稼働・目視確認済み。アクセス制限(Basic 認証/noindex)適用済み)
- [x] **I-STEP2: 本番カットオーバー**(前提: M トラック完了 + staging で monorepo 稼働・
      全ゴールデン green。内容: production EC2 を terraform で新設 → setup/*.sh →
      monorepo clone → run → 受け入れ試験(全サイトのルートゴールデン curl 照合)→ DNS 切替。
      指針: prod 新設そのものが「monorepo 前提でゼロから立てる」再現性の実地検証。
      ドキュメント・スクリプトの抜けはここで全部露出する — 露出は失敗ではなく本 STEP の成果。
      切替後: 旧リポジトリ凍結(M 計画 M-7)。DNS 切替時、移行対象外サブドメイン
      (store.transformism.art 等)のレコード温存を確認)
- [x] **I-STEP2b: 露出した抜けの修正**(prod 構築中に露出した抜けは、その場しのぎの
      手作業で埋めて先に進まず、monorepo の infra/(setup・runbooks・terraform)に
      反映してから次の手順へ進む。手作業で通した箇所は I-STEP3 の staging 再構築で
      必ず再発する — 修正の完了指標は「同じ手順をもう一度流せば素通りすること」)
- [x] **I-STEP3: staging の monorepo 前提再構築**(前提: カットオーバー完了。
      指針: それまで既存 staging は不触 — prod 構築で詰まったときの「正解の参照」
      として維持する。カットオーバー後に既存 staging を destroy し、prod と同一の
      手順で再作成。staging / prod が同一手順書の産物になった時点で旧世界の手作業の
      痕跡が消える。完了後 E トラック(docs/SITE_EDIT_WORKFLOW.md)発効)

> **auth の infra(Phase 4d の I 計画)** は上記 I トラックとは別に、auth-spec 03/05 に従い
> staging 集約1台 + production 定義のみ(apply しない)で用意する。本番の署名鍵・client_secret・
> ユーザーデータを staging と共有しない(DECISIONS D-44)。

## monorepo 化(M トラック。裁定済み — 2026-07)

引き金の(a)(b)(c)実測待ちは撤回し、**EC2 カットオーバーと monorepo 化を一点に束ねる**と裁定した。
旧リポジトリ群はカットオーバー後に凍結アーカイブ化(履歴は運ばない・調査は旧リポジトリで行う)。

- [x] **M: monorepo 取り込み**(規範: docs/MONOREPO_PLAN.md v1.1。方式: ファイルコピー・
      1リポジトリ=1コミット・ARCHIVE.md に出所記録。取り込み元: 全リポジトリ一律
      2026refactor HEAD。対象外: quantz-web(後続・新システム設計時に判断)、
      libcommon / simplicity(D-35: canonical 独立 git として存続)。
      前提: S2 完了(済)+ staging 全サイト確認(済)。完了判定: 全ゴールデン sweep green + push)
- [ ] **E: サイト編集ワークフロー**(規範: docs/SITE_EDIT_WORKFLOW.md。発効はカットオーバー後。
      Remote Control 常駐 + セッションブランチ → staging 確認 → PR → rebase マージ →
      prod 反映。マージは人間のみ = 本番反映の承認ゲート)

## 参照

- **認証契約: monorepo/auth/docs/auth-spec/ が正本**(ソースコードと契約テストを含む。
  DECISIONS D-38/D-39)。旧 auth/PROTOCOL.md v1 は参照プランに格下げ済み。
- コーディング規約: 各リポジトリの CLAUDE.md(層状配置。組織原則 → 契約 → リポジトリ固有)
- インフラ: infra リポジトリ(Terraform + runbooks)。AWS 移行 STEP2 の受け入れ試験は
  quantz-web の Q-2 スモークスイートが兼ねる
- monorepo 取り込み: docs/MONOREPO_PLAN.md(M トラック正本)
- 共通ライブラリ運用: docs/COMMON_LIB_POLICY.md(B案・D-35)
- サイト編集ワークフロー: docs/SITE_EDIT_WORKFLOW.md(E トラック正本・カットオーバー後発効)
- citywalk 再構築: monorepo/citywalk/refactor_plan.md(Phase 4c 正本)/ docs/CITYWALK_TRACK.md