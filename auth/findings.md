# findings — auth 前倒しトラック (Phase 4a)

形式: `ファイル:行 / 事実`。解釈・修正方針は書かない。Phase 4b / Phase 3 の入力。
セキュリティ疑い (D-22) は本ファイルに流さず即停止・人間報告する運用。本セッションで D-22 該当なし。

## 起動足場の確立中に観測した事実

- `.claude/settings.json:4-56` / deny 配列に `quantz-web/web-server/libcommon/**` 等はあるが、auth 自身の
  `web-server/libcommon/**`(vendored)への Edit/Write deny は無い。auth/CLAUDE.md 前倒し条件3 は
  「vendored コピーは .claude/settings.json の deny と VERSION のハッシュ照合で強制」と記す。
- `docs/AUTH_TRACK.md` / 不在。DECISIONS D-25・D-26 と `auth/CLAUDE.md`(改訂版・前倒し実装の条件)が
  参照するが、workspace・auth いずれにもファイルが無い。
- `web-server/config.py.example:1-56` / `PASSWORD_ENCRYPT_KEY` を含まない。
  `web-server/libcommon/cipher.py:36` が `REQUIRED_KEYS_IN_CONFIG=['PASSWORD_ENCRYPT_KEY']` を要求し、
  `models/data/user.py:25` の `from libcommon.cipher import Cipher` 経由で import 時に check_config が落ちる。
  本セッションで `config.py`(example の複製)に `PASSWORD_ENCRYPT_KEY`(ダミー値)を追加した。
- `web-server/models/data/user.py:48-52` / `UnauthorizedAccessError` が未定義だった。
  `web-server/libcommon/web/flask_helpers.py:8` が `from models.data.user import User, UnauthorizedAccessError, UserNotFoundError`
  を import する(同8行に `# NEEDSFIX: don't depend on data.user`)。本セッションで同名例外クラスを追加した。
- `web-server/requirements.txt` / 元は `Flask redis mongoengine pymongo pytz pydantic msgpack google-auth` の
  8件のみで、`pycryptodome`・`requests` が未列挙だった。
  `web-server/libcommon/cipher.py:21` `from Crypto import Random`(pycryptodome)、
  `web-server/libcommon/web/google_oauth_helper.py` の `google.auth.transport.requests`(requests)が import 時に要求する。
  本セッションで両者を追加・ピンした。
- `web-server/requirements.txt` / `redis` を `5.2.1` にピンした。`redis==8.0.1`(pip 既定で入る最新)は
  `fakeredis==2.26.2` と実行時非互換で、`web-server/libcommon/web/session.py:83` の `self.__redis.ping()` が
  fakeredis 接続で `ResponseError`(RESP3 HELLO ハンドシェイク)を出す。`fakeredis 2.26.2` の宣言依存は
  `redis>=4.3`(緩い)で pip は 8.0.1 を許容する。
- `web-server/sso.py:53` `Locale('sso.json')` / `web-server/accounts.py:45` `Locale('accounts.json')` /
  bare ファイル名。`web-server/libcommon/locale.py:99` は与えられたパスを cwd 相対で `open()` する。
  実体は `web-server/locales/sso.json`・`web-server/locales/accounts.json`。
  quantz-web は `Config.LOCALES_ROOT`(`quantz-web/web-server/config.py:67` = `join(SRC_ROOT,'locales')`、絶対)
  で Locale を呼ぶ。quantz-web の uwsgi は `chdir=../web-server`(`quantz-web/web-server/uwsgi/uwsgi.ini:9`)。
  本セッションは `tests/conftest.py` で import 時 cwd を `web-server/locales` に移して解決した(app ソースは未変更)。
- `web-server/libcommon/web/http_response_formatter.py:54,56` / `Field(default=None, example='user_id')` /
  `Field(..., example='Error message here.')` が pydantic V2 の `PydanticDeprecatedSince20` warning を出す。
- 環境 / 既定 `python3` は `3.9.2rc1`(workspace CLAUDE.md 記載の要件 3.10+ 未満)。
  `/opt/homebrew/bin/python3.11`(3.11.15)が存在。本セッションの `.venv` は python3.11 で作成した。
- `web-server/libcommon/web/flask_helpers.py:8` / libcommon が host アプリの `models.data.user` を import する
  レイヤ逆転(DECISIONS D-8 が L-1 で解消予定とする面)。auth は現行 pre-v2.0.0 スナップショットに対して
  この結合を満たす形で書かれている。
- `scripts/bake_libcommon_snapshot.sh:24` / tree_sha256 の計算が `find . -type f ! -name VERSION` で、
  `__pycache__/*.pyc` を除外しない。テスト実行や本番 import で `web-server/libcommon/**/__pycache__/*.pyc`
  (16件、`.gitignore` 済み・git 追跡0)が生成されると、`find ... | xargs sha256sum | sha256sum` の再計算が
  焼き込み時の値(`eab9e78...`)と不一致になる。`__pycache__`・`*.pyc` を除外して再計算すると一致する
  (= vendored source は無編集)。ハッシュ照合(D-25 条件3 / D-10 CI 照合)は .pyc を除外する必要がある。

## Phase 4b (libcommon v2.0.0 追随) の実施中に観測した事実

- `libcommon/scripts/bake.sh` (L-8) / tree_sha256 を `-not -path '*/__pycache__/*' -not -name '*.pyc'`
  で算出する。上の pre-v2.0.0 スクリプトの .pyc 混入問題は L-8 側で解消済み。auth 側 `scripts/bake_libcommon_snapshot.sh`
  は F-1 に従い削除した(正典は libcommon/scripts/bake.sh の1本)。
- `web-server/libcommon/VERSION` / 焼き直し後 `version: v2.0.0` / tree_sha256 `3359309a30a392a75a97b3fad594569487cb07068f770877202de3096fb57cf0`。
  この値は quantz-web(Q-6)の vendored `web-server/libcommon/VERSION` と**一致**する。同一 tag を同一 bake.sh で焼くと
  消費者間で byte 同一(再現可能 vendoring)であることの実測。
- `libcommon/scripts/bake.sh` は `.git` のみ除去し、`tests/` `tutorials/` `refactor_plan.md` `findings.md`
  `CLAUDE.md` `attic/` `ruff.toml` `pyrightconfig.json` `scripts/` を vendored 配下に含める(quantz-web Q-6 も同形)。
  auth の旧スクリプトは `tests/tutorials` を除去していたため、v2.0.0 追随で vendored 構成が増える(挙動には無影響。
  auth の pytest は `tests/` のみを対象に走るため libcommon/tests は収集されない)。
- `web-server/libcommon/web/flask_helpers.py`(pre-v2.0.0):7-8 の `from config import Config` /
  `from models.data.user import User, UnauthorizedAccessError, UserNotFoundError`(レイヤ逆転)は v2.0.0 で消滅。
  L-1 の `configure_flask_helpers()` / `make_session_helper()` 注入に置換された。auth 側は main.py で config 値を、
  app_session.py で User 取得ロジックと例外を注入する形に配線替えした。
- `web-server/libcommon/web/session.py`(v2.0.0)/ `RedisSessionInterface.__init__(host, port, db, expiration_time_sec, prefix)` /
  `Session.configure(host, port, db)`。pre-v2.0.0 の `RedisSessionInterface(prefix)`(host/port/db を内部で Config 参照)から
  署名が変わり、main.py の初期化を新署名へ機械置換した。
- `tests/golden/smoke_routes.json` / pre-v2.0.0 で凍結した golden に v2.0.0 追随後のアプリが**一致**(21 passed)。
  L-1 注入 API への配線替えは観測可能な挙動を変えない(成果物不変)ことの実測。smoke は `authorize`(Session.user_id
  経由で Session.configure を、language_wrapper 経由で configure_flask_helpers を)を駆動しており、import だけでなく
  実行経路で注入が効いていることを兼ねて確認している。
- 環境 / `web-server/libcommon/{ruff.toml,pyrightconfig.json}` は vendored libcommon 自身の lint 設定であり auth の
  ゲートではない。auth のゲートは `python3 -m pytest -q tests`(規約ゲート test_conventions.py を含む)の1本。

## OIDC 確定仕様の実装前調査で確認した事実

- `docs/auth-spec/01_PROTOCOL_FLOW.md` の失効フロー例は auth 中央 Session に
  `Session.revoke_all(user.subject_id)` を渡す。一方、同ファイルの signin は
  `Session.start(str(user.id), browser_context_id=bctx)` で中央 Session の逆引きを ObjectId 文字列で作る。
  オーナー裁定により、中央 Session 失効は `Session.revoke_all(str(user.id))`、サービスへの外部失効通知は
  `subject_id` を使う。`01_PROTOCOL_FLOW.md` / `03_DATA_AND_INFRA.md` への訂正反映が必要。
- オーナー裁定により、auth 側の接続済みサービスは
  `ConnectedService(subject, client_id, connected_at)` として独立 collection に保存し、
  `(subject, client_id)` に複合 unique index を置く。旧 `User.services` は使用しない。
- `ServicePrincipal(issuer, subject, local_user_id)` は各サービス側が所有する identity mapping、
  `ConnectedService(subject, client_id, connected_at)` は auth 側が所有する接続記録であり、別モデルである。
  `docs/auth-spec/01_PROTOCOL_FLOW.md:18` は auth MongoDB の一覧に `ServicePrincipal` を含めるが、
  `03_DATA_AND_INFRA.md` のモデル配置とオーナー裁定ではサービス側に置く。
- オーナー裁定により、初版 E2E client は `auth/reference-client/` に最小実装を置く。
  旧 quantz-web の統合は後続計画とする。
- auth 単独の project-local venv は未整備で、system Python には pytest がなく、canonical libcommon の
  venv には mongoengine がないため、auth の pytest は conftest 収集前に停止する。L 計画中の
  Session 拡張は canonical libcommon 側の全テストで担保する。A 計画の最初の項目(A-0相当)で
  auth 用 venv を作成し、requirements の依存を導入したうえで、auth pytest が収集・実行できることを
  確認する必要がある。依存は未承認のまま system や既存 venv へ追加しない。

## Auth L-4 libcommon v2.2.0 配布整合性

- L-4 実行時点の `auth/**/libcommon/VERSION` は1件で、`auth/web-server/libcommon/VERSION` のみ。
  reference-client は C 計画で作成するため、snapshot 追加直後に全snapshot照合を再実行する。
- canonical `v2.2.0` を正規 `scripts/bake.sh` でauthと一時ディレクトリへ再bakeした。
  VERSION保存値、VERSIONを除いたauth treeの再計算値、canonical一時bake値はすべて
  `caf94015027a627b95abd54e8e222908f79fcded750b1d345016d60d5a10a3d6` で一致した。
- canonical一時bakeとauth snapshotはbyte identical。auth snapshotの再bake前後にtracked差分なし。
- canonical HEADの最終ゲートは pytest 84 passed、ruff All checks passed、pyright 0 errors
  (既存warnings 5件)。これをもってL計画を完了する。

## Auth A-0 単独テスト環境

- `auth/web-server/venv` を `/opt/homebrew/bin/python3.11` 3.11.15 arm64で作成した。配置は
  CLAUDE_GENERALのcomponent-local `venv` 規則に従い、既存 `auth/.gitignore` の `venv/` 対象内。
- runtime直接依存の根拠は次のとおり。Flaskはmain/accounts/sso、redisはssoとlibcommon Session、
  mongoengineはUser/init_mongodb、pymongoはvendored mongomodelのbson、pytzはUser/mongomodel、
  pydanticはlibcommon response format、msgpackはSession serializer、google-authはGoogle token検証、
  pycryptodomeはUserが使うCipher、requestsはauth_clientとGoogle transportがimportする。
  PyJWTは現行scaffoldでは未importだが、確定auth-specのRS256 ID Token署名・検証に用いる唯一の
  JWTライブラリとして `PyJWT==2.13.0` を固定した。RS256実行に必要なcryptographyも、google-authの
  推移依存へ偶然依存しないよう `cryptography==49.0.0` を直接固定した。Authlibは導入していない。
- test直接依存はpytest、conftestが使うmongomockとfakeredis。`pip check`はbroken requirementsなし。
- venvからのimportでlibcommon package pathは `auth/web-server/libcommon`、Session moduleも同snapshot内。
  別cloneやPyPIのlibcommonは参照していない。
- auth pytestは21件をcollectし、14 passed / 7 skipped / 1 warning。skipはA-9で置換予定の旧PROTOCOL
  v1規約テスト。warningはMongoEngineの既存uuidRepresentation既定値に関するdeprecation。

## Auth A-1 データモデルと seed

- `web-server/models/data/user.py` / password 保存を復号可能な Cipher から Argon2id へ変更し、
  `subject_id`、`suspended_email`、`verified_emails`、`verified_phone_numbers`、`auth_generation`、
  `last_auth_time`、`status` を追加した。`email_verified` / `services` / `stripe_customer_id` は
  MongoEngine field から除去した。email 確認済み状態は `is_primary_email_verified()` で導出する。
- `web-server/models/data/` / `AuthService`、`ConnectedService`、`ServiceEntitlement`、`SigningKey`、
  `VerificationChallenge` を追加した。ConnectedService と ServiceEntitlement は
  `(subject, client_id)` 複合 unique。ServiceEntitlement の payment event 適用は event id 冪等かつ
  source timestamp 単調で、同時刻以前の更新を破棄する。
- `web-server/seed.py` / test User、AuthService、active RS256 SigningKey を冪等に投入する seed を追加した。
  password と client_secret は CLI 引数に載せず環境変数から読む。
- `web-server/requirements.txt` / Argon2id 実装として `argon2-cffi==25.1.0` を直接依存へ追加した。
- `tests/test_data_models.py` / モデル制約、Argon2id、redirect 完全一致、接続一意性、billing 投影の
  冪等性・単調性、seed 冪等性を7テストで固定した。A-1 後の auth pytest は28件 collect、
  21 passed / 7 skipped / 1既存 warning。
- A-1 レビュー追補 / email と suspended_email をまたぐ identity 一意性、Google sub 一意性、
  ConnectedService の並行初回接続、ServiceEntitlement の並行・同時刻更新、active SigningKey 1件制約を
  DB index と原子的 update で固定した。実 MongoDB 固有の index/atomicity は
  `AUTH_A1_REAL_MONGO_URI` が loopback を指す場合だけ走る opt-in テストを追加した。
- A-1 レビュー追補 / seed は `ENV` と Config.ENV の一致、非 production、`AUTH_SEED_ENABLED=1`、
  32 byte以上の client secret、明示 `--reset` を必須にした。再実行時は auth_generation を増やし、
  対象 test User の中央 Session・旧 code・旧 access token を失効する。
- A-1 レビュー追補 / 旧 scaffold が pending/suspended User を認証しないよう accounts/sso を新モデルへ
  配線し、UserInfo の課金材料を User.services から ConnectedService + ServiceEntitlement へ移した。
  レビュー追補後の auth pytest は49件 collect、41 passed / 8 skipped / 1既存 warning。追加skip 1件は
  loopback実MongoDBを明示した場合だけ走る A-1 integration test。

## Auth A-2 署名鍵・JWKS・OpenID Provider metadata

- `web-server/oidc/id_token.py` / active SigningKey を使う RS256 ID Token issuer を追加した。
  ID Token は `kid` header と iss/sub/aud/exp/iat/nonce/auth_time の認証claimだけを持つ。
- `GET /oauth/jwks` / retired 以外の SigningKey を RSA public JWK(kty/use/alg/kid/n/e)として公開し、
  private keyを応答へ含めない。`Cache-Control: public, max-age=300`を付与した。
- `GET /.well-known/openid-configuration` / 固定 `AUTH_PUBLIC_BASE_URL` をissuerとして、authorize/token/
  userinfo/jwks/logout、code response、public subject、RS256、client_secret_basic、PKCE S256を公開する。
- `tests/test_oidc_discovery.py` / metadata、retired鍵除外、必須claimとactive kid、公開JWKによる実検証を
  4テストで固定した。A-2後のauth pytestは53件collect、45 passed / 8 skipped / 1既存warning。

## Auth A-3 OIDC authorize / signin resume / token happy path

- `web-server/oidc/stores.py` / authorization request、authorization code、opaque access tokenを
  auth所有Redisの専用prefixへ保存するStoreを追加した。raw code/token/handleはkeyにせずSHA-256 digestを使う。
  codeはclient_id・redirect_uri・PKCE S256を検証してから、WATCH/MULTIでcode削除とaccess token作成を行う。
- `GET /oauth/authorize` / 重複・欠落、client status、redirect完全一致、response_type、scope、
  state/nonce、PKCE S256を検証する。未登録redirectへはredirectせず、登録済みredirectへの標準errorには
  stateとissを付ける。未ログイン要求はbrowser_context digestにbindした専用Storeへ退避する。
- `GET /signin` と `POST /v1/users/signin` / request_handleを使うOIDC signin再開を追加した。
  認証前SessionのCSRF token、Origin、Fetch Metadataを検証し、Session.start時はbrowser_context_idを引き継ぐ。
- `POST /oauth/token` / application/x-www-form-urlencoded、HTTP Basic、authorization_code grant、
  redirect、43–128文字code_verifier、PKCE、User status、auth_generationを検証する。成功時だけcodeを消費し、
  RS256 ID Tokenとopaque access tokenをno-store応答で返す。
- コーディング規約照合 / 長いhandlerを検証・client認証・Store・CSRF・署名の小関数/モジュールへ分割し、
  `digest`/`decode`等の曖昧名を`sha256_hex`/`decode_json_record`等へ改名した。標準endpointだけは
  auth/CLAUDE.mdの例外どおりlibcommon response wrapperと言語二重routeを適用していない。
- `tests/test_oidc_authorization.py` / ログイン済みhappy path、signin再開、code一回消費、wrong verifier後の
  再試行、CSRF/Origin、重複param、未登録redirect、登録済みredirectへのerrorを6テストで固定した。
  A-3後のauth pytestは59件collect、51 passed / 8 skipped / 1既存warning。

## Auth A-4 OIDC UserInfo

- `GET|POST /oauth/userinfo` / Authorization Bearerのopaque access tokenをSHA-256 digest keyから解決し、
  Userの存在、active状態、token発行時と現在のauth_generation一致を利用時ごとに検証する。
- UserInfoは常にsubを返し、token scopeにemailがある場合だけemailと
  `is_primary_email_verified()` の導出値を返す。ID Token、legacy protocol_version、billingは混在させない。
- invalid/missing Bearer tokenは401 `invalid_token` と `WWW-Authenticate: Bearer error="invalid_token"`、
  成功応答はno-storeとした。
- `tests/test_oidc_userinfo.py` / GET/POST、email scope、openid-only、generation失効、suspended User、
  Bearer形式異常を8テストで固定した。A-4後のauth pytestは67件collect、59 passed / 8 skipped /
  1既存warning。

## Auth A-5 signup verification / password reset

- `web-server/account_challenges.py` / signup・password_resetのemail challengeを専用collectionへ保存する。
  raw codeは32-byte相当の乱数で、DBにはSHA-256 hashだけを保存する。用途+宛先ごとに最新1件、TTL index、
  誤入力5回上限、正解時はfind_one_and_deleteで一回だけ消費する。
- `web-server/challenge_email.py` / 標準ライブラリsmtplibの小さいadapterを追加した。codeをHTTP応答・URL・
  logへ出さない。production系でSMTP host未設定ならfail loudly、development/testは外部送信しない。
  import時に実メール送信とprintを行う既存libcommon/sendmail.pyは使用していない。
- `POST /v1/users/verify` / suspended_emailのsignup challenge成功時だけemailを確認済みへ昇格し、
  VerifiedEmailへmethod/verified_atを保存する。codeは再利用不可。
- `POST /v1/password-reset/request` / 登録済み・未登録emailでstatus/bodyを同一にして列挙を防ぐ。
  `POST /v1/password-reset/complete` / code成功時にArgon2id再hash、auth_generation増加、
  `Session.revoke_all(str(user.id))`で中央Sessionを全失効する。
- `tests/test_account_challenges.py` / code非露出・一回消費・試行上限・列挙耐性・password/generation/session
  失効を4テストで固定した。A-5後のauth pytestは71件collect、63 passed / 8 skipped / 1既存warning。

## Auth A-6 revocation outbox / logout

- `web-server/revocation.py` / password resetとglobal logoutを`revoke_user`へ統合した。1回の処理で
  auth_generation増加、`Session.revoke_all(str(user.id))`、ConnectedServiceごとのMongoDB outbox作成を行う。
- revocation payloadはissuer/subject/auth_generation/reason/revocation_id/issued_at。client_secretや
  ID Token署名鍵を流用せず、AuthServiceのrevoke_webhook_secretでcanonical method/path/bodyをHMAC-SHA256署名する。
- 配送はtimeout=(3,10)、TLS検証既定、redirect拒否。2xxだけ成功とし、失敗時はsecretや応答本文を保存せず
  例外型だけをlast_errorへ保存する。outboxはpending→processingを原子的claimし、worker停止で残ったprocessingは
  5分後に再claimする。`process_revocations.py`を決定論的retry worker入口として追加した。
- `POST /oauth/logout` / Originを検証し、既定globalは共通失効処理、`logout_type=auth`は
  `Session.clear_current()`だけを実行する。未知のlogout typeとcross-originを拒否する。
- `tests/test_revocation.py` / generation・中央Session・outbox、HMAC、配送成功/timeout/3xx、stale claim、
  auth-only/global/cross-origin logoutを7テストで固定した。A-6後のauth pytestは78件collect、
  70 passed / 8 skipped / 1既存warning。

## Auth A-7 payment billing projection push

- `POST /v1[/<lang>]/internal/service-entitlements` / 通常account API規約の二重言語route、
  language_wrapper、JSON/required field decorators、libcommon response wrapperで実装した。
- payment専用の32byte以上HMAC secretでcanonical method/path/bodyをSHA-256署名し、未署名・改ざんを401拒否する。
  production系は環境変数`PAYMENT_PROJECTION_WEBHOOK_SECRET`が無ければ起動時にfail loudlyする。
- 署名後もsubject Userの存在、active AuthService、timezone-aware source timestamp、billing status schemaを検証する。
  auth自身から状態遷移を作る経路はなく、保存は`ServiceEntitlement.apply_projection()`だけを通す。
- 同一payment_event_idは同内容なら冪等、内容衝突なら400、古いsource timestampは200 applied=falseで破棄し、
  新しい投影を上書きしない。entitlement不在時のアクセス可否はこのendpointでは判断しない。
- `tests/test_entitlements_endpoint.py` / 正常適用・再送・署名なし/改ざん・古いevent・event ID衝突・
  naive timestamp・unknown subject/client・invalid statusを5テストで固定した。A-7後のauth pytestは
  83件collect、75 passed / 8 skipped / 1既存warning。

## Auth A-8 signing key rotation

- `web-server/rotate_keys.py` / `prepare`、`activate`、`retire` の3 phaseを持つ決定論的コマンドを追加した。
  prepareでnext鍵をJWKSへ先行公開し、設定済みoverlap後にactiveを切替、さらにoverlap後に旧鍵をretiredへ
  移してJWKSから除外する。各phaseは再実行可能で、待機不足は`RotationNotReadyError`として明示的に停止する。
- RSA鍵生成を`oidc/keys.py`へ分離し、seedとrotationで同じ実装を共有した。署名は常にactive鍵だけ、JWKSは
  active/next/retiringを公開する既存責務を維持している。
- SigningKeyへ`status_changed_at`を追加した。既存documentにはfieldが無いためdefaultで読込時刻を補わず、
  `created_at`へfallbackする。これにより既存鍵の公開済み時間を誤ってリセットしない。
- activeに加えてnextもpartial unique indexで1件に制約し、重複スケジューラ実行時の`NotUniqueError`を既存nextの
  取得へ回収する。プロセス内の先行確認だけに依存せず、prepareを並行実行してもnext鍵を増殖させない。
- `tests/test_key_rotation.py` / prepare冪等性と先行公開、overlap前の切替拒否、active署名鍵切替、2回目overlap前の
  retire拒否とJWKS除外、切替途中からの再開、旧document互換を5テストで固定した。A-8後のauth pytestは
  88件collect、80 passed / 8 skipped / 1既存warning。compileallとpip checkも成功した。

## Auth A-9 auth-spec contract / negative tests

- `tests/test_conventions.py` / 旧PROTOCOL v1を強制していた7件のskipを削除し、OIDC標準endpointの単一路線、
  account JSON APIの共通decorator積層、token endpointのform contract、標準wire名とerror shape、ID Tokenと
  UserInfoのclaim責務分離、refresh token不採用を静的に固定する7件へ置換した。
- `tests/test_oidc_authorization.py` / 必須parameter欠落、許可外scope、同一browser contextでの2 transaction、
  別browser contextからのresume拒否時にtransactionを消さないこと、auth_generation変更後の旧code拒否、
  同一codeの並行交換で成功が1件だけになることを追加した。
- `tests/test_key_rotation.py` / overlap中は旧鍵tokenと新鍵tokenの署名を両方検証でき、retire後は旧kidがJWKSから
  消えることまで固定した。A-9後のauth pytestは91件collect、90 passed / 1 skipped / 1既存warning。
  残るskipは`AUTH_A1_REAL_MONGO_URI`でloopback実Mongoを明示した場合だけ走るintegration testであり、旧仕様の
  保留テストは残っていない。compileallとpip checkも成功した。
- ID Token verifierのwrong iss/aud/nonce/azp、UserInfo sub照合、ServicePrincipal並行作成、失効webhook受信側の
  冪等性、token HTTP client timeout/信頼済みURLはサービス所有のC計画で実装する。auth server所有のnegative
  caseだけをA-9へ置き、所有境界を越えて参照client実装を先取りしていない。

## Auth A 最終仕様監査の補正

- `03_DATA_AND_INFRA.md`のpassword reset終端に対して不足していた完了通知と監査記録を追加した。
  `SecurityAuditEvent`はevent type・公開subject・時刻だけを持ち、password/codeを保存しない。保存済みrecordの
  再saveを拒否するappend-onlyモデルとし、password更新→共通失効→監査記録→完了通知の順をテストで固定した。
- challenge codeを含む確認メールと、codeを一切含まないsecurity notificationを別関数へ分けた。SMTP資格情報は
  従来どおりConfigからだけ読み、response・log・監査recordへ流さない。
- OIDC authorization request/code/access tokenのRedis接続を旧v1用`SSO_REDIS_DB_NUMBER`から中央Sessionと同じ
  `REDIS_SESSION_DB_NUMBER`へ変更した。各recordは既存の専用prefixで分離され、Redis DB番号を論理分離境界に
  しないauth-specの設計へ一致した。旧v1 blueprint用DB設定は互換経路が登録中のため変更していない。
- 補正後もauth pytestは91件collect、90 passed / 1 opt-in skipped / 1既存warning。compileallとpip checkも成功。

## Auth L/A Session security hotfix v2.2.1

- v2.2.0 は `RedisSessionInterface(prefix='auth_session:')` が認証済み Session 本体を
  `auth_session:{sid}` へ保存する一方、`Session.revoke_all()` が固定 `session:{sid}` を削除していた。
  実 Cookie を持つ2 client で global logout 後も別 client が認可を継続することを Red として固定した。
- canonical libcommon v2.2.1 は `Session.configure(..., prefix=...)` と Interface の prefix を一致させ、
  不一致時は起動を拒否する。Redis mutation 失敗は `start/clear_current/revoke_all` から再送出し、
  Cookie の name/path/domain/Secure/HttpOnly/SameSite を Flask config から Set-Cookie と削除 Cookie へ反映する。
- auth は `Config.REDIS_SESSION_KEY_PREFIX = 'auth_session:'` を唯一の設定源とし、main.py の両 Session API と
  seed reset が同じ値を使う。静的規約テストでも main.py の2箇所への注入を固定した。
- 正規 `scripts/bake.sh` の一時 bake と `auth/web-server/libcommon` は byte identical。VERSION 保存値と
  VERSION 除外後の実 tree hash はともに
  `c49c15a98ef29865f3aaa6eb7663831228df68c78997c73b528d0fda2ef69b89`。
- `tests/test_session_security.py` は実 signin の Set-Cookie 属性と、2 client の認証済み状態 → global logout →
  第2 client が signin へ戻る HTTP round trip を固定した。auth 全ゲートは92 passed / 1 opt-in skipped /
  1既存warning、compileall成功、pip checkはbroken requirementsなし。

## Security follow-up: revoke と signin の同時実行

- Security exception 該当。現行 `Session.start()` と `revoke_all()` は複数 Redis command で構成されるため、
  revoke が sid 集合を読んだ後に signin が追加される競合は逐次2 client hotfixとは別に残る。
  解消には Session registry の原子化だけでなく、password reset/global logout と signin の
  `auth_generation` 協調を含む L/A 境界の設計が必要。C 計画には持ち込まず、別の security 判断対象とする。
