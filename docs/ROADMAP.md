# ThinkX システム統合ロードマップ

目的: citywalk / ilrsa / quantz として別々に構築してきたサービスを、共通アカウント(apps/auth)・
共通UI(simplicity)・共通契約層(libcommon)の上に統合する。規模が大きくなっても
AI 駆動開発で詰まらないこと(独立した軽量モジュール+機械オラクル)を最優先とする。

## フェーズと現在地

- [x] **Phase 0: ワークスペース構築**(bootstrap.sh 実行、計画書の各リポジトリへの配置、
      ブランチ refactor/2026 作成)
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
      vendoring(編集禁止)。コーディングガイドの正規化(D-19)はこのトラックの前提作業)
- [x] **Phase 4b: auth 追随**(前提: Phase 2 完了。bake.sh v2.0.0 で焼き直し、
      L-1 の注入 API へ配線替え、auth テスト一式 green。Q-4 と同型の機械的追随。
      本番投入は原則この完了後 — AUTH_TRACK.md 未決事項参照)
- [ ] **Phase 5: 各サイトの auth 統合**(quantz-web から。simplicity 計画 §1.7 の接点
      A-1〜A-3 のレビューを含む)

Phase 1・Phase 2・Phase 4a は対象リポジトリが重ならないため**並列実行可**(別セッション・別端末)。
Phase 2 完了後は Phase 2.5 と Phase 4b も相互に並列実行可(いずれも前提は Phase 2 完了のみ)。
直列で進める場合の推奨順は 1 → 2(どちらが先でも依存はない)。Phase 4b のみ Phase 2 完了が前提。

## セッション運用

- 1セッション = 1計画書(ルート CLAUDE.md の規律)。
- フェーズ間の移行(計画完了の判定、次フェーズの開始)は人間が承認する。
  完了の定義は各計画書の最終項目(R-12 / 全ゲート green)。
- 完了したらこのファイルのチェックボックスを人間が更新する(実行者は書き換え不可)。

## インフラトラック(I。Phase 系と独立・並行可)

- [ ] **I-STEP1: 最小インフラのリハーサル**(staging の VPC/EC2×2(LB+web)を terraform で
      作成→経路確認→destroy。規範: infra/CLAUDE.md + infra/docs/step1-rehearsal.md。
      前提なし・いつでも開始可。全 apply/destroy 承認制)
- [ ] **I-STEP2: 既存 web システムの載せ替え**(setup/*.sh を ssh で流す。
      前提: Phase 3 完了(v2.1.0 の全系再 bake)+ 2026refactor→master マージの人間判断。
      受け入れ試験: 各サイトのルートゴールデンを curl 照合(機械化済み)+
      quantz を載せる場合は Q-2 スイート。)
- インフラの検証はここだけ実インフラが要る(D-16: Ubuntu/AWS 必須は STEP2 から)

## monorepo 化の引き金(先回りしない。PROTOCOL.md §7 と同じ流儀)

現構成は polyrepo + vendoring(独立凍結・変更の完全可視を優先した決定)。
次のいずれかが**実測で**成立した時点で monorepo 移行計画に着手する:
- (a) libcommon の変更と全サイト追随を1コミットで原子的に行いたい場面が高頻度になった
- (b) vendoring の焼き直し運用コストが実測で支配的になった
- (c) 横断 CI を一本化する必要が生じた
移行自体は「フォルダ集約 + import 路書き換え + 全ゲート green」であり、
全リポジトリに機械オラクルが張られた後なら小さな計画書1本で済む。

## 参照

- 認証契約: auth リポジトリの PROTOCOL.md(v1・確定版)が正本
- コーディング規約: 各リポジトリの CLAUDE.md(層状配置。組織原則 → 契約 → リポジトリ固有)
- インフラ: infra リポジトリ(Terraform + runbooks)。AWS 移行 STEP2 の受け入れ試験は
  quantz-web の Q-2 スモークスイートが兼ねる