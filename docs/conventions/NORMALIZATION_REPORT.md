# コーディングガイド正規化レポート(D-19)

対象: `docs/conventions/` の原本2本
- `thinkx_coding_guide.md` — 「ThinkX でのコードの書き方」(音声書き起こし原本)
- `thinkx_coding_axioms.md` — 「Coding Guide」(2022, wiki。公理 Minimalism / Uniqueness / Speed)

生成物(すべて `docs/conventions/` 配下):
- `archive/thinkx_coding_guide.md` / `archive/thinkx_coding_axioms.md` — 非規範ヘッダ付き原本コピー
- `AXIOMS.md`(公理層)/ `SKILLS_INDEX.md`(手順層の見出し)/ 本レポート

原本は**一切編集していない**(archive のコピー冒頭にのみ非規範ヘッダを付与)。
コード・計画書・既存 CLAUDE.md も変更していない。

---

## 1. archive 配置

| 原本 | コピー先 | 付与した明記 |
|---|---|---|
| `thinkx_coding_guide.md` | `archive/thinkx_coding_guide.md` | 冒頭に「原本(非規範・D-19)。正規化版が規範の材料。」+ 参照先 |
| `thinkx_coding_axioms.md` | `archive/thinkx_coding_axioms.md` | 同上 |

---

## 2. 誤変換の除去

原本は既知の代表的誤変換(「鬼は」→これは / 「セレビィ」→Celery / 「ATM構造」→HTML構造 /
「壱発」→一発)が**既に修正済み**の状態で配置されていた(本フェーズで確認、`grep` で残存なしを検証)。
新たに検出した未修正の誤変換候補は下記2件。いずれも**手順層(SKILLS_INDEX 送り)の本文**にあり、
正規化本体(AXIOMS)には出現しないため、本レポートに記録し原本は保存する。

| 箇所 | 原文 | 判定 | 扱い |
|---|---|---|---|
| guide L167 | 「その View を処理している**改装**（=その View を初期化して配下として持っている親側）」 | 誤変換の可能性大。丸括弧の注記で意味(=親コンポーネント/上位ビュー)は確定できる | **[判読不能: 原文ママ]** で保存。単語のみ garble、注記が意味を保つため推測置換しない |
| guide L151 | 「**ホーム**等の重要な要素には ID をつける」 | 誤変換の可能性大。「フォーム」の脱字(フ欠落)と推定されるが確信なし | **[判読不能: 原文ママ]** で保存。§7 保留に記録 |

---

## 3. 層移動(公理 → 契約 → リポ固有 → 手順)

原本の各節を層へ振り分けた。移設の**実作業**(リポ CLAUDE.md への転記等)は各計画の管轄であり、
本作業では行き先の明示に止める。

| 原本の節 | 行き先の層 | 配置先 |
|---|---|---|
| 三公理(Minimalism/Uniqueness/Speed) | 公理 | `AXIOMS.md` |
| 記憶力より思考力に頼る | 公理 | `AXIOMS.md` |
| 命名(Naming basics / JS 変数名 1.5 語) | 公理 | `AXIOMS.md` |
| メソッドは小分けにする | 公理 | `AXIOMS.md` |
| 疎結合の維持 / View の最小権限 / コンポーネントの Locale | 公理 | `AXIOMS.md` |
| コメントの程度 / チャンク(空白行) | 公理 | `AXIOMS.md` |
| データ型の制約(pydantic/namedtuple) | 公理 | `AXIOMS.md` |
| 日時(datetime)は UTC | 公理 | `AXIOMS.md`(実装契約は L-5) |
| クラスの継承(→現代化) | 公理 | `AXIOMS.md`(§5-1) |
| エラー表示(→現代化) | 公理 | `AXIOMS.md`(§5-2) |
| 返却値のフォーマット / エラーハンドリング 3 パターン | **契約** | libcommon `CLAUDE.md`(L-7)/ PROTOCOL.md。**AXIOMS には重複記載しない** |
| セッション(Redis カスタムハンドラ・session ID 転送) | **契約**(実装 API)+ **リポ固有**(cookie 名等) | libcommon `CLAUDE.md`(L-7)+ 各リポ CLAUDE.md |
| アーキテクチャの前提(Nginx/uWSGI/submodule 配置) | リポ固有 | 各リポの `CLAUDE.md` |
| ログの色分け(赤/シアン/イエロー/マゼンタ) | リポ固有(実装は libcommon.color) | 各リポ CLAUDE.md / libcommon |
| スタイルシートの配置 | リポ固有 | 各リポの `CLAUDE.md` |
| 画面描画の全体フロー / View 三部構成 / PageView / TextField / 401・403 / HTML 注入 / SVG / エラーページ / 共通ライブラリ切り出し | 手順 | `SKILLS_INDEX.md`(見出しのみ) |
| デバッグ(細かくログ) | 手順(降格) | `SKILLS_INDEX.md` + §5-3 |
| トラブルシュート(gulp ビルド) | 手順(本文から除外) | `SKILLS_INDEX.md`(次期)+ §6 findings |

---

## 4. 契約層(L-7)との重複回避・差分

原本の「返却値のフォーマット」「エラーハンドリング 3 パターン」「セッション」は、libcommon 計画 L-7 の
`CLAUDE.md`(契約の機械可読化)が担う領域である。**AXIOMS.md では重複記述せず、行き先を指すに止めた。**

- L-7 は現時点で**未生成**(`libcommon/CLAUDE.md` 不在。L-7 は Phase 2 の項目)。計画テキスト
  (`libcommon/refactor_plan.md` §L-7)で内容が確定しているため、それを契約層の正典として参照した。
- 原本と L-7 の間に**矛盾は検出されなかった**。原本の 3 パターン(成功 / 単体エラー / 複数バリデーション)
  は L-7 のレスポンス正典(pydantic フォーマット族)・PROTOCOL.md §5 の外形と整合する。

---

## 5. 現代化(確定済み修正)

### 5-1. 継承 [現代化]

- 原本(guide L133-135): 「クラスの継承は基本的に行わない。」
- 正規化(AXIOMS §継承): 「アプリ層で深い継承をしない。フレームワーク基底の継承+1段の拡張
  (TextField 等)は可。」
- 根拠: simplicity の実態と整合。`grep` で確認した継承は framework 基底
  (`ViewComponentBase` / `Page` / `TextField`)起点で、多くが 1 段拡張。無条件の「継承しない」は
  実態と矛盾していた(`conventions/README.md` も原本の矛盾点として指摘済み)。

### 5-2. エラー表示 [現代化]

- 原本(guide L42-44): 「エラーの内容は、なるべく詳しく細かくユーザに表示しても、ほとんどの場合は
  構わない。」
- 正規化(AXIOMS §エラー表示): 「詳細はログへ。ユーザへはエラーコード+安全なメッセージ。詳細を
  返すのはバリデーションエラーのみ。」
- 根拠: 無条件の詳細表示は内部情報の漏えい経路。バリデーションエラーのみ、ユーザが直せるよう
  フィールド名・コード・メッセージを返す(契約の `errors` 配列型は不変)。

### 5-3. テスト規律 [追加](原本に無い新規規約)

- 追加(AXIOMS §テスト規律): 「機械オラクル(sha 台帳・ゴールデン・lint ベースライン)が全変更に
  先行する(D-4)。」
- 併せて、原本(guide L90-92)の「原因不明時は細かくログを出す」デバッグを**オラクル不在時の
  最終手段に降格**(SKILLS_INDEX で [降格] 明記)。
- 根拠: D-4。原本には無い規約のため**「追加」と明示**。

### 5-4. gulp ビルド記述 [本文から除外]

- 原本(guide L275-286)の gulp 前提のビルド/トラブルシュート記述は、現行(babel /
  less-watch-compiler / cpx 併存)と乖離しているため正規化本文から外し、SKILLS_INDEX に [次期] として
  見出しのみ残した。**ビルド方式の統一は次期論点**(§6 findings)。

### 5-5. その他の原文 [保存]

上記以外の原文の言い回し・決定は保存した。改善提案は §6 findings に分離し、本文は原文の意図を保つ。

---

## 6. Findings(編集せず報告のみ / 提案)

### 構造上の欠落(参照先が未存在)
- **F-1 `docs/AUTH_TRACK.md` が不在。** D-25 / D-26 と `auth/CLAUDE.md`(改訂版 §前倒し実装の条件)が
  「詳細は docs/AUTH_TRACK.md」と参照するが、ファイルが workspace・auth のいずれにも存在しない。
  D-19 の範囲外(作成は人間/別トラック)だが、参照整合性の穴として記録する。
- **F-2 `libcommon/CLAUDE.md`(L-7)が未生成。** 契約層の正典は現状「計画テキスト」にのみ存在する。
  Phase 2 で L-7 が生成されるまで、契約層参照は計画書 §L-7 を典拠とする。

### 文書の不整合(非規範・原本を編集しないため報告のみ)
- **F-3 `conventions/README.md` のファイル名が実体と不一致。** README は原本を
  `thinkx-coding-style.md` / `coding-guide-2022.md` と記すが、実体は `thinkx_coding_guide.md` /
  `thinkx_coding_axioms.md`。README の更新は人間判断(本作業では未編集)。

### 次期論点(提案)
- **F-4 ビルド方式の統一。** gulp(simplicity)/ babel・less-watch-compiler・cpx(併存)が混在。
  ビルド系の正本化・手順の skills 化は、ビルド方式統一後に行うのが安全。次期論点として記録。
- **F-5 手順の skills 化。** `SKILLS_INDEX.md` は見出しのみ。1手順=1 skill 化は次期。
- **F-6 ログ色分けの正典化。** 原本の色区分(赤/シアン/イエロー/マゼンタ)は実装
  (`libcommon.color` / `libcommon.logger`)と対応づけて各リポ CLAUDE.md へ移すのが望ましい。

### 改善提案(本文には反映せず、原文の意図を保存)
- **F-7 命名公理の機械検査。** auth は禁止命名(`sub`/`client_id`/`available_services` 等)を
  `tests/test_conventions.py` で静的検査している。命名公理(別名禁止)を全リポで機械ゲート化する
  提案(実装は各計画の管轄)。

---

## 7. 保留 [判読不能: 原文ママ]

推測で埋めず原文のまま残した箇所(§2 と同一。再掲)。

| 箇所 | 原文の語 | 推定(確信なし) |
|---|---|---|
| guide L167 | 「改装」 | 親コンポーネント/上位ビュー(丸括弧の注記が意味を確定させる) |
| guide L151 | 「ホーム」 | 「フォーム」の脱字か(未確定) |

---

## 8. 矛盾チェック(AXIOMS.md × 既存 CLAUDE.md 群)

編集は行わず、矛盾の有無のみ報告する。

### 8-1. AXIOMS × simplicity `CLAUDE.md`(R-11)
- **矛盾なし(解消済み)。** 原本の「継承しない」は simplicity の継承階層と矛盾していたが、現代化
  (§5-1)で「framework 基底+1段拡張は可」に精密化し整合。
- 観察: simplicity には共有抽象 `*Base`(例 `AlertMessageComponentBase extends ViewComponentBase`)を
  挟む 2〜3 段の連鎖が一部ある(`KeywordsField → TextField → …`)。いずれも framework 基底起点で
  「アプリ層の深い継承」ではないため規約の趣旨内。違反ではなく観察として記録。
- 命名・console 禁止(simplicity は `debuglog` 使用)・exact ピン等は AXIOMS と同方向で矛盾なし。

### 8-2. AXIOMS × libcommon 契約層(L-7 計画テキスト)
- **矛盾なし。** レスポンス外形・デコレータ積層・セッション API は契約層の管轄として AXIOMS から
  除外(重複なし)。エラー表示の**方針**(§5-2)は L-7 の**外形**(APIErrorFormat)と相補的で衝突しない。
  日時 UTC(AXIOMS)は L-5/D-17 の aware-UTC ドクトリンと同一。

### 8-3. AXIOMS × auth `CLAUDE.md`
- **矛盾なし。** 命名(「一つの事実に一つの名前・別名禁止」)は auth の命名規約と一致。エラー表示の
  方針は auth の「名前付きエラークラス+バリデーションはデコレータ」と整合。内部 `lang`/ワイヤ
  `locale` の使い分けは AXIOMS の「外部境界のみ相手の名前」と整合。テスト規律(D-4)は auth の
  静的ゲート(`tests/test_conventions.py`)と同方向。

**総合: 現代化後の AXIOMS.md と既存 CLAUDE.md 群(R-11 / L-7 計画 / auth)に規約矛盾は検出されなかった。**
未解消の構造的欠落は F-1(AUTH_TRACK 不在)・F-2(L-7 未生成)の2件で、いずれも D-19 の範囲外。

---

## 9. 完了条件の充足

- [x] archive 配置済み(非規範ヘッダ付き、原本は無編集)
- [x] `AXIOMS.md` 存在
- [x] `SKILLS_INDEX.md` 存在
- [x] `NORMALIZATION_REPORT.md` 存在
- [x] 全変更を本レポートに列挙(§2 誤変換 / §3 層移動 / §5 現代化 / §7 保留)
- [x] 原本に無い新規規約は「追加」と明示(§5-3 テスト規律のみ)
- [x] セキュリティ疑い(D-22): エラー表示の現代化は情報漏えい経路の**是正**であり、原本に秘密値・
      exploit は無い。新規のセキュリティ疑いは検出せず(即停止事由なし)。

ROADMAP のチェックボックス更新は人間が行う。
