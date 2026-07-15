# transformism vendoring カットオーバー計画書(S2 トラック) v1.1

対象: transformism のみ。正本はこの1箇所(transformism/refactor_plan.md)— 複製を他リポジトリに置かない。
雛形: thinkx/refactor_plan.md(S トラック。thinkx + kazukiotsukacom で完遂・実証済み)の同型縮小版。
ブランチ: `2026refactor`(統一ブランチ規約 D-14。S2-0 で master(85e59b7)から作成済み)。

v1.1 の変更点: F-S2-09 裁定(2026-07-14)を反映。S2-2 手順2 の COMMON_LOCALES_ROOT 付け替えは
**誤指示だった**(実体はデッドコード・libcommon が locale パスを自己解決・thinkx も未付け替えで稼働)。
「付け替え」→「不触の確認」に修正。作業内容への影響なし(実行者は裁定どおり no-op で処理済み)。
教訓: 下見(読み取り観察)の「要注意点」は、実依存の検証を経てから指示に昇格させること。

v1.0 の確定内容: 前提確認セッション(読み取り専用)の実測を反映。
焼き込み版 = **v2.1.0**(thinkx/kazukiotsukacom と同一スナップショット。tree_sha256: ab534a69…)。

## 目的

transformism を他の静的サイト群(thinkx / kazukiotsukacom)と同じ状態に揃える:
libcommon 依存を submodule から vendoring(リポジトリ内スナップショット)へ切り替え、
ルートゴールデン(機械オラクル)を新設し、monorepo 取り込みの前提を満たす。

**サイトのコード(Flask ルート・テンプレート・views)は無変更。** 変更は依存の配線と
テスト・規範文書の新設のみ。

## 前提(確認済み・2026-07 前提確認セッションの実測)

- Phase 2 完了の実物証拠あり(libcommon v2 系タグ + bake.sh、thinkx/kazukiotsukacom の
  vendoring + VERSION + ゴールデン、全て確認済み)
- transformism の現状:
  - libcommon は **submodule のまま**(`web-server/libcommon`、ピン先 c318f32 = v2.0.0 の祖先の旧版)
  - 作業ツリーは**未 populate**(submodule update 未実行。旧版の実体化は S2 では不要 — 直接 v2.1.0 を焼く)
  - libcommon への import は **config.py / flask_helper.py / mails/send_mail.py / main.py**
    (Python 4 ファイル・19 import 行。使用モジュール: logger / color / language / locale /
    validator / mail / web.validation_errors / web.http_errors / web.http_successes)
  - main.py:37 `COMMON_LOCALES_ROOT` は**デッドコード**(定義のみ・参照ゼロ。F-S2-09 裁定により不触。
    是正は thinkx 側の同一行と併せて Phase 3 型仕分けへ)
  - `www/playbooks` submodule が別に存在(**本計画では不触**)
- settings.json のスコープが transformism への書き込みを許可している(S-0a 同型・人間作業)
- 本計画は infra/ 構築(I-STEP1)と対象が重ならないため並行実行可

## 禁止事項

- transformism のサイトコード(Flask ルート・テンプレート・views・静的ファイル)の変更。
  例外は libcommon の import 文の配線書き換えのみ(実測では同一パス焼き込みのため
  no-op だった — F-S2-08。「念のため」の書き換えは禁止)
- vendoring された libcommon スナップショットの編集(修正は libcommon 原本 → 再 bake)
- ゴールデン生成後、スモークが落ちた際にゴールデンを黙って再生成して通すこと。
  不一致は findings.md に記録して停止し、人間の判断を仰ぐ
- `www/playbooks` submodule への変更・実体化
- 旧 submodule(c318f32)の populate(`git submodule update --init` を実行しない — 不要かつ混入リスク)
- 他リポジトリ(thinkx / kazukiotsukacom / libcommon / simplicity 等)への変更
- 本計画書・ROADMAP・DECISIONS・settings の書き換え

## 手順

### S2-0: ブランチ作成と消費実態の最終確認 [完了]

- [x] master(HEAD 85e59b7)から `2026refactor` ブランチを作成・checkout
- [x] import 一覧を行番号付きで確定(Python 4 ファイル・19 行。「5」は .gitmodules の数え誤差 — F-S2-02)
- [x] 使用モジュール 9 種が v2.1.0 スナップショットに全存在・locales/ 同梱を確認(F-S2-04)
- [x] パス直参照は main.py:37 のみと確認(F-S2-05)→ 後の調査でデッドコードと判明(F-S2-09)
- [x] 実行時依存経路: send_mail.py の SES 初期化は TEST_SEND=False でゲート済・import 安全(F-S2-06)

### S2-1: vendoring bake(v2.1.0) [完了]

- [x] bake.sh を v2.1.0 で実行、transformism/web-server/libcommon/ へ焼き込み(exit 0)
- [x] VERSION = v2.1.0、tree_sha256 = ab534a69…95b04 で thinkx vendored と完全一致(diff -r で byte 一致)
- [x] locales/ 実体同梱を確認(api_response / errors / validation_errors .json)

### S2-2: 配線切り替え [完了]

- [x] import 文: thinkx vendored との byte 一致照合により **no-op 確定**、書き換えなし(F-S2-08)
- [x] COMMON_LOCALES_ROOT(main.py:37): **不触**(F-S2-09 裁定。デッドコード・libcommon の
      locale.py:49 が __file__ 相対で自己解決・thinkx も未付け替えで稼働実績)
- [x] `.gitmodules` から web-server/libcommon 節を削除、gitlink(160000)除去、
      vendored 38 ファイルを通常 blob 化(www/playbooks は残置)(F-S2-10)
- [x] ENV=develop・cwd=web-server で 9 モジュール全て vendored から解決、
      COMMON_LOCALES_FILE_PATHS が vendored locales に解決・実在を確認(F-S2-11)
- [x] カットオーバー 1 コミット(50d6ca0)+ push 完了

### S2-3: ルートゴールデンの新設

- [ ] thinkx と同型で `web-server/tests/golden/` を新設し、全 GET ルートの
      (rule, status) 一覧を生成する(ハーネス前提 3 点: cwd=web-server /
      名前空間パッケージの解決先判定 / ENV 注入 conftest — thinkx 同型で実装)
- [ ] 生成されたゴールデンを人間がレビューできる形で全件報告(件数と一覧。
      多言語ルートの件数を明示)

### S2-4: スモーク実行

- [ ] ローカル起動した transformism に対し、ゴールデン全ルートを curl 照合して green を確認
- [ ] 多言語ルート(locale 依存ページ)が代表言語で正しく描画されることを数点、応答内容で確認
- [ ] メール送信経路(SES)は実送信せず import/初期化の成立のみ確認し、
      実送信の検証はステージング(I-STEP2 以降)へ送ることを findings に明記

### S2-5: 規範文書の新設

- [ ] `transformism/CLAUDE.md` を thinkx / kazukiotsukacom と同じ層構造で新設
      (vendoring 済みスナップショット編集禁止・ゴールデンの位置と再生成手順・
      ビルド/起動コマンド・playbooks submodule の存在と扱い)

### S2-6: 完了処理

- [ ] findings.md の全項目を整理(修正はしない — Phase 3 型の仕分けは人間が後日判断)
- [ ] `2026refactor` へ push、成否を報告冒頭に明記
- [ ] 完了報告: 変更ファイル一覧・ゴールデン件数・スモーク結果・残課題

## 完了判定

S2-4 のスモーク green + S2-5 の CLAUDE.md 新設 + push 完了。
ROADMAP のチェック更新(S2 行の追加)と I-STEP2 注記(transformism 人間判断)の削除は人間が行う。

## この計画の後工程(参考・本計画の範囲外)

monorepo 取り込み(M トラック: docs/MONOREPO_PLAN.md。ファイルコピー方式)→
staging EC2 で全サイト run → 全ゴールデン green → master マージ = EC2 カットオーバー。
以後のサイト編集はセッションブランチ → staging 反映 → 確認 → PR → rebase マージ → prod pull → restart。
