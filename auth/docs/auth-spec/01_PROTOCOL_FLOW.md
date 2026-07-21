# 01 — 認証フローの完全な手続き

ログイン開始からログイン成立までの全手続きを、実際のコードに近い形で示す。
各値が「なぜ必要か」は `02` を参照。ステップ番号は両ファイルで対応する。
コードは実装イメージであり、メソッド名の細部は既存 libcommon の実際の API に合わせること。
`★` は OAuth/OIDC/PKCE により追加された部分を示す。

---

## 登場するサーバーと Redis

```
ブラウザ
quantz web server        （Python / Flask）
quantz 所有 Redis        （quantz:session:* , oidc:client_transaction:*）
auth web server          （Python / Flask）
auth 所有 Redis          （auth:session:* , oidc:authorization_request:* , oauth:code:* , oauth:at:*）
auth MongoDB             （User, AuthService, ServicePrincipal, 監査・失効 outbox, 署名鍵）
```

Session クラスは auth・quantz で **同一実装を別インスタンス**（別 Redis・別 cookie 名）として使う。
新しい Session の種類を増やすのではない。詳細は `03`。

### 重要な前提: browser_context_id と Session ローテーション

`Session.start()` は既存 Session ID を破棄し新 ID を発行する（Session fixation 対策）。
一方、認証フローは「同じブラウザが始めた認証か」をローテーションをまたいで追う必要がある。
そこで **Session ID とは別に `browser_context_id`** を持つ。これは cookie/URL には出さず、Session の
中身として保持し、`Session.start()` 時に新 Session へ引き継ぐ。transaction には Session ID ではなく
`browser_context_id` の digest を bind する。理由は `02`（複数タブ）、`04` D-21。

```python
Session.browser_context_id()           # 無ければ生成して現 Session に保存
Session.start(user_id, browser_context_id=<引き継ぐ値>)   # 認証前の値を新 Session へ渡す
```

---

## 全体像（誰が誰に送るか）

```
① browser → quantz    GET /auth/signin              → 302
② browser → auth      GET /oauth/authorize          → 未ログインなら signin へ（request_handle 発行）
③ browser → auth      GET /signin?request_handle=.. → signin 画面（CSRF token 付き）
                       POST /v1/users/signin         → 中央 Session 開始、認可処理を再開
④ browser → auth      （authorize 再開）              → 302 to quantz callback
⑤ auth（内部で code 発行）
⑥ browser → quantz    GET /auth/callback            → claim（検証）→ ⑦⑧ → complete
⑦ quantz  → auth      POST /oauth/token（サーバー間） → {id_token, access_token}
⑧ quantz（内部で ID Token 検証）                      → ローカル Session 開始
⑨ browser → quantz    GET /workspace                → 既存ローカル Session で判定
```

②③④は「auth に未ログインの場合」の手順。既にログイン済みなら ② から ⑤ へ直行する。

---

## ① ブラウザ → quantz `/auth/signin`（ログイン開始）

```
GET https://quantz.example/auth/signin
Cookie: quantz_session_id=...    （未ログインの匿名ローカル Session）
```

```python
# quantz web server
def auth_signin():
    txn_id         = secrets.token_urlsafe(32)      # wire 名 state。§02-state
    code_verifier  = secrets.token_urlsafe(64)      # ★PKCE。§02-pkce
    code_challenge = sha256_b64url(code_verifier)   # ★S256
    nonce          = secrets.token_urlsafe(32)      # ★OIDC。§02-nonce

    # client transaction を専用 Redis Store へ保存（Session 単一フィールドに入れない＝複数タブ対応）。
    # bind は Session ID ではなく browser_context_id の digest（ローテーションをまたぐ）。§02, §04 D-21
    quantz_txn_store.create(txn_id, {
        'browser_context_hash': sha256_hex(Session.browser_context_id()),
        'return_to': '/workspace',
        'code_verifier': code_verifier,              # ★⑦で使用
        'nonce': nonce,                              # ★⑧で照合
        'expected_issuer': 'https://auth.smallservice.com',  # ★⑥で照合。§02-iss
        'status': 'pending',                         # ★pending→processing→(削除)。§04 D-20
    })

    # URL は必ず urlencode で構築（文字列連結禁止）。§04（URL 構築）
    return redirect(build_url('https://auth.smallservice.com/oauth/authorize', {
        'response_type': 'code',                     # ★標準
        'client_id':     'quantz',                   # ★標準名
        'redirect_uri':  'https://quantz.example/auth/callback',
        'scope':         'openid email',             # ★openid で OIDC になる
        'state':         txn_id,
        'nonce':         nonce,                      # ★
        'code_challenge':        code_challenge,     # ★
        'code_challenge_method': 'S256',             # ★常に S256（後述の検証で強制）
    }))
```

**返り:** 302 で ② へ。

---

## ② ブラウザ → auth `/oauth/authorize`

```
GET https://auth.smallservice.com/oauth/authorize?response_type=code&client_id=quantz&...
Cookie: auth_session_id=...   （auth 中央 Session。quantz の cookie は別ドメインなので付かない）
```

```python
# auth web server
def authorize():
    # --- パラメータ検証（存在・型・重複・値の意味）。§02, §04 D-22 ---
    p = require_single_params(request.args, [   # 重複パラメータは invalid_request
        'response_type','client_id','redirect_uri','scope',
        'state','nonce','code_challenge','code_challenge_method'])

    service = AuthService.find(p['client_id'])
    if not service or service.status != 'active':
        return auth_error_page('unauthorized_client')
    if p['response_type'] != 'code':
        return auth_error_page('unsupported_response_type')
    if p['code_challenge_method'] != 'S256':          # ★downgrade を許さない（plain 拒否）
        return auth_error_page('invalid_request')
    if 'openid' not in p['scope'].split():            # ★OIDC には openid 必須
        return auth_error_page('invalid_scope')
    if not set(p['scope'].split()) <= set(service.allowed_scopes):  # 要求 scope は許可範囲内
        return auth_error_page('invalid_scope')
    # state/nonce/code_challenge の長さ・文字種も検証（省略記載）

    # redirect_uri は完全一致（startswith 禁止）。不正時は error redirect せず自前ページ。§02-redirect
    if not service.valid_redirect(p['redirect_uri']):
        return auth_error_page('invalid_redirect_uri')
    # ここまで通れば、以降のエラーは redirect_uri へ返してよい（iss を必ず添える。§02-iss, §04 D-22）

    # auth 中央 Session（既存 Session）でログイン済みか
    user_id = Session.user_id()
    if not user_id:
        # 認可要求を「専用 Store」へ保存し、signin 画面には request_handle だけ渡す。
        # Session 単一フィールドに入れない（return_to バグ再発 & 複数タブ）。§04 D-19
        request_handle = auth_request_store.create({
            'client_id': p['client_id'], 'redirect_uri': p['redirect_uri'],
            'state': p['state'], 'nonce': p['nonce'], 'scope': p['scope'],
            'code_challenge': p['code_challenge'],
            'browser_context_hash': sha256_hex(Session.browser_context_id()),
        })
        return redirect(f'/signin?request_handle={request_handle}')   # → ③
    return _issue_code_and_redirect(user_id, p)   # → ⑤
```

---

## ③ ブラウザ → auth `/signin` と `/v1/users/signin`（パスワード認証）

```
GET  /signin?request_handle=...   → signin 画面（既存 simplicity UI）。CSRF token を認証前 Session に発行
POST /v1/users/signin
     { "email":"...", "password":"...", "request_handle":"...", "csrf_token":"..." }
```

```python
# auth web server
def users_signin():
    # ★login CSRF 対策: 認証前 Session の CSRF token と照合（+ Origin/Fetch Metadata 検証）。§02, §04 D-25
    if not verify_csrf(request):
        return error_response('invalid_request', 400)

    ar = auth_request_store.get(request.json['request_handle'])   # 認可要求を先に取得
    if not ar:
        return error_response('invalid_request', 400)

    user = User.objects(email=request.json['email']).first()
    if not user or not user.check_password(request.json['password']):   # Argon2id
        return error_response('invalid_credentials', 401)
    if not user.is_primary_email_verified():
        return error_response('email_unverified', 403)

    # ★Session.start の「前に」browser_context を確保して引き継ぐ。§04 D-05, D-21
    bctx = Session.browser_context_id()
    Session.start(str(user.id), browser_context_id=bctx)   # 中央 Session を開始（ID ローテーション）

    # 認可要求は Session ではなく Store から取得済みなので、ローテーションの影響を受けない
    return json_response({'next': build_authorize_resume_url(ar)})   # → ④
```

`Session.start()` で新 `auth_session_id` に張り替わる。認可要求は Store 側にあるため失われない。

---

## ④ ブラウザ → auth（authorize 再開・ログイン済み）→ ⑤

`request_handle` から認可要求を復元し、`_issue_code_and_redirect` へ進む。

---

## ⑤ auth：code 発行 → ブラウザを quantz へ戻す

```python
# auth web server
def _issue_code_and_redirect(user_id, p):
    user = User.objects(id=user_id).first()
    code = sso_store.issue_code(
        subject=user.subject_id,              # ★sub = 独立 subject_id（ObjectId でない）。§02-sub, §04 D-23
        client_id=p['client_id'],
        redirect_uri=p['redirect_uri'],
        code_challenge=p['code_challenge'],   # ★PKCE: code に challenge を結ぶ
        nonce=p['nonce'],
        scope=p['scope'],
        auth_generation=user.auth_generation, # ★失効の世代。§02-generation
    )                                          # code record は §03 参照、TTL 60秒、digest を key に
    return redirect(build_url(p['redirect_uri'], {
        'code':  code,
        'state': p['state'],
        'iss':   'https://auth.smallservice.com',   # ★mix-up 対策（RFC 9207）。§02-iss
    }))
```

**返り:** `302 Location: https://quantz.example/auth/callback?code=...&state=...&iss=...`

---

## ⑥ ブラウザ → quantz `/auth/callback`

```
GET https://quantz.example/auth/callback?code=...&state=...&iss=...
Cookie: quantz_session_id=...   （① で作った匿名ローカル Session）
```

```python
# quantz web server
def auth_callback():
    args = require_single_params(request.args, ['code', 'state', 'iss'])

    # --- transaction を「削除せず」claim する（検証を先に、原子的に pending→processing）。§04 D-20 ---
    try:
        txn = quantz_txn_store.claim_for_callback(
            state=args['state'],
            browser_context_hash=sha256_hex(Session.browser_context_id()),  # ブラウザ照合。§02-state
            returned_issuer=args['iss'],                                     # iss 照合。§02-iss
        )
    except TransactionInvalid:
        return reject()   # 別ブラウザの state / wrong iss / 既 processing では transaction を壊さない

    try:
        token_response = AuthClient.exchange(                # → ⑦（サーバー間）
            code=args['code'],
            redirect_uri='https://quantz.example/auth/callback',
            code_verifier=txn['code_verifier'],              # ★PKCE
            expected_issuer=txn['expected_issuer'])          # token endpoint は信頼済み設定から引く。§04 D-24
        claims = IDTokenVerifier.verify(                     # → ⑧
            token_response['id_token'], expected_nonce=txn['nonce'])
    except AuthError:
        quantz_txn_store.complete(args['state'], outcome='failed')   # 恒久失敗 → 削除
        return reject()
    except TransientError:
        quantz_txn_store.release(args['state'])   # 一時失敗 → lock 解除し再試行可能に
        return retry_or_reject()

    # identity mapping: (iss, sub) → ローカル user_id。並行初回は atomic upsert。§03, §04 D-13
    principal = ServicePrincipal.find_or_create(issuer=claims['iss'], subject=claims['sub'])

    # return_to は Session.start の「前に」ローカル変数へ。§04 D-05
    return_to = safe_return_to(txn['return_to'])   # 相対パスのみ。§02-redirect
    bctx      = Session.browser_context_id()

    Session.start(principal.local_user_id, browser_context_id=bctx)   # ★合流点（既存 Session）
    quantz_txn_store.complete(args['state'], outcome='completed')     # 成功 → 削除
    return redirect(return_to)
```

---

## ⑦ quantz → auth `/oauth/token`（サーバー間、⑥ の内部）

ブラウザを経由しない。`client_secret` をブラウザに晒さないため。§02-client_secret

```python
# quantz web server
class AuthClient:
    @staticmethod
    def exchange(*, code, redirect_uri, code_verifier, expected_issuer):
        provider = TRUSTED_PROVIDERS[expected_issuer]     # ★iss から URL を組み立てない。§04 D-24
        resp = requests.post(provider.token_endpoint,
            auth=(CLIENT_ID, CLIENT_SECRET),              # ★HTTP Basic（標準）
            data={                                         # ★form encoding（標準）
                'grant_type':'authorization_code', 'code':code,
                'redirect_uri':redirect_uri, 'code_verifier':code_verifier},
            timeout=(3.0, 10.0), allow_redirects=False)   # ★timeout / redirect 拒否。§04 D-24
        if resp.headers.get('Content-Type','').split(';')[0] != 'application/json':
            raise AuthError('bad_response')
        if resp.status_code != 200:
            raise AuthError(resp.json().get('error', 'invalid_grant'))
        return resp.json()   # Authorization ヘッダ・code_verifier をログに残さないこと
```

```python
# auth web server
def token_endpoint():
    # client 認証（HTTP Basic、SHA-256 照合）。§04 D-12
    client_id, client_secret = parse_basic_auth(request)
    service = AuthService.find(client_id)
    if not service or not service.verify_secret(client_secret):
        return token_error('invalid_client', 401)
    if request.form.get('grant_type') != 'authorization_code':
        return token_error('unsupported_grant_type', 400)

    # --- code を「検証してから削除」。client/redirect/PKCE を確認し、通れば MULTI で原子的処理。§04 D-06,D-26 ---
    #   1. Redis: code record を読み、client_id / redirect_uri / PKCE(code_verifier) を検証
    #   2. Mongo: User の存在・停止状態・auth_generation を確認
    #   3. ID Token 署名
    #   4. Redis MULTI: code 削除 ＋ access token record 作成
    #   5. EXEC 成功時だけ response を返す（途中 crash 時はログインやり直し。自動 retry 禁止）
    try:
        rec = sso_store.begin_consume(   # 1（検証のみ、まだ削除しない）
            code=request.form['code'], client_id=client_id,
            redirect_uri=request.form['redirect_uri'],
            code_verifier=request.form['code_verifier'])
    except AuthError:
        return token_error('invalid_grant', 400)   # 外部は一律 invalid_grant。詳細は内部ログ。§04 D-07

    user = User.objects(subject_id=rec['subject']).first()   # 2
    if not user or not user.is_active() or user.auth_generation != rec['auth_generation']:
        return token_error('invalid_grant', 400)

    id_token = id_token_issuer.issue(                        # 3（email 等は入れない。§02-idtoken, §04 D-08）
        subject=user.subject_id, audience=client_id,
        nonce=rec['nonce'], auth_time=user.last_auth_time)
    access_token = sso_store.finish_consume_and_issue_at(    # 4,5（MULTI）
        code=request.form['code'], subject=user.subject_id, client_id=client_id,
        scope=rec['scope'], auth_generation=user.auth_generation)

    return json_response({
        'access_token': access_token, 'token_type': 'Bearer',   # ★標準
        'expires_in': 3600, 'id_token': id_token,               # ★OIDC 本体
    }, headers={'Cache-Control': 'no-store', 'Pragma': 'no-cache'})
```

**返り（auth → quantz）:**
`{"access_token":"...", "token_type":"Bearer", "expires_in":3600, "id_token":"eyJ..."}`

---

## ⑧ quantz：ID Token 検証（⑥ の内部）

```python
# quantz web server
import jwt
class IDTokenVerifier:
    @staticmethod
    def verify(id_token, *, expected_nonce):
        header = jwt.get_unverified_header(id_token)
        signing_key = resolve_signing_key(header['kid'])   # ★kid → JWKS（or 設定）から公開鍵。§03 鍵管理
        claims = jwt.decode(
            id_token, signing_key, algorithms=['RS256'],
            audience=CLIENT_ID, issuer='https://auth.smallservice.com',
            leeway=60,
            options={'require': ['iss','sub','aud','exp','iat','nonce']})  # ★必須 claim を強制。§04 D-07b
        # 明示検証（欠落は認証失敗、内部例外を外へ出さない）
        if not isinstance(claims['sub'], str) or not claims['sub']:
            raise AuthError('invalid_id_token')
        if not hmac.compare_digest(claims['nonce'], expected_nonce):       # ★nonce 照合。§02-nonce
            raise AuthError('nonce_mismatch')
        if 'azp' in claims and claims['azp'] != CLIENT_ID:                  # 複数 aud 時の azp。§04 D-07b
            raise AuthError('invalid_azp')
        return claims
```

ID Token は認証 claim（iss/sub/aud/exp/iat/nonce/auth_time）のみ。email 等プロフィールは `/userinfo` から
取得する（§02-idtoken, §04 D-08）。ID Token の TTL は 5〜10 分で足りる（ログイン成立の瞬間だけ使う）。

---

## ⑨ 以後：quantz 通常ページ（変化なし）

```
GET https://quantz.example/workspace
Cookie: quantz_session_id=...   （⑥ で張り替えた認証済みローカル Session）
→ Session.user_id() で判定。auth へは問い合わせない。
```

変わるのはログイン成立までである。成立後の通常ページ判定は既存ローカル Session をそのまま維持する。

---

## /userinfo（ログイン後の情報再取得、access token を使う）

```python
# auth web server
def userinfo():
    token = parse_bearer(request)                       # GET/POST 両対応
    rec   = sso_store.resolve_access_token(token)       # 無ければ invalid_token
    user  = User.objects(subject_id=rec['subject']).first()
    # ★access token 利用時に必ず再検証（auth_generation を実際に効かせる）。§04 D-04b
    if not user or not user.is_active() or user.auth_generation != rec['auth_generation']:
        return userinfo_error('invalid_token', 401)
    claims = {'sub': user.subject_id}
    if 'email' in rec['scope'].split():
        claims['email'] = user.email
        claims['email_verified'] = user.is_primary_email_verified()  # 保存せず導出。§04 D-09
    return json_response(claims)
```

Client は UserInfo の `sub` が ID Token の `sub` と完全一致することを確認すること（§04 D-08）。

---

## logout（3 種。デフォルトは global）。§04 D-27

```python
# 各サービス: このサービスからログアウト
def service_logout():
    Session.revoke_all(Session.user_id()); return redirect('/')

# auth: 中央 Session だけ削除（サービス Session は残す）
def auth_logout():
    Session.clear_current()

# global logout（ログアウトボタンのデフォルト挙動）
def global_logout():
    user = current_user()
    Session.revoke_all(user.subject_id)              # auth 中央 Session を全消し
    for svc in user.connected_services():            # 各サービスへ失効通知（失効フローを再利用）
        post_revoke(svc, user, reason='global_logout')
```

UI: 「ログアウト」ボタン = global logout。「このサービスだけログアウト」は設定など奥に置き、残すが目立たせない。

---

## 失効フロー（password reset / アカウント保護 / global logout 共通）。§04 D-11b, D-17

```python
# auth web server
def revoke_user(user, reason):
    user.auth_generation += 1; user.save()   # ★code/access token を世代で一括無効化。§02-generation
    Session.revoke_all(user.subject_id)      # auth 中央 Session を全消し
    for svc in user.connected_services():
        post_revoke(svc, user, reason)        # 下記 payload。失敗は outbox で再送

def post_revoke(svc, user, reason):
    body = {
        'issuer': 'https://auth.smallservice.com',
        'subject': user.subject_id,
        'auth_generation': user.auth_generation,
        'reason': reason,
        'revocation_id': str(uuid4()),        # ★冪等性
        'issued_at': int(time.time()),        # ★replay 対策
    }
    revocation_outbox.save(body)              # ★先に Mongo outbox へ。停止中も失われない
    sig = hmac_sign(svc.revoke_webhook_secret, canonical(request_line, body))  # ★webhook 用 secret（署名鍵と別）
    send_with_retry(svc.revoke_url, body, headers={'X-Auth-Signature': sig})
```

各サービス側の受け口:

```python
# quantz web server
def sessions_revoke():
    verify_webhook_signature(request)        # 署名・timestamp 許容・issuer 確認
    if revocation_seen(request.json['revocation_id']):   # ★重複適用しない
        return ok()
    p = ServicePrincipal.find_one(issuer=request.json['issuer'], subject=request.json['subject'])
    if p:
        Session.revoke_all(p.local_user_id)  # 既存メソッド
    mark_revocation_seen(request.json['revocation_id'])
    return ok()
```

`auth_generation` は「利用時に generation を再検証する code / access token」だけを無効化する。既に
サービスへ受理されローカル Session に変換済みの過去 ID Token は無効化できない。その部分はこの失効通知が担う。

---

## 新規に書くもの・使うもの（実装チェックリスト）

**新規クラス（すべて自作、アダプタ層なし）**
- auth: `SSOStore`（code/access token、begin_consume/finish_consume）, `AuthorizationRequestStore`,
  `IDTokenIssuer`, `AuthService`, `SigningKeyStore`, `RevocationOutbox`
- quantz: `ClientTransactionStore`（create/claim_for_callback/complete/release）, `AuthClient`,
  `IDTokenVerifier`, `ServicePrincipal`

**新規ハンドラ**
- auth: `/oauth/authorize`, `/oauth/token`, `/v1/users/signin`, `/oauth/userinfo`,
  `/oauth/jwks`, `/.well-known/openid-configuration`, `/oauth/logout`, （失効の入口）
- quantz: `/auth/signin`, `/auth/callback`, `/v1/sessions/revoke`, logout（3種）

**既存のまま使うもの**
- libcommon `Session`（`start` / `user_id` / `id` / `browser_context_id` / `clear_current` /
  `revoke_all`）。`revoke_all` と `clear_current` の責務分離は要実装（§04 D-17）。
- MongoModel, RedisBase, Argon2id パスワード関数, simplicity UI

**新規ライブラリ:** JWT（PyJWT 想定、quantz で使用実績あり）のみ。

**初版でやらないもの（外部開放時に足す）**
- prompt/display/ui_locales/max_age/acr_values 等の汎用 OP 要件
- Dynamic Client Registration
- pairwise subject（`subject_id` を分離済みなので後付け可能。§04 D-23）
