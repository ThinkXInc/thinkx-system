# transformism findings（S2 トラック）

記録規約: 気づき・不整合・判断待ちをその場で記録する。修正は行わない（Phase 3 型の仕分けは人間が後日）。
Security exception は即停止。パスは明示。

---

## S2-0: ブランチ作成と消費実態の最終確認（2026-07-14）

### F-S2-01 [解決済 2026-07-14] 計画ファイル名と settings/計画本文の参照名が不一致
- 検出時: 実ファイルが `transformism_refactor_plan.md` で、計画本文 §3 と settings.json deny が
  指す `transformism/refactor_plan.md` と別名。settings の書込保護が実ファイルに効いていなかった。
- 解決: 人間が実ファイルを `transformism/refactor_plan.md` にリネーム（裁定 (a)）。
  これにより settings.json `deny: Write(transformism/refactor_plan.md)` が実ファイルに一致し、
  **計画の書込保護が有効化**。計画本文 §3 の自己参照名とも整合。以後この正名で参照する。

### F-S2-02 [解決済] import 件数「5」対「4」の不一致
- 前提確認セッションの `git grep -Il libcommon | wc -l` が 5 を返したのは `.gitmodules` を
  数えたため。**libcommon を import する Python は 4 ファイル**（下記）。件数=名前で一致。

### F-S2-03 [観察] libcommon 消費実態（import 全 19 行・4 ファイル）
```
web-server/config.py:17   from libcommon.logger import Logger
web-server/config.py:20   from libcommon.color import *
web-server/flask_helper.py:4   from libcommon.language import Language
web-server/flask_helper.py:5   from libcommon.locale import Locale
web-server/flask_helper.py:6   from libcommon.validator import Validator, ValidationType
web-server/flask_helper.py:9   from libcommon.logger import Logger
web-server/flask_helper.py:10  from libcommon.color import *
web-server/mails/send_mail.py:22  from libcommon.logger import Logger
web-server/mails/send_mail.py:25  from libcommon.color import *
web-server/mails/send_mail.py:28  from libcommon.locale import Locale
web-server/mails/send_mail.py:34  from libcommon.mail import Mail, MailSendError
web-server/main.py:18  from libcommon.language import Language
web-server/main.py:19  from libcommon.locale import Locale, COMMON_LOCALES_FILE_PATHS
web-server/main.py:22  from libcommon.logger import Logger
web-server/main.py:25  from libcommon.color import *
web-server/main.py:26  from libcommon.validator import Validator, ValidationType
web-server/main.py:29  from libcommon.web.validation_errors import RequiredFieldsNotSatisfiedFormat
web-server/main.py:30  from libcommon.web.http_errors import InvalidContentTypeAPIErrorFormat, \
web-server/main.py:33  from libcommon.web.http_successes import OKAPISuccessFormat, CreatedAPISuccessFormat, \
```
- 使用モジュール: logger / color / language / locale / validator / mail /
  web.validation_errors / web.http_errors / web.http_successes
- 注記: `flask_helper.py` は transformism 自身のサイトファイルであり、libcommon の
  凍結面（language/locale/validator/logger/color）を消費するだけ。thinkx CLAUDE.md の
  「libcommon の flask_helpers は使わない」とは別物（libcommon モジュールではなくサイト内スクリプト）。矛盾ではない。

### F-S2-04 [観察] 使用モジュールは v2.1.0 スナップショットに全て存在
- 照合先: thinkx vendored 実体（`thinkx/web-server/libcommon/`、VERSION v2.1.0 /
  tree_sha256 ab534a69…95b04 = 焼き込み対象アイデンティティ）。
- logger.py / color.py / language.py / locale.py / validator.py / mail.py = OK
- web/validation_errors.py / web/http_errors.py / web/http_successes.py = OK
- `locales/` データ実体も同梱（3 entries）。→ S2-1 の「locales 同梱」条件を先行充足の見込み。

### F-S2-05 [S2-2 の付け替え範囲確定] locale ルートは 2 系統。付け替え対象は 1 つだけ
- `Config.LOCALES_ROOT = join(SRC_ROOT, 'locales')`（config.py:58）→ `web-server/locales/`。
  **サイト自身の locale**（emails.json / error_pages.json / page_metadata.json、実在）。
  libcommon 無関係・**付け替え不要**。main.py:38-40 と send_mail.py:29-31 がこれを参照。
- `COMMON_LOCALES_ROOT = join(abspath(__file__), 'libcommon/locales')`（main.py:37）→
  **libcommon の共通 locales（submodule 直参照）**。**S2-2 で vendored パスへ付け替える唯一の対象**。
- 併記の pre-existing な形の癖: `join(abspath(__file__), 'libcommon/locales')` は
  `abspath(__file__)`（= main.py 自身のパス）に連結しており見かけ上不正。
  ただしサイトコードの挙動修正は本計画の対象外。S2-2 は「vendored 側 locales への付け替え」
  のみ行い、既存ロジックの正誤是正はしない（必要なら Phase 3 型送り）。

### F-S2-06 [観察・実行時経路] メール送信（SES）は import 時に初期化されるが送信はゲートされる
- `web-server/mails/send_mail.py` はモジュールロード時に:
  - L23 `Logger()` 生成、L31 `Locale([f'{Config.LOCALES_ROOT}/emails.json'])` 読み込み
    （サイト locale。vendoring 無関係）
  - L35 `Mail(aws_access_key_id=…, aws_secret_access_key=…, region_name=…)` で SES クライアント構築
- L47 `TEST_SEND = False` / L49 `if ENV != 'production' and TEST_SEND:` により
  **import 時の実送信は発生しない**。→ import/初期化の成立確認は安全に行える。
- 実 SES 送信の検証は本計画では行わず、ステージング（I-STEP2 以降）へ送る（計画 S2-4 準拠）。

### S2-0 実行済みミューテーション
- `2026refactor` ブランチを master(85e59b7) から作成・checkout（計画 S2-0 第1項）。他の変更なし。

---

## S2-1: vendoring bake（v2.1.0）（2026-07-14）

### F-S2-07 [完了] bake 成功・thinkx vendored と byte 一致
- `bash libcommon/scripts/bake.sh v2.1.0 transformism/web-server/` → exit 0。
- VERSION = `v2.1.0` / tree_sha256 `ab534a69ddb3ade5634253bc0d8b0c1bd6ea4e215a856b4320eb9b60b5495b04`
  = thinkx vendored と一致。`diff -r`（pyc 除外）で全ツリー byte 一致。`locales/` 実体同梱
  （api_response.json / errors.json / validation_errors.json）。dev 物は除外済み。
- git 特性: 焼き込み先 `web-server/libcommon` は index 上まだ gitlink(160000) のため、
  親 repo からファイルは不可視（`status` clean）。git 取り込みは gitlink 除去（S2-2）と同時。

---

## S2-2: 配線切り替え（2026-07-14）

### F-S2-08 [解決済・no-op] import 文の書き換えは不要（thinkx 照合で確定）
- 根拠: thinkx（vendored 完了・稼働中）の site-level import は transformism と byte 一致。
  `config.py:17/20`・`flask_helper.py:4-10` が完全同一（`from libcommon.X import ...`）。
- vendored snapshot は submodule と同一パス `web-server/libcommon` に載るため、top-level
  package 名 `libcommon` は不変 → import 文字列は変わらない。**書き換えなし（無変更原則・裁定1）。**

### F-S2-09 [要人間裁定・S2-2 を一時停止] COMMON_LOCALES_ROOT 付け替えは計画と thinkx 実態が矛盾
- 計画 S2-2 手順2: 「`COMMON_LOCALES_ROOT`（main.py:37）を vendored locales パスへ付け替え」。
- 実態:
  1. transformism `main.py:37` の `COMMON_LOCALES_ROOT` は **定義 1 回のみ・他に参照ゼロ =
     デッドコード**。`git grep COMMON_LOCALES_ROOT -- '*.py'` は定義行のみ（1 件）。
  2. common locale の実ロードは **libcommon 自身**が担う: `libcommon/locale.py:49`
     `COMMON_LOCALES_ROOT = (Path(__file__).parent / 'locales').absolute()` を自前計算し、
     `COMMON_LOCALES_FILE_PATHS`（api_response/errors/validation_errors.json）を構成。
     vendoring 後は `web-server/libcommon/locale.py` の `__file__` 相対で
     `web-server/libcommon/locales` に解決 → **サイト側変更ゼロで成立**。
  3. 雛形 thinkx（vendored 完了・稼働中）は main.py の `COMMON_LOCALES_ROOT` を **付け替えず**
     `join(abspath(__file__), 'libcommon/locales')` のまま byte 一致で稼働。
- 帰結: 計画の付け替え指示は **未使用のデッドコードへの「念のため」変更** に相当し、
  無変更原則（裁定1）と thinkx 同型性に反する。付け替えても実挙動は変わらず、
  むしろ thinkx との byte 差分を生む。
- 推奨: import と同様に **no-op 扱い**（付け替えない）。既存のデッドコード是正は
  Phase 3 型の仕分けへ送る（本計画は配線切り替えのみ・サイトコード無変更）。
- **裁定（2026-07-14・人間）**: (a) 付け替えない。計画 S2-2 手順2 は本裁定により **no-op に
  読み替える**（計画書自体の修正は人間が後日行う）。根拠は本 finding の調査（デッドコード・
  libcommon の自己解決・thinkx 稼働実績）。→ import（F-S2-08）と併せ、S2-2 のサイトコード変更は
  **ゼロ**。
- **Phase 3 送り**: `main.py` の未使用 `COMMON_LOCALES_ROOT`（transformism L37 / thinkx L40 の
  **同一行**）はデッドコード。是正は本計画では行わず、thinkx 側の同一行と併せて Phase 3 型
  仕分けの対象とする（挙動のついで修正禁止・無変更原則）。

### F-S2-10 [完了] 手順3: gitlink 除去・vendored 通常ファイル化
- `.gitmodules` から `[submodule "web-server/libcommon"]` 節を削除（`www/playbooks` は残置）。
- `git rm --cached web-server/libcommon`（gitlink 160000 除去）→ `git add web-server/libcommon`
  で vendored 38 ファイルを通常 blob 化。VERSION blob `656eb8a` は thinkx と同一。
- 注: `.gitmodules` を先にステージしないと `git rm --cached` が
  「please stage your changes to .gitmodules」で拒否する（実行順の注意点）。
- submodule は未 init（`.git/config` に submodule.* 無し・nested .git 無し）のため
  `git submodule deinit` は不要だった。

### F-S2-11 [完了・S2-4 への申し送り] 手順4: vendored 解決と import/locale 起動確認
- 検証条件: `.s-track-venv`（py3.10）+ `ENV=develop` + cwd=web-server（アプリ実行と同条件）。
- 結果: 消費 9 モジュール（logger/color/language/locale/validator/mail/web.{validation_errors,
  http_errors,http_successes}）が全て **vendored パスから import・解決**（`ALL_VENDORED`）。
  `COMMON_LOCALES_FILE_PATHS` は libcommon の自己解決で vendored `locales/` の 3 ファイルに
  解決・実在。vendoring 起因の import エラーなし。
- **ハーネス上の落とし穴（S2-4 で必須の前提）**:
  1. cwd が workspace root だと `sys.path[0]=''` が root の `libcommon/`（原本）を先に拾い、
     vendored ではなく原本をロードしてしまう。**必ず cwd=web-server（または sys.path 先頭に
     web-server）で実行する**こと。
  2. `libcommon` は `__init__.py` を持たない**名前空間パッケージ**。`find_spec().origin` は
     None を返すため、解決先は **submブモジュールの `__file__`** で判定する。
  3. libcommon.logger が host `config` を import する設計のため、`ENV`（develop/production）
     未指定だと `config.EnvironmentNotSpecified` で停止する。S2-4 のスモークは thinkx 同型に
     `ENV` を与える conftest/config_test を要する。
- 全アプリ `import main`（ルート/DB 含む）は未実施。S2-4 のスモークハーネスで実施する。

### F-S2-12 [完了] 手順5: カットオーバーコミット
- `build: vendor libcommon v2.1.0, retire submodule`（40 files, `delete mode 160000` 確認）。
  メッセージに VERSION `v2.1.0` と tree_sha256 先頭8桁 `ab534a69` を明記。

---

## S2-3: ルートゴールデンの新設（2026-07-14）

### F-S2-13 [完了・thinkx との差分] config_test の要求キーが thinkx と一部異なる
- ハーネスは thinkx S-0b と同型（conftest / config_test / golden_utils / test_route_sweep /
  test_app_imports の5点）。汎用4点は同一ロジック。config_test のみサイト固有差分あり:
  - **不要（thinkx にはあるが transformism の import 連鎖が参照しない）**: Discord webhook 系
    （`DISCORD_*_WEBHOOK_URL`）、`AVAILABLE_LANGS`（flask_helper は
    `Language.lang_label_map(only=[...])` のハードコード list を使う）。
  - **必要キー**（import 時 check_config / 直接アクセス）: `ENV`, `DEFAULT_LANG`,
    `FLASK_APP_SECRET_KEY`, `HOST_URL`, `MAIL_SENDER`, `MAIL_REPLY_TO`,
    `AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY/DEFAULT_REGION`, `LOCALES_ROOT`。
  - `LOCALES_ROOT` は本番同様サイトの `web-server/locales`（error_pages.json /
    page_metadata.json / emails.json を import 時に読む）。
- mongo/redis/session は import 連鎖に現れない（thinkx 同様）。boto3 は no-op mock。
- 結果: `test_app_imports` / `test_route_sweep` ともに PASS（2 passed）。

### F-S2-14 [要注意・S2-4 に影響] 現状 transformism master の能動ルートは実質 `/` のみ
- 生成ゴールデン `web-server/tests/golden/route_sweep.json` は **2 ルートのみ**:
  - `/` → 200（`main.py:76 @app.route('/')` の top_handler）
  - `/static/<path:filename>` → 404（Flask 既定）
- **多言語（`<lang>`）ルートは 0 件**。`/<lang>/` 含む他ハンドラは main.py で
  **コメントアウト済み**（L60-61 ほか）。errorhandler は 400/404/500/502 が能動。
- これは **vendoring 起因ではなく、master(85e59b7) のサイト実態**（大半のルートが
  コメントアウトされた WIP 状態）。S2 はサイトコード無変更のため現状をそのまま凍結した。
- **S2-4 への影響**: 計画 S2-4 の「多言語ルート（locale 依存ページ）を代表言語で描画確認」は
  **対象が存在しない**（多言語ルート 0）。スモークで curl 照合できるのは `/`（200）と
  `/static`（404）のみ。→ S2-4 着手前に人間へ確認要（この route surface が意図どおりか、
  あるいは master がコメント解除前の中間状態か）。
- **裁定（2026-07-14・人間）**: (A) 現状のまま S2-4 実施。根拠（人間が実サイト確認済み）:
  本番 https://transformism.art/ は単一ページ構成、ナビは全てページ内アンカー、外部リンクは
  store.transformism.art（別システム）のみ。master のルート面（`/` + `/static`）は本番と一致し、
  コメントアウト済みルート群は本番未投入の WIP。凍結対象として master(85e59b7) は正しい。

---

## S2-4: スモーク実行（2026-07-14）

### F-S2-15 [完了] ローカル起動 + curl 照合 + トップページ内容確認
- 実サーバ起動: 自前ランナー（`app` を cwd=web-server で `app.run(127.0.0.1:8137)`）。
  注: main.py の `__main__` ブロックは `app.run(secret_key=…, max_content_length=…)` と
  無効 kwargs を渡すため直接起動不可（pre-existing WIP。本計画では不修正 → Phase 3 送り候補）。
- curl 照合（ゴールデン全 2 ルート）:
  - `GET /` → **200**（ゴールデン一致）
  - `GET /static/x` → **404**（ゴールデン一致）
- **トップページ内容確認（人間追加指示）**: `/` 応答 HTML（17,239 bytes）に "Transformism" が
  **15 箇所**含有。`<title>Transformism - A New Mainstream of Modern …`。実描画（language_wrapper
  経由・locale 解決）が成立。
- **vendored libcommon の実行時使用を確証**: サーバ stderr
  `libcommon path: ['…/transformism/web-server/libcommon']`（workspace-root 原本ではない）。
- **多言語描画確認**: 対象 **0 件**（F-S2-14 のとおり）。実施項目なし。
- **SES メール経路**: import/初期化のみ成立（Mail() が dummy creds で boto3 client 構築、
  ログに `AWS_ACCESS_KEY_ID:test-key SES_REGION:us-east-1`）。`TEST_SEND=False` により
  実送信なし。**実 SES 送信の検証はステージング（I-STEP2 以降）へ送る**（計画 S2-4 準拠）。
- ランナー・ログはスクラッチパッド（リポジトリ外）。リポジトリへの変更なし（S2-4 は検証のみ）。

---

## S2-5: 規範文書の新設（2026-07-14）

### F-S2-16 [完了] transformism/CLAUDE.md 新設
- thinkx / kazukiotsukacom（repo ルート・簡潔版）を雛形に、計画 S2-5 の要求を反映して新設:
  vendoring/bake、golden 位置と再生成・検証手順、実行前提3点（cwd=web-server / 名前空間
  パッケージ / ENV 注入）、ビルド/起動（`python main.py` 直接起動不可の注記）、
  `www/playbooks` 不触、SES ステージング送り。
- **裁定反映（人間指示）**: route surface の事実（能動ルートは `/` のみ、`/<lang>/` 等は
  本番未投入の WIP としてコメントアウト・実サイト照合済み）を明記し、将来セッションが
  コメントアウト群を「誤削除」と誤解して復活させる事故を防ぐ注意書きを入れた。
- bake.sh は vendored ツリーから CLAUDE.md を除外するため、`web-server/libcommon` 配下に
  ネストした CLAUDE.md は生じない（in-context 汚染なし）。

---

## S2-6: 完了処理（2026-07-15）

### Phase 3 型仕分け候補一覧（後日の人間仕分けの入力・本トラックでは不修正）

本 S2 トラックはサイトコード無変更（配線切り替え + オラクル新設のみ）のため、下記は
**是正せず記録のみ**。Phase 3（バグ修正計画型）の仕分け入力とする。

- **[Phase3候補] main.py `__main__` の無効 kwargs で `python main.py` 直接起動不可**（F-S2-15）
  - `main.py` 末尾 `app.run(debug=True, secret_key='…', max_content_length=70000000)` は
    Flask の `app.run()` が受け付けない `secret_key` / `max_content_length` を渡す。
  - 影響: `python main.py` での直接起動が失敗（TypeError）。本番は uwsgi、ローカルは
    `app` を import して起動する運用で回避中。
  - 是正案（仕分け時）: `secret_key` は `app.secret_key`（既に別行で設定済み）へ、
    `max_content_length` は `app.config['MAX_CONTENT_LENGTH']` へ移す。

- **[Phase3候補] 未使用 `COMMON_LOCALES_ROOT`（デッドコード）— transformism / thinkx 両方**（F-S2-09）
  - `main.py` の `COMMON_LOCALES_ROOT = join(abspath(__file__), 'libcommon/locales')` は
    定義のみで参照ゼロ。共通 locale の実ロードは libcommon が自己解決するため未使用。
  - 対象は **transformism `main.py:37` と thinkx `main.py:40` の同一行**（両サイト同時に是正）。
  - 併記: 形自体も `join(abspath(__file__), …)` で見かけ上不正（`__file__` はファイルパス）。
  - 是正案（仕分け時）: 行削除（未使用のため）。挙動不変。

- **[Phase3候補] その他**: 上記 2 件以外に S2 実行中で新規発見した Phase 3 候補は無し。
  （コメントアウトされた `/<lang>/` 等のルート群は本番未投入の WIP = 製品意思決定事項であり、
  コード品質バグではない。Phase 3 仕分け対象ではなく、復活は人間の本番投入判断を伴う別作業。
  F-S2-14 / CLAUDE.md の誤解防止注記を参照。）

### S2 完了判定（計画準拠）

- S2-4 スモーク green（`/`→200・`/static`→404・トップページ実描画 "Transformism" 含有）＝ 達成
- S2-5 `transformism/CLAUDE.md` 新設 ＝ 達成
- `2026refactor` へ push 完了（origin と同期・作業ツリー clean）＝ 達成
- **→ 計画の完了判定を全て満たす。**
- 残: ROADMAP のチェック更新・I-STEP2 の transformism 注記削除は**人間が行う**（計画明記・実行者は触らない）。
