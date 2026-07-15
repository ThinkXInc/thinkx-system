# CLAUDE.md — auth (全サービス共通アカウントサービス)

このリポジトリで作業する際の規約。ここに書かれた規約の多くは tests/ の静的ゲートで
機械検査される。ゲートを通らないコードはマージしない。

## このアプリは何か

ThinkX の全サービス共通アカウント (ログイン・課金状態) を持つ唯一の場所。apps の一つとして
quantz-web / thinkx と同じ形 (Flask + uWSGI + nginx-root 配下) で稼働する。
各サイトとの通信契約は **PROTOCOL.md がすべて**。実装は契約に従う。契約に無い
エンドポイント・パラメータ・レスポンスキーを実装に足すことは、PROTOCOL.md の
更新とセットでなければ禁止。

文書の役割分担:
- `PROTOCOL.md` — ワイヤ上の契約 (凍結ルール §6 あり)。最優先。
- `CLAUDE.md` (この文書) — コードの書き方。
- `docs/API設計原則_原本.md` — 方針の発言原文。判断に迷ったらここへ戻る。
- `PROTOCOL_ROADMAP.md` — 次段階 (B2B API・ユーザー委任) の計画。先回り実装はしない。

## 命名

- **キーを見て中身が完全にわかる命名。一つの事実に一つの名前。別名・エイリアスは禁止**
  (config キー、HTTP ヘッダ、関数名、どこであっても。「secret でも service_secret でも
  読める」のような親切は、将来のずれの種なので書かない)。
- 外部 (Google 等) と話す境界だけは相手の名前 (sub, aud 等) で読み書きする。
  内部では使わない。
- 内部モデルの言語フィールドは既存コードベース全体に合わせ `lang`。
  ワイヤ上 (UserInfo) では OIDC 準拠の `locale`。変換は protocol.py が行う。

## HTTP ハンドラの書き方 (デコレータ積層 — 順序は契約)

quantz-web と同一の型。全ハンドラがこの形に従う。

```python
@blueprint_x.route('/v1/path', methods=['POST'])
@blueprint_x.route('/v1/<lang>/path', methods=['POST'])   # 二重ルート登録は必須
@language_wrapper                                          # 必須。lang 検証と lang_name 供給
@content_type_check_json                                   # POST(JSON) は必須
@required_fields_check(['field_a', 'field_b'])
@regex_check('field_a', SOME_REGEX, 'locale_key')
def handler(lang, lang_name):
    validation_error = validate_request(lang, locale)      # 積層の検証結果を回収
    if validation_error:
        return validation_error.http_response()   # errors 配列型は全アプリ共通契約のまま
    ...
```

- バリデーションは libcommon のデコレータで行う。**ハンドラ内での必須チェック・
  形式チェックの再実装 (私設の `_required` / `_api_error` 等) は禁止。**
- レスポンスは libcommon の SuccessFormat / http_errors の名前付きエラークラス
  (UnauthorizedAPIErrorFormat 等) を使う。APIErrorFormat を直接組み立てない。
- SSO のエラーレスポンスには protocol_version を含める (PROTOCOL.md §5)。
  `protocol.with_protocol_version(...)` を通すこと。

## libcommon の使い方

- セッション: `libcommon.web.session` の Session / RedisSessionInterface。app 起動時
  (main.py) に `Session.configure(host, port, db)` で Redis を注入し、`RedisSessionInterface`
  には host/port/db/expiration を渡す (L-1)。cookie 名はこのアプリ固有 (`thinkx_auth_session`)。
  サイトと共有しない。
- 多言語: `libcommon.locale.Locale('xxx.json')` + `locales/xxx.json`
  (形式: `{key: {lang: text}}`)。**locale.get を try/except で包んでキーを
  そのまま返すフォールバックは禁止** — キー欠落は大声で落とす (fail loudly)。
- ログ: `libcommon.logger.Logger` + `libcommon.color`。квantz と同じ流儀。
- config: 各モジュール冒頭で `from config import Config, check_config` し、
  REQUIRED_KEYS_IN_CONFIG を宣言して check する (app 側モジュールの現行規約)。
  libcommon 内部への config 供給は L-1 (v2.0.0) で注入方式 (`Session.configure` /
  `configure_flask_helpers` / `make_session_helper`) に統一済み。libcommon が
  `from config import Config` でホストへ逆依存することは禁止 (もう起きない)。app は
  main.py / app_session.py で config 値と User 取得ロジックを注入する。
- **存在しない libcommon API を推測して書かない。** try/except ImportError や
  hasattr で「将来できるはずの API」を探るコードは禁止。必要な API が無ければ、
  PLAN_libcommon_simplicity.md に追記して libcommon 側で作る。

## UserInfo とプロトコル

- UserInfo (ワイヤ上の JSON) を組み立てるのは **protocol.py の build_userinfo だけ**。
  他のファイルで dict を組み立てない。
- protocol.py は Flask / Mongo / config に依存しない純粋モジュールに保つ
  (契約テストを外部依存なしで走らせるため)。
- Stripe の生ステータスは User.services[*].stripe_subscription_status に生のまま保存し、
  ワイヤに出すときに protocol.py が4値 (billing_status) へ丸める。丸めはここ以外でしない。

## 禁止事項 (静的ゲートの検査対象)

- `request.get_json(silent=True)` — content_type_check_json を使う。
- 私設のエラーヘルパ (`def _api_error` 等) — 名前付きエラークラスを使う。
- 同一の値に対する複数のヘッダ名・キー名。
- `sub` / `client_id` / `available_services` 等、旧命名・不採用命名の使用。
- JWT / refresh_token の実装 (protocol_version 2 の引き金成立まで。PROTOCOL.md §7)。
- console 相当の print デバッグ。logger を使う。

## 前倒し実装の条件 (D-25 / docs/AUTH_TRACK.md)

この auth はロードマップ Phase 4 の前倒しとして、libcommon 計画 (Phase 2) 完了前に
建てられた。安全条件は4つで、すべて構造化済み:

1. **現行 libcommon に対して書く。未来 API の推測禁止** — tests/test_conventions.py が検査。
2. **CLAUDE.md が実装より先** — この文書。
3. **libcommon はスナップショット vendoring** — libcommon 原本の `scripts/bake.sh` (L-8) で
   `bake.sh v2.0.0 web-server` と焼く。VERSION に `version: v2.0.0` と tree_sha256 (`__pycache__`/
   `*.pyc` 除外) を記録。submodule は新設しない。**vendored コピーは読み取り専用** — 修正は
   libcommon 原本で行い、焼き直す (.claude/settings.json の deny と VERSION のハッシュ照合で強制)。
   (Phase 4b 追随済み: pre-v2.0.0 スナップショットから v2.0.0 へカットオーバー。)
4. **libcommon v2.0.0 出荷後、PLAN_followup_L1.md の追随を経てから本番投入する。** (追随完了。)

## 起動・テスト

```
path/to/libcommon/scripts/bake.sh v2.0.0 web-server   # 焼き直し時 (web-server/libcommon を生成)
cd web-server && pip install -r requirements.txt && cd ..
python3 -m pytest -q tests              # 外部依存なしで走る契約・規約ゲート
cd web-server && python3 main.py        # local (development)
```

本番は uWSGI + systemd (uwsgi_auth.service)、nginx-root の conf.d/auth_web.conf 経由。
