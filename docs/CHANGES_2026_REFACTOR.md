# 2026 リファクタリング作戦 — 変更総覧

Phase 1(simplicity)/ Phase 2(libcommon+quantz-web)/ Phase 2.5(静的サイト)/
Phase 4a・4b(auth)/ Phase 3(バグ修正+v2.1.0 全系再配布)の全変更のうち、
**利用側のコードの書き方が変わるもの・根本的なもの**を列挙する。
各項目は「変更後」のコードが正であり、以後の新規実装はこの形に従う。

---

## A. 根本的な変更(アーキテクチャ・import・配布)

### A-1. libcommon の依存注入化(最重要。レイヤ逆転の解消)

libcommon がホストアプリの `config.py` と `models/data/user.py` を import する構造を廃止。
**libcommon はどのアプリからも素の venv で import 可能**になった。アプリ固有の値・
オブジェクトは、アプリ起動時(main.py)に明示注入する:

```python
# main.py(アプリ起動時に1回)
from libcommon.web.session import Session
from libcommon.web import flask_helpers

Session.configure(host=Config.REDIS_SESSION_HOST,
                  port=Config.REDIS_SESSION_PORT, db=Config.REDIS_SESSION_DB)

flask_helpers.configure_flask_helpers(
    default_lang=Config.DEFAULT_LANG,
    available_langs=Config.AVAILABLE_LANGS,          # 旧: libcommon 内ハードコード(F-4)
    basic_auth_username=Config.BASIC_AUTH_USERNAME,
    basic_auth_password=Config.BASIC_AUTH_PASSWORD)

session_helper = flask_helpers.make_session_helper(  # 旧: from libcommon import session_helper
    user_loader=lambda uid: User.objects(id=uid).first(),
    on_no_session=UnauthorizedAccessError,
    on_user_not_found=UserNotFoundError)
```

- `session_helper` は**アプリが生成するデコレータ**になった(ハンドラ側の使い方は従来同一:
  `@session_helper` を積み、`def handler(user, ...)` で受ける)。
- `user_loader` が将来の auth SSO 統合の差し込み口(ローカル User 取得 ⇄ auth 照会を
  この関数の差し替えだけで切り替えられる)。
- Session は import 時に Redis 接続しない。`configure()` 前に使うと
  `RuntimeError('Session.configure() must be called at app startup')`。

### A-2. libcommon の配布: git submodule → vendoring(実物コピー+VERSION)

```
web-server/libcommon/VERSION
  version: v2.1.0
  tree_sha256: ab534a69ddb3ade5634253bc0d8b0c1bd6ea4e215a856b4320eb9b60b5495b04
```

- 消費先(quantz web-server / quantz vectordb / thinkx / kazukiotsukacom / auth)は
  **同一タグを同一 bake.sh で焼くと byte 同一**(上の hash が全系で一致=実測)。
- 更新フロー: **原本リポジトリで修正 → タグ → `scripts/bake.sh <tag> <dest>` で再焼き**。
  vendored コピーの直接編集は禁止(settings deny + hash 照合の二重防御)。
- clone 直後に `git submodule update` 不要。デプロイ手順から submodule 取得が消えた
  (thinkx の playbooks submodule のみ従来通り)。
- bake ツリーは痩身済み: `tests/ attic/ scripts/ CLAUDE.md refactor_plan.md findings.md
  CHANGELOG.md ruff.toml pyrightconfig.json` は焼き込まれない。tree hash は
  `__pycache__`/`*.pyc` 除外で算出。

### A-3. simplicity の import 方式(変更しないことを確定)

simplicity は **concat + グローバル名前空間を恒久維持**。`src/` への
import/export/require は禁止(D-1)。消費側は従来通り:

```html
<script src="/js/simplicity/simplicity.js"></script>  <!-- classic script。ESM ではない -->
```

### A-4. レスポンスの正典を一本化

例外 raise 型の並立系(`api_response_v1.py`+`errors_v1.py`)は attic/ へ退避、
`[DEPRECATE]api_errors.py`(705行)は削除。**正典は pydantic フォーマット族のみ**:

```python
from libcommon.web.http_errors import UnauthorizedAccessErrorFormat
from libcommon.web.http_successes import OKAPISuccessFormat
return OKAPISuccessFormat(message='ok', data={...}).http_response()
```

エラー外形 `{field_name, code, message, reason}` / 成功外形 `{code, message}` は
PROTOCOL.md §5(auth)が依存する凍結契約。**変更は追加のみ**(契約錨テストが機械強制)。

---

## B. API 仕様の変更(利用コードが変わるもの)

### B-1. dateutils: 正名 API と epoch 対の追加、例外の正常化

```python
from libcommon.dateutils import (
    datetime_to_iso8601, iso8601_to_datetime,   # 正名(aware UTC 既定)
    datetime_to_epoch, epoch_to_datetime,        # 新規: 数値との往復対
    InvalidISOFormatError,                       # 新規: 不正入力で raise(旧: NameError で自壊)
)
now_str = datetime_to_iso8601()                  # 既定が aware UTC(多地域整合)
```

- 旧名 `*_iso8061_*`(typo)は互換エイリアスとして残存するが **deprecated**
  (既定 tz 呼び出しが壊れたまま互換凍結)。新規コードは正名のみ使用。
- ドクトリン: 保存・演算は常に aware UTC、表示時のみ変換、naive datetime を新規に作らない。

### B-2. Session: 型と挙動の修正

```python
Session.start(str(user.id))      # user_id は str(ObjectId 文字列)。旧型ヒント int は嘘だった
```

- **TTL が秒として正しく効く**(旧: `timedelta(days=秒数)` の単位バグで 3600 秒設定が
  約10年セッションになっていた → 1時間に)。既存の稼働セッションの体感が変わりうる
  最大の挙動変更。
- `Session.start` が `session:{sid}` を書くようになり、`Session.count()` が
  ログイン直後から正しい端末数を返す。

### B-3. flask_helpers: エラー経路が正しい HTTP エラーを返す

旧: 必須クエリ欠落・一部バリデーション異常系が **NameError → 500**。
新: 正しいフォーマットで **400**(実波及の例: `/v1/users/verify_link` と
`/v1/<lang>/users/verify_link` の2ルートが 500→400 に。route golden 更新済み):

```json
{"errors": [{"field_name": "q", "code": 400, "message": "...", "reason": "REQUIRED_FIELDS_NOT_SATISFIED"}]}
```

デコレータの正典的積層順(route → language_wrapper → content_type_check_json →
required_fields_check → regex/format/length → 本体冒頭 validate_request)は不変。

### B-4. quantz-web: サンプル実装規約(新規実装が引用する型)

```python
# (1) 二重ルートの一括登録(旧: /v1/xxx と /v1/<lang>/xxx を手で2回書く)
route_with_lang(blueprint_accounts, '/signup')

# (2) デバッグ判定のハードコード廃止
is_debug = email in Config.DEBUG_USER_EMAILS   # 旧: ["dev1@thinkxinc.com", ...] 直書き
```

```html
<!-- (3) テンプレ→JS の受け渡しは単一 JSON 注入(旧: スカラ個別注入で数値が文字列化) -->
<script>const PAGE_DATA = {{ page_data | tojson }};</script>
```

いずれも代表箇所で実証済み(全面展開は次期)。新規画面はこの形で書く。

### B-5. quantz-web: import 副作用の除去

- `mails/send_mail.py` — **import してもメールは送信されない**(旧: import 時に SES 実送信
  2通)。手動テストは `python send_mail.py`(`if __name__` ガード)。
- `users_create` — 空 JSON POST が 500(KeyError)ではなく 400(バリデーション)を返す。

### B-6. simplicity: Validator の実効化(挙動変更に注意)

```javascript
// postal_code_format が実際に検証するようになった(旧: case 欠落で全入力素通し)
new Validator([{ type: ValidationErrorType.postalCodeFormat, ... }])
```

- 既存フォームで**不正な郵便番号が新たに弾かれる**ようになる。
- `maxLength` は null 入力で落ちない(null ガード追加、minLength と同型)。
- `notCorresponding` は未実装のまま(消費ゼロにつき次期。使用しないこと)。

### B-7. simplicity: その他の修正

```javascript
Browser.getValueFromHash(...)   // 旧: Browswer(タイポ)— hashchange のたび ReferenceError だった
```

- エラー経路の console.error がスコープ外変数で自壊しない(F-9)。
- file_upload_view の setter が正しい引数を switch する(F-10)。
- リスナー/タイマー解放(F-5)は監査の結果**コード変更なし**が着地: 両 setInterval は
  自己解放済みと実測確認(計画の「file_upload L484 は確実な漏れ」は誤りだった)。
  実害のある漏れは draggable のリスナーのみで、次期サイクル送り。
- リネーム: `models/userbase.js` → `models/user_base.js` ほか(snake_case 統一。
  concat バンドルなので消費側の参照名(クラス名)は不変)。

---

## C. 削除・退避されたもの(参照するとエラー/存在しない)

| もの | 処置 |
|---|---|
| `libcommon/web/[DEPRECATE]api_errors.py`(705行) | 削除 |
| `api_response_v1.py` / `errors_v1.py`(例外族・消費ゼロ) | `attic/` へ退避(bake にも含まれない) |
| `libcommon.response.*`(存在しないモジュール) | quantz material_v1 の import を除去。celery.py の残存分は次期 |
| simplicity の孤児ファイル群(MapPointer 系ほか) | `attic/` へ退避 |
| 死テスト2ファイル(mongobase/modelbase) | 削除 |

## D. 開発フローの変更(コードではなく作法)

- **各リポジトリの規範は CLAUDE.md**(simplicity R-11 / libcommon L-7 / 各サイト S-4 / auth)。
  変更時は各レポの検証ゲートを green にしてからコミット:
  - libcommon: `pytest` / `ruff check .` / `pyright`
  - quantz-web: `pytest`(route sweep + API 3型スナップショット)
  - simplicity: `npm run build` → dist sha 台帳一致 / `node --test 'test/**/*.test.js'` /
    ESLint(no-undef+自動グローバル生成)/ tsc 構文ゲート
  - 静的サイト: `pytest`(スモーク+route golden)。libcommon 焼き直し後は必ず実行
- 依存は exact ピン。無断アップグレード禁止(typescript は 6.0.3 固定)。
- ブランチ: 全リポジトリ `2026refactor`(simplicity の Phase 1 完遂のみ `refactor/2026` が歴史)。
  タグ: simplicity `refactor-v1-complete` / libcommon `v2.0.0`(注入 API 確立)`v2.1.0`(バグ修正+痩身 bake)。
- バグを見つけたら修正せず findings.md へ(次期バグ修正サイクルの入力)。
  セキュリティ疑いのみ即停止・報告(D-22)。