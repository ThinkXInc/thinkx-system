# 03 — データモデル・Redis 設計・インフラ構成

`01` のコードで参照されるデータ構造・保存先・サーバー配置を定義する。

---

## データモデル（MongoDB, auth 側）

```python
# auth/models/data/user.py
class User(MongoModel):
    # signup で確認前 User を作るため email は optional。確認済みメールは email、確認待ちは suspended_email。§04 D-15
    email           = StringField(unique=True, sparse=True)   # 確認済みメール（確認前は None）
    suspended_email = StringField()          # 確認待ちメール
    verified_emails = ListField()            # [{email, method, verified_at}, ...]
    verified_phone_numbers = ListField()     # 将来の SMS 用
    password        = StringField()          # フィールド名は password。実体は Argon2id ハッシュ。§04 D-11
    google_id       = StringField()
    picture_url     = StringField()          # 実体が URL なので picture_url
    auth_generation = IntField(default=0)    # 失効の世代。§02-generation
    last_auth_time  = DateTimeField()        # ID Token の auth_time 用
    status          = StringField(default='active')   # active | suspended 等
    # 外部 identity は ObjectId と分離した専用フィールド。§02-sub, §04 D-23
    subject_id      = StringField(required=True, unique=True, default=create_random_subject_id)

    def check_password(self, raw): return argon2_verify(self.password, raw)
    def is_active(self): return self.status == 'active'
    def subject(self): return self.subject_id     # sub は subject_id（ObjectId でない）

    # 確認済み判定は保存した bool ではなくメソッドで導出。§04 D-09
    def is_primary_email_verified(self):
        return bool(self.email) and self.email in [e['email'] for e in self.verified_emails]
    def is_email_verified(self, email):
        return email in [e['email'] for e in self.verified_emails]
```

**email_verified を永続保存しない理由（D-09）:** `email` が存在すること自体が「確認済み」を意味する設計。
別途 `email_verified=true` を保存すると同じ事実の二重保持になり、食い違い時に「どちらを信用するか」の新問題が
生じる。Google トークンの `email_verified` クレームは外部入力として検査するが User には保存しない（別物）。

**subject_id を ObjectId と分ける理由（D-23）:** 一度公開した sub は永久に変えられない。ObjectId を露出させると
内部 DB 構造が外部 identity に漏れる。独立の `subject_id` を持てば、将来 pairwise subject を後付けしても内部
identity を変えずに済む。

```python
# auth/models/data/auth_service.py   （OAuth の Client）
class AuthService(MongoModel):
    client_id      = StringField(required=True, unique=True)   # 'quantz'
    secret_digest  = StringField(required=True)   # SHA-256。§04 D-12
    redirect_uris  = ListField()                  # 完全一致ホワイトリスト
    allowed_scopes = ListField()                  # 例 ['openid','email']。§04 D-22
    trusted_first_party = BooleanField(default=False)  # true なら同意画面を省略可（scope 検証は別途）
    subject_type   = StringField(default='public')     # public | (将来)pairwise。§04 D-23
    id_token_signing_alg = StringField(default='RS256')
    status         = StringField(default='active')     # active | disabled
    revoke_url     = StringField()                # 失効通知先
    revoke_webhook_secret = StringField()         # 失効通知用（client_secret とも署名鍵とも別）。§04 D-12,D-17

    @classmethod
    def find(cls, client_id): return cls.objects(client_id=client_id).first()
    def verify_secret(self, raw): return hmac.compare_digest(self.secret_digest, sha256_hex(raw))
    def valid_redirect(self, uri): return uri in self.redirect_uris   # in。startswith 禁止

# 初版 quantz の登録例
# { "client_id":"quantz", "allowed_scopes":["openid","email"],
#   "trusted_first_party":true, "subject_type":"public", "id_token_signing_alg":"RS256",
#   "status":"active" }
```

```python
# quantz/models/data/service_principal.py   （各サービス側）
class ServicePrincipal(MongoModel):
    issuer        = StringField(required=True)
    subject       = StringField(required=True)    # auth の sub（= subject_id）
    local_user_id = StringField(required=True)    # サービス内 user_id
    meta = {'indexes': [{'fields': ['issuer', 'subject'], 'unique': True}]}  # ★複合ユニーク。§04 D-13

    @classmethod
    def find_or_create(cls, issuer, subject):
        p = cls.objects(issuer=issuer, subject=subject).first()
        if p: return p
        # 初版は新規のみ・移行なし（§04 D-13）。並行初回 callback の二重作成を atomic upsert / duplicate-key で防ぐ
        local = create_local_service_user()
        try:
            return cls(issuer=issuer, subject=subject, local_user_id=str(local.id)).save()
        except DuplicateKeyError:
            delete_local_service_user(local)
            return cls.objects(issuer=issuer, subject=subject).first()
```

**初版は「新規のみ・移行なし」（D-13）:** 既存サービスユーザーの移行・リンク機構は初版スコープ外。突合キーに
メールを使ってはいけない（変わりうる・乗っ取りリスク）。ただし複合ユニークインデックスと二重作成防止は、移行の
有無と無関係に必須。

### VerificationChallenge / password reset

確認済み情報は User に永続保存。確認コード・期限・試行回数などの一時状態は専用 `VerificationChallenge`
（`purpose` ∈ {signup, email_change, phone_verification, password_reset}、`channel` ∈ {email, sms}、
`code_hash`, `destination`, `expires_at`, `attempts`）に分離。成功時はレコード削除で一回消費。理由: 用途別
コードを User 単一フィールドに置くと新コード発行時に別用途を上書きし、複数確認の同時進行を表現できない。

password reset 要件: 有効期限初期値 1 時間（設定可能）/ 登録済み・未登録メールで外部レスポンス同一
（account enumeration 対策、内部では存在時のみ送信）/ 成功時に challenge 削除 → password 更新 →
`auth_generation++` → 中央 Session 全失効 → 各サービスへ失効通知 → 完了メール → 監査記録。

---

## Redis 設計

### キー Prefix による論理分離（DB 番号は使わない）

Redis Cluster では DB0 しか使えず `SELECT` が無効なため、DB 番号を分離境界にすると将来のクラスタ化で壊れる。
論理分離は **キー Prefix** で行う（§04 D-10）。

```
auth 所有 Redis:
  auth:session:*                中央 Session（既存 Session クラス）
  oidc:authorization_request:*  signin を挟む間の認可要求（request_handle で参照）。§01 ②
  oauth:code:*                  authorization code（TTL 60秒）
  oauth:at:*                    access token（TTL 1時間）
  auth:rate_limit:*             レート制限

各サービス（quantz 等）所有 Redis:
  quantz:session:*              ローカル Session（既存 Session クラス）
  oidc:client_transaction:*     client transaction（code_verifier, nonce, return_to, expected_issuer, status）
```

### 所有境界はインスタンスで分ける

同一サービス内の用途（session / code / token / request）は同じインスタンスで Prefix 分けで足りる。auth と
各サービスは所有者が違うため、production では別インスタンス（最低でも別接続 credential + 別 ACL user）に分ける。

### Session 実装は「同じクラス・別インスタンス」

```python
auth_sessions = RedisSessionStore(redis=auth_redis,
    cookie_name='auth_session_id', key_prefix='auth:session:')
quantz_sessions = RedisSessionStore(redis=quantz_redis,
    cookie_name='quantz_session_id', key_prefix='quantz:session:')
```

コードは共通、インスタンスと所有データは別。

### code record / access token record

```
oauth:code:<sha256(raw_code)>          TTL 60秒
  subject          (= subject_id)
  client_id
  redirect_uri
  code_challenge
  nonce
  scope
  auth_generation

oauth:at:<sha256(raw_token)>           TTL 1時間
  subject
  client_id
  scope
  auth_generation
  issued_at
```

raw 値でなく **SHA-256 digest を key に**する（漏洩時に生トークンを復元させにくくする）。

### 「検証してから削除」の原子性（§04 D-06, D-26）

`begin_consume`（読む→client_id/redirect_uri/PKCE を検証、まだ削除しない）→ Mongo で User・generation 確認
→ ID Token 署名 → `MULTI`{code 削除＋access token 作成}→`EXEC`。`getdel` で先に消してはならない（漏れた
code で他 client 向け code を消す DoS を防ぐ）。並行消費は `WATCH`/`MULTI` の楽観ロックで 1 つだけ通す
（Lua/Function は性能問題が出てから。契約テストで追いにくいため）。Mongo と Redis をまたぐ完全 transaction は
不可なので、途中 crash 時は「ログインをやり直す」で回復する（token request に自動 retry を付けない）。

### Redis に置くもの・置かないもの

Redis: 中央 Session / ローカル Session / authorization code / access token / authorization request /
client transaction / レート制限。**バックアップ対象外**（再起動でログイン状態が消えることを許容）。

MongoDB: User / 確認済み identity / VerificationChallenge / AuthService / ServicePrincipal / 失効 outbox /
監査記録 / 署名鍵。**MongoDB だけをバックアップ対象**にする。

---

## cookie 設定（auth・各サービス共通の最低要件）

```python
app.config.update(
    SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
```

- **Domain 指定なし**（host-only）。`Domain=.smallservice.com` の親ドメイン共有は使わない。
- auth とサービスで **cookie 名を分ける**（`auth_session_id` / `quantz_session_id`）。
- callback 処理後は **code を含まない URL へ直ちに redirect** し、callback ページに analytics /
  third-party スクリプトを置かない。

---

## サーバー構成（インフラ）

### production（最小構成）

```
production LB
├─ auth app EC2
├─ MongoDB EC2                （バックアップ対象）
└─ Redis EC2 × 2             （auth 所有 / 各サービス所有。バックアップ対象外）
```

計 **MongoDB 1 + Redis 2**。**OIDC 準拠・JWKS 公開にしてもこの構成は変わらない。** JWKS / metadata は
read-only エンドポイントの追加であり、サーバー・DB・プロセスを増やさない。増えるのは署名鍵ペアのみ。

t3 サイズは起動直前に staging 実測と最新料金で確定（MongoDB は t3.small 目安、Redis は t3.micro から）。
production はまだ apply せず Terraform で構成だけ用意する。

### staging（1 台集約）

```
staging EC2 1台
├─ auth app container
├─ MongoDB container
├─ Redis container（auth 所有相当）
└─ Redis container（サービス所有相当）
```

論理接続先を最初から分ける（`MONGODB_HOST`, `REDIS_AUTH_HOST`, `REDIS_SERVICE_HOST`）。production では
ホスト設定を変えるだけ。開発運用は `05` を参照（staging に常駐エージェントを置かず、ローカル修正→デプロイ→
テストコマンド一発の構成）。

### staging / production 分離の原則（無条件）

**本番の署名鍵・client_secret・ユーザーデータを staging と共有しない。** staging の署名鍵・client_secret は
本番と別物、staging のユーザーはテストデータのみ。これにより staging 環境が侵害されても、漏れるのは
「捨ててよい staging 用の秘密」に限られる。

---

## 鍵管理と JWKS（初版から公開。§04 D-A）

OIDC が追加するインフラ要素は **署名鍵ペア**と **read-only エンドポイント 2 本**のみ。DB もサーバーも増やさない。

### エンドポイント（初版から）

```
GET /.well-known/openid-configuration   issuer, authorization/token/userinfo/jwks の各 URL, 対応 alg 等
GET /oauth/jwks                          公開鍵 JWK Set（status != retired の鍵を kid 付きで列挙）
```

各サービスは ID Token 検証時、ヘッダの `kid` に対応する公開鍵を JWKS から取得する（短期キャッシュ可）。
`kid` は ID Token ヘッダに必ず入れる（`01` ⑦）。

### 署名鍵の保持

```
MongoDB: signing_keys コレクション
  kid, public_key, private_key, status(active|next|retiring|retired), created_at
```

JWKS は `status != retired` の公開鍵を返す。auth は `status=active` の鍵で署名する。

### 鍵ローテーション（決定論的スクリプト＋スケジューラで自動化。Claude Code は使わない。§04 D-A）

無停止で回るのは、切替期間中 JWKS に新旧両方の公開鍵が並び、検証側が `kid` で正しい鍵を引けるため。

```
1. 新鍵ペア生成、新 kid、status=next で保存         （JWKS に公開鍵が増える）
2. 既存トークン TTL（最大 access token 1時間）を超える待機
3. active を新鍵へ切替（旧鍵 status=retiring）      （署名だけ新鍵に）
4. さらに TTL を超える待機
5. 旧鍵 status=retired                              （JWKS から消える）
```

判断を要する分岐が無いので、定期実行（例 90 日）にできる。漏洩時は同じスクリプトを手動トリガー。
日常の手作業はゼロ。「運用が増える」の実体は「ローテーションスクリプト 1 本を書く」であり、書けば以後は自動。

---

## 識別子・環境変数

```
# auth サーバー側
AUTH_ID=smallservice
AUTH_PUBLIC_BASE_URL=https://auth.smallservice.com   （= ID Token の iss、metadata の issuer）

# auth を利用するサービス側
SERVICE_ID=quantz            （wire 上は client_id）
CLIENT_SECRET=...            （token endpoint 用。§02-client_secret）
AUTH_JWKS_URL=https://auth.smallservice.com/oauth/jwks   （ID Token 検証の公開鍵取得元）

# Redis 接続（staging は同一ホスト、production は分離）
MONGODB_HOST / REDIS_AUTH_HOST / REDIS_SERVICE_HOST
PASSWORD_RESET_EXPIRATION_SECONDS=3600
```

`AUTH_ID` は auth 自身、`SERVICE_ID`（`client_id`）は接続サービスの識別子。混同しないよう名前を分ける。
