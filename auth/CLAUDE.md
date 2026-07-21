# CLAUDE.md — auth (全サービス共通アカウントサービス)

このリポジトリで作業する際の規約。ここに書かれた規約の多くは tests/ の静的ゲートで
機械検査される。ゲートを通らないコードはマージしない。

---

## 【2026-07 更新】auth-spec 準拠への移行(最優先で読むこと)

本ファイルの以下の旧記述は、旧 PROTOCOL.md v1 の scaffold 用に書かれたものである。
auth の正本は `docs/auth-spec/`(monorepo/auth/docs/auth-spec/)とソースコード・契約テストへ
移行した(DECISIONS D-38/D-39)。**本節は以下の旧記述すべてに優先する。**

- **正本の変更**: PROTOCOL.md は「最優先・すべて」ではなく参照プランに格下げ。
  endpoint / request / response の正本は `docs/auth-spec/` とソースコード・契約テスト。
  文書とコードが食い違う場合はコードと契約テストを正とする(auth-spec D-14)。

- **OIDC / JWT / JWKS は許可**: auth は OpenID Connect Core の Authorization Code Flow +
  PKCE(S256) を実装し、ID Token を RS256 JWT で署名し、JWKS と OpenID Provider metadata を
  公開する。`import jwt`・`jwks`・`RS256` 等の使用を禁止しない。

- **標準 endpoint はハンドラ規約の例外**: 次の OAuth/OIDC 標準 endpoint は、OAuth/OIDC の標準
  request / response 形式に従う。これらには「言語二重 route(`/v1/<lang>/...`)」
  「`@language_wrapper` 必須」「libcommon response wrapper」「`protocol_version` の付与」を
  **適用しない**。
  - `GET /oauth/authorize`
  - `POST /oauth/token`
  - `GET|POST /oauth/userinfo`
  - `GET /oauth/jwks`
  - `GET /.well-known/openid-configuration`
  - `POST /oauth/logout`

- **通常 account API は従来規約を維持**: 上記標準 endpoint 以外の通常の account API には、
  本ファイル下部の「HTTP ハンドラの書き方(デコレータ積層)」「命名」「libcommon の使い方」
  「禁止事項」をそのまま適用する。

- **UserInfo と ID Token の分離**: ID Token は認証 claim のみ
  (iss / sub / aud / exp / iat / nonce / auth_time)。email / email_verified / picture 等の
  プロフィール、billing 状態は `/oauth/userinfo` から返す。ID Token に billing を入れない
  (auth-spec 02/03、DECISIONS D-43)。`email_verified` は User の永続フィールドではなく
  `is_primary_email_verified()` の結果として導出する(auth-spec D-09)。

- **wire 名は標準に統一**: 接続サービスの識別子は wire 上 `client_id`、認可コードは `code`、
  照合値は `state`(内部名 `authorization_transaction_id`)。旧 `service_id` / `auth_code` /
  `service_secret` の wire 名は使わない(auth-spec 00 命名規約)。

- **billing 保存先は User ではない・auth は非権威な投影**: 旧
  `User.services[*].stripe_subscription_status` は使わない。billing の真実源(権威)は payment
  サービスであり、auth が持つのはその **読み取り専用の投影(projection)** である。auth 側の
  entitlement は payment からの push でのみ更新され、auth 自身のロジックで昇格・降格しない。
  投影は独立モデル
  `ServiceEntitlement(subject, client_id, plan, billing_status, payment_event_id, source_event_timestamp, updated_at)`
  に保存する。サービス接続の事実は `ConnectedService(subject, client_id, connected_at)` と
  分ける(DECISIONS D-45)。詳細は下部「UserInfo とプロトコル」節。

- **libcommon 版数**: vendoring 対象は L 計画完了後の版に更新する。本ファイル下部の v2.0.0
  表記は、L 計画完了後の現行版(v2.1.0 系 → L で更新)に読み替える。

- **実装計画**: L(libcommon Session 拡張)→ A(auth server 本体)→ C(reference client)→
  I(infra)の順に、1セッション1計画で進める(ROADMAP Phase 4d)。

---

## このアプリは何か

ThinkX の全サービス共通アカウント (ログイン・課金状態) を持つ唯一の場所。apps の一つとして
quantz-web / thinkx と同じ形 (Flask + uWSGI + nginx-root 配下) で稼働する。

> 【更新】各サイトとの通信契約は、上記「移行」節のとおり `docs/auth-spec/` とソースコード・
> 契約テストが正本。以下の「PROTOCOL.md がすべて/最優先」という旧記述は参照プランへの格下げ後は
> 適用しない。契約に無いエンドポイント・パラメータ・レスポンスキーを足さない原則自体は維持し、
> その「契約」の実体を auth-spec + 契約テストとして読む。

文書の役割分担:
- `docs/auth-spec/` — **正本**。プロトコルフロー・セキュリティ根拠・データ/インフラ・判断記録・
  テスト/運用。実装とハンドラの契約はこことソースコード・契約テストで確定する。
- `PROTOCOL.md` — 参照プラン(旧 v1・格下げ済み)。歴史的経緯の参照用。
- `CLAUDE.md` (この文書) — コードの書き方(通常 account API の規約 + 上記標準 endpoint 例外)。
- `docs/API設計原則_原本.md` — 方針の発言原文。判断に迷ったらここへ戻る。

## 命名

- **キーを見て中身が完全にわかる命名。一つの事実に一つの名前。別名・エイリアスは禁止**
  (config キー、HTTP ヘッダ、関数名、どこであっても。「secret でも service_secret でも
  読める」のような親切は、将来のずれの種なので書かない)。
- 外部 (Google 等) や OAuth/OIDC の wire 境界だけは相手の名前 (sub, aud, client_id, code,
  state 等) で読み書きする。内部では実態に合った名前を使う
  (例: 内部 `authorization_transaction_id` ↔ wire `state`。auth-spec 00 命名規約)。
- 内部モデルの言語フィールドは既存コードベース全体に合わせ `lang`。
  ワイヤ上 (UserInfo) では OIDC 準拠の `locale`。変換は protocol.py が行う。

## HTTP ハンドラの書き方 (デコレータ積層 — 順序は契約)

> 【適用範囲】この節は **通常 account API** に適用する。上記「移行」節に挙げた
> OAuth/OIDC 標準 endpoint(`/oauth/*`・`/.well-known/*`)には適用しない
> (それらは標準 request/response 形式に従う)。

quantz-web と同一の型。通常 account API の全ハンドラがこの形に従う。

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
- 通常 account API のエラーレスポンスには protocol_version を含める (PROTOCOL.md §5)。
  `protocol.with_protocol_version(...)` を通すこと。
  **【例外】OAuth/OIDC 標準 endpoint のエラーは標準形式(`{"error": "..."}` 等)を返し、
  protocol_version を付けない。**

## libcommon の使い方

- セッション: `libcommon.web.session` の Session / RedisSessionInterface。app 起動時
  (main.py) に `Session.configure(host, port, db)` で Redis を注入し、`RedisSessionInterface`
  には host/port/db/expiration を渡す (L-1)。cookie 名はこのアプリ固有 (`thinkx_auth_session`)。
  サイトと共有しない。
  **【L 計画で追加】** auth-spec 準拠のため、Session に `id()` / `browser_context_id()` /
  `clear_current()` / `revoke_all(user_id)` / `start(user_id, browser_context_id=...)` を
  libcommon 正本側で追加する(L 計画)。中央 Session の失効は `revoke_all(str(user.id))`
  (逆引きキー `sessions:{user_id}` と一致させる)、外部失効通知は `subject_id` を使う
  (auth-spec 01 の訂正、findings 記録済み)。
- 多言語: `libcommon.locale.Locale('xxx.json')` + `locales/xxx.json`
  (形式: `{key: {lang: text}}`)。**locale.get を try/except で包んでキーを
  そのまま返すフォールバックは禁止** — キー欠落は大声で落とす (fail loudly)。
- ログ: `libcommon.logger.Logger` + `libcommon.color`。quantz と同じ流儀。
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
- **【auth-spec で分離】** ID Token(iss/sub/aud/exp/iat/nonce/auth_time)と
  UserInfo(sub/email/email_verified 等)は責務が別。ID Token 署名は oidc/id_token.py、
  UserInfo 組み立ては protocol.py。billing 状態は ID Token に入れず UserInfo(または
  サービス情報 API)で返す。
- **billing の保存先は User.services ではない。真実源は payment、auth は投影。**
  旧 User.services[*].stripe_subscription_status は使わない(旧 payment 混在の廃止。
  DECISIONS D-45)。billing の権威(真実源)は payment サービスであり、auth が持つのは
  読み取り専用の投影(projection)。auth 側の entitlement は payment からの push でのみ
  更新され、auth 自身のロジックで書き換えない。独立モデル
  ServiceEntitlement(subject, client_id, plan, billing_status, payment_event_id,
  source_event_timestamp, updated_at) に保存する。Stripe customer id / PaymentIntent /
  カード情報は auth は持たない。
- **投影の更新は冪等かつ単調。** payment→auth の push は payment_event_id で冪等(同一
  イベントを二重適用しない)。加えて source_event_timestamp で単調性を守り、保存済みの
  timestamp より古いイベントは破棄する(webhook の順序転倒・再送で新しい状態が古い状態に
  上書きされるのを防ぐ)。timestamp の厳密な意味(Stripe の created / sequence 等)は payment
  連携実装時に確定する。auth 初版はこの「古い更新は破棄」ルールだけ守る。
- **entitlement 不在 = アクセス拒否ではない。** ServiceEntitlement のレコードが無いことは、
  そのサービスのデフォルト状態(多くは無料/オープン枠)を意味する。billing_status を読む側は
  「entitlement が無ければデフォルト枠として扱う」を既定とし、レコードの有無を利用可否の
  判定に直結させない。有料機能のゲートは billing_status の値で行う。
- 接続の事実(どのサービスに接続したか)は ConnectedService(subject, client_id, connected_at)、
  課金権限の状態は ServiceEntitlement に分ける(更新の主体・頻度が違うため。接続は初回一度、
  billing は webhook で反復更新)。両者を1モデルに併合しない。
- UserInfo に billing を出すときは、protocol.py が ServiceEntitlement を読んで4値
  (billing_status) へ丸める。丸めはここ以外でしない。entitlement が無い場合のデフォルト値も
  protocol.py が与える。

## 禁止事項 (静的ゲートの検査対象)

- `request.get_json(silent=True)` — content_type_check_json を使う(通常 account API)。
- 私設のエラーヘルパ (`def _api_error` 等) — 名前付きエラークラスを使う。
- 同一の値に対する複数のヘッダ名・キー名。
- console 相当の print デバッグ。logger を使う。

> 【更新】旧「JWT/JWKS/refresh_token 禁止」は解除した(DECISIONS D-39)。auth は OIDC を実装する。
> ただし `refresh_token` は auth-spec が採用していない(access token は opaque・短期)ため、
> refresh_token の新規実装はしない。OIDC 契約の機械的強制は A-9 の新契約テストが担う。

## 前倒し実装の条件 (D-25 / docs/AUTH_TRACK.md)

この auth はロードマップ Phase 4 の前倒しとして、libcommon 計画 (Phase 2) 完了前に
建てられた。安全条件は4つで、すべて構造化済み:

1. **現行 libcommon に対して書く。未来 API の推測禁止** — tests/test_conventions.py が検査。
   (L 計画で libcommon Session を拡張したら、その版に対して書く。)
2. **CLAUDE.md が実装より先** — この文書。
3. **libcommon はスナップショット vendoring** — libcommon 原本の `scripts/bake.sh` (L-8) で
   焼く。VERSION に version と tree_sha256 (`__pycache__`/`*.pyc` 除外) を記録。submodule は
   新設しない。**vendored コピーは読み取り専用** — 修正は libcommon 原本で行い、焼き直す
   (.claude/settings.json の deny と VERSION のハッシュ照合で強制)。
4. **libcommon 出荷後、追随を経てから本番投入する。**
   (Phase 4b で v2.0.0 追随済み。L 計画で Session 拡張版へ再追随する。)

## 起動・テスト

```
path/to/libcommon/scripts/bake.sh <version> web-server   # 焼き直し時 (web-server/libcommon を生成)
cd web-server && pip install -r requirements.txt && cd ..
python3 -m pytest -q tests              # 契約・規約ゲート
cd web-server && python3 main.py        # local (development)
```

本番は uWSGI + systemd (uwsgi_auth.service)、nginx-root の conf.d/auth_web.conf 経由。