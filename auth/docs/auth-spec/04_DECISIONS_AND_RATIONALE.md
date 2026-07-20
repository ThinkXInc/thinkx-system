# 04 — 設計判断の記録（採用理由・却下案）

各判断について「決定 / 理由 / 却下した案」を記録する。ここを読めば同じ論点を再議論せずに済む。
第三者レビュー（GPT Pro）を 2 回経ており、後半（D-19 以降）はそのレビューで発見された見落としの修正が中心。

---

## D-01. プロトコルは OIDC 完全準拠（opaque 独自案を却下）

**決定:** OpenID Connect Authorization Code Flow + PKCE(S256) に準拠する。
**理由:** (1) インフラコストが増えない（署名鍵と read-only エンドポイントのみ、`03`）、(2) 認証 API を将来
外部開放できる（プラットフォーマー戦略）、(3) quantz の JWT 知見の延長。
**却下:** OAuth 風独自プロトコル + opaque token のみ。標準に沿わないと外部開放できず、独自 wire は標準ツールで
認識されない。opaque token 自体は access token として構成内に残す（捨てたのは独自 wire）。
**線引き:** 初版で汎用 OP 要件（prompt/display/ui_locales/max_age/acr_values 等）や Dynamic Registration は
作らない。呼称は「静的登録 first-party confidential client 向けの OIDC Core Authorization Code Flow + PKCE
S256 実装」。conformance suite 通過を「OIDC Core 準拠」の条件とし、外部開放時の完了条件に置く（`00`, D-16）。

## D-02. Authlib 等を使わず自作（アダプタ層なし）

**決定:** OAuth/OIDC フレームワークは使わない。JWT ライブラリのみ。
**理由:** 既存 MongoEngine User / AuthService / libcommon Session / Redis を Authlib の Mixin へ翻訳する
アダプタ層のコストが、肩代わりされる処理量を上回る。「ソースコードを契約の正本にする」方針（D-14）と
フレームワークのブラックボックス化が衝突。危険な処理（PKCE の S256 照合、code 一回消費、redirect 完全一致、
compare_digest）は既知の道具で書け契約テストで固められる規模。
**再検討の余地:** 完全 OIDC 準拠の高度化や複数外部 IdP の束ね、JWKS/discovery の本格運用が必要になった時点で
Authlib 移行を再検討してよい。token endpoint の外形契約を変えなければ内部は差し替え可能。

## D-03. PKCE を初版から入れる

**決定:** PKCE(S256) を初版から実装し、全 client で必須。`plain`・challenge 無しを拒否（downgrade 防止）。
**理由:** RFC 9700 が confidential client にも推奨。後から足すと code のデータ構造と token endpoint の契約が
変わる。**却下:** 「client_secret で守るから見送り」。secret はサービスのなりすましを防ぐが、code 自体の
盗難は PKCE でしか塞げない（役割が違う）。

## D-04. 認証 transaction は専用 Store（Session 単一フィールドを却下）
（詳細は D-19, D-20, D-21 に発展）

## D-04b. access token 失効は「利用時に generation を再検証」して初めて成立

**決定:** `/userinfo` で access token を使うたび、record の `auth_generation` と現在の User generation を
実際に比較し、不一致なら `invalid_token`。
**理由:** record に generation を保存するだけでは失効しない。当初コードは `resolve_access_token` が読んで
返すだけで比較が抜けていた（レビュー指摘 4）。

## D-05. return_to は Session.start() の前に退避
**決定:** `return_to` を transaction store から取り出しローカル変数に保持してから `Session.start()`。
**理由:** `Session.start()` は旧 Session を破棄する。後で旧 Session を読むと消えている。auth 側の認可要求も
同じ（→ D-19）。

## D-06. code は「検証してから削除」、原子的に
**決定:** client_id/redirect_uri/PKCE を検証し、通れば `MULTI` で code 削除＋access token 作成。`getdel` で
先に消さない。**理由:** 先に消すと、正しい secret を持つ別 client が他 client 向け code を提示して「利用は
失敗するが code は消せる」DoS が成立する。**後回し:** Lua/Function は性能問題が出てから（契約テストで追い
にくい）。

## D-07. 外部エラーは標準名で一律、内部で詳細区別
**決定:** token endpoint 外部は `invalid_request`/`invalid_client`/`invalid_grant`/`unsupported_grant_type`/
`invalid_scope` の標準名。詳細（expired/wrong_client/wrong_redirect_uri/wrong_code_verifier/already_used/
wrong_auth_generation）は内部ログのみ。**理由:** 細かい失敗理由を外へ返すと攻撃者に手掛かりを与える。

## D-07b. ID Token 検証は必須 claim を明示要求
**決定:** `jwt.decode(..., options={'require':['iss','sub','aud','exp','iat','nonce']}, leeway=60)`。加えて
sub 非空・nonce 一致・azp（複数 aud 時）・kid 既知を明示検証。claim 直接アクセスで 500 にしない。
**理由:** PyJWT は `require` を指定しないと claim 欠落を素通りし、`exp` 欠落時は期限検証自体ができない
（レビュー指摘 7）。

## D-08. ID Token は認証 claim 中心、email 等は /userinfo
**決定:** ID Token は iss/sub/aud/exp/iat/nonce/auth_time のみ。email/email_verified/picture 等は
`/userinfo`（access token + email scope）から返す。ID Token TTL は 5〜10 分。
**理由:** `email` scope は本来 UserInfo から返すのが OIDC の形。頻繁に変わる billing 状態を ID Token に
詰めると発行直後に古くなる。Client は UserInfo の sub が ID Token の sub と一致することを確認する
（レビュー指摘 8）。

## D-09. email_verified を永続保存しない（メソッドで導出）
**決定:** User に `email_verified` を持たない。`email` と `verified_emails` からメソッドで導出。
**理由:** `email` の存在自体が「確認済み」を意味する設計。二重保持は食い違いの新問題を生む。Google トークンの
`email_verified` クレームは検査するが保存しない（別物）。

## D-10. Redis 分離はキー Prefix、所有境界はインスタンス
**決定:** 論理分離は Prefix、所有境界（auth と各サービス）はインスタンス。DB 番号は使わない。
**理由:** Redis Cluster は DB0 のみで `SELECT` 不可。DB 番号を前提にすると将来のクラスタ化で壊れる。

## D-11. パスワードは Argon2id（復号可能方式を却下、フィールド名は password）
**決定:** `password` フィールドに Argon2id ハッシュを保存。復号処理は存在しない。
**理由:** AES 復号可能方式は DB とアプリ鍵の両方漏洩で全平文パスワードが復元され、使い回しで被害が波及。
NIST/OWASP は salt + コスト係数付き hashing を要求。旧ユーザー移行時のみ旧 AES を一度検証しログイン成功時に
Argon2id へ変換。**注意:** フィールド名は `password_hash` でなく `password`（D-15 で再確認）。

## D-12. client_secret は高エントロピー乱数 + SHA-256（Argon2id を却下）
**決定:** 32byte 以上の乱数を生成、SHA-256 ダイジェストで保存。
**理由:** 低エントロピーパスワードでないので Argon2id の高コストは不要。誤 secret 大量送信で Argon2id が走ると
CPU DoS 増幅。rotation（新旧 2 つ同時許容）構造は「将来対応できる形」に留め初版では作らない。
**方向別 credential:** auth→サービスの失効通知には client_secret を流用せず `revoke_webhook_secret` を使う
（さらに ID Token 署名鍵とも別。D-17）。

## D-13. identity mapping — (iss, sub) → local_user_id、初版は新規のみ
**決定:** サービスは `ServicePrincipal(issuer, subject)` をローカル user_id へ対応付ける。`(issuer, subject)`
に複合ユニークインデックス、並行初回 callback は atomic upsert / duplicate-key で二重作成を防ぐ。**初版は
新規のみ・既存ユーザー移行なし。**
**理由:** サービスに既存 user_id 体系が残ると auth の user_id 直接使用は壊れる。メールをマッピングキーに
しない（変わりうる・乗っ取りリスク）。移行が必要になった場合は事前移行 / 明示リンク / migration table の
いずれかを別途決める（自動メールリンクは禁止）。今回は「新規のみ」で確定（オーナー判断）。

## D-14. PROTOCOL.md は参照プラン、ソースコードと契約テストが正本
**決定:** endpoint/request/response の正本はソースコードと契約テスト。実装を曲げてまで文書に従わない。
食い違えばコードとテストを正とする。**帰結:** 既存文書に「PROTOCOL が唯一の凍結契約」とあれば矛盾するため
決定記録の更新が必要。

## D-15. Userモデルを既存決定に整合させる
**決定:** (a) 確認前 User を作るため `email` は optional（`unique, sparse`）、確認待ちは `suspended_email`。
(b) フィールド名は `password`（`password_hash` でない）。
**理由:** 既存思想（email=確認済み、suspended_email=確認待ち）と、確認前に User を作る signup フローの整合。
当初サンプルが `email required` かつ `password_hash` で不整合だった（レビュー指摘 15）。

docs/auth-spec/04_DECISIONS_AND_RATIONALE.md の既存 D-15 の項の直後に、次のブロックを追加する。
※前回渡した D-15b からさらに更新している(投影・単調性・不在既定・イベントログ却下を追記)。
既に前回版の D-15b を貼っている場合は、その項をこの内容にまるごと差し替える。

## D-15b. payment 連携と billing 保存先（DECISIONS D-45）

**決定:** auth と payment は DB を共有せず、payment で決済状態が変わったときだけ payment が auth へ
billing 状態を POST で push する(pull しない)。billing の真実源(権威)は payment サービスであり、
auth が持つのはその **読み取り専用の投影(projection)** である。auth 側の entitlement は payment からの
push でのみ更新され、auth 自身のロジックで昇格・降格しない。投影は、User でも ConnectedService でもなく、
独立モデル
`ServiceEntitlement(subject, client_id, plan, billing_status, payment_event_id, source_event_timestamp, updated_at)`
(`(subject, client_id)` 複合ユニーク)に保存する。サービス接続の事実は
`ConnectedService(subject, client_id, connected_at)` と分ける。決済 UI は auth の signup に含めず、
各サービスの共通設定 Modal に組み込む(無料サービスには入れない)。

**更新の冪等性と単調性:** push は `payment_event_id` で冪等(同一イベントを二重適用しない)。加えて
`source_event_timestamp` で単調性を守り、保存済みの timestamp より古いイベントは破棄する。Stripe の
webhook は順序保証がなく再送もあるため、冪等だけでは「古いイベントが新しい状態を上書きする」順序転倒を
防げない(例: 開始→即解約 が逆順で届くと解約後に開始状態へ戻る)。timestamp の厳密な意味(Stripe の
`created` / sequence 等)は payment 連携実装時に確定し、auth 初版は「古い更新は破棄」ルールだけ守る。

**entitlement 不在の意味:** ServiceEntitlement レコードの不在は「アクセス拒否」ではなく、そのサービスの
デフォルト状態(多くは無料/オープン枠)を意味する。billing_status を読む側は「entitlement が無ければ
デフォルト枠として扱う」を既定とし、レコードの有無を利用可否に直結させない。有料機能のゲートは
billing_status の値で行う。UserInfo で billing を返すときは protocol.py が ServiceEntitlement を読んで
4値へ丸め、不在時のデフォルト値も protocol.py が与える。ID Token には billing を入れない。

**理由:** DB 共有は schema 変更での相互破壊と全ユーザー DB 読み取り権付与を招く。auth からの pull は
payment 障害をログインへ波及させる。billing(webhook で反復更新)と接続履歴(初回一度)は更新主体・頻度が
異なるため、責務分離としてモデルを分ける(D-42/D-45 の思想を auth 内部でも守る)。

**却下した案(初版スコープ外):** ServiceEntitlement を追記型のイベントログ(billing 変更履歴の台帳)に
する案は却下する。イベント履歴の台帳は真実源である payment が持つべきで、auth に二重化すると「どちらが
正本か」という D-45 で避けた問題が再発する。auth は現在の投影状態1行のみを持ち、履歴が必要なら payment に
問い合わせる。billing の状態遷移モデル(trial / grace period 等)の本格設計も、payment が実際に push する
内容が具体化してから payment 連携時に詰める(初版は plan / billing_status / payment_event_id /
source_event_timestamp の最小形)。

## D-16. 実装量評価の訂正と完了条件
**決定:** 「完全 OIDC 準拠は 30 行」「約 400 行」という評価は happy path 限定として訂正する。production 品質の
protocol validation・negative test・鍵運用・失効・UserInfo を含む総量は数百行〜規模。**初版の完了条件は
`05` の 2 層テスト通過**。conformance suite 通過は外部開放時の完了条件（D-01 の線引き）。
**理由:** 過小評価のまま実装者へ渡すと品質要件が抜ける（レビュー指摘 16）。

## D-17. Session 強制失効の二段構え & 失効通知の設計
**決定:** (1) 各サービス Session に `revoke_all(user_id)` を追加（既存逆引き `sessions:{user_id}` を使い全消し）。
現行 `clear()` の責務不整合を `clear_current()` と `revoke_all()` に分離。(2) 各サービスに auth だけが叩ける
`POST /v1/sessions/revoke`。失効通知の payload は `{issuer, subject, auth_generation, reason, revocation_id,
issued_at}`、HMAC 署名（webhook secret、署名鍵と別）、timestamp 許容、revocation_id 重複確認、issuer 確認。
**MongoDB outbox に先に保存し失敗は再送**（同期 POST だけだとサービス停止中に永久消失）。
**理由:** auth と各サービスは別 Redis。両方消す仕組みが要る。冪等性・replay 対策・再送が無いと通知が壊れる
（レビュー指摘 11）。

## D-18. access token を初版から残す
**決定:** access token（opaque, TTL 1時間, Redis, DB 永続なし, localStorage/cookie に置かない）を初版から。
`/userinfo` 再取得に使う。**理由:** 後から導入すると token 交換レスポンス・auth client・サービス実装の契約
変更が必要。「最終形を先に作る」方針。

---

# 第 2 回レビューで発見・修正した見落とし（D-19 以降）

## D-19. auth 側の認可要求は専用 AuthorizationRequestStore へ
**決定:** auth 未ログイン時、認可要求を Session 単一フィールド（`pending_authorize`）でなく専用 Redis Store へ
保存し、signin 画面には短命 `request_handle` だけ渡す。signin 成功後は Store から取得して認可を再開する。
**理由:** (a) `Session.start()` 後に旧 Session の `pending_authorize` を読む D-05 と同型のバグ、(b) 単一
フィールドは同一ブラウザの複数サービス並行認証で上書きされる（レビュー指摘 1）。

## D-20. callback transaction は claim → complete/release の状態遷移
**決定:** quantz callback で transaction を `getdel` で即削除せず、`claim_for_callback`（読む→ブラウザ照合→
iss 照合→pending 確認→processing へ、を原子的に）してから token 交換し、成功/恒久失敗で削除、一時失敗で
`release`。`pending → processing → completed`。
**理由:** 検証前に削除すると、漏れた `state` を別ブラウザから送るだけで正規 transaction を破壊できる（DoS）、
通信失敗で再試行できない。状態遷移で並行 callback を 1 つだけ通す（レビュー指摘 2）。

## D-21. transaction bind は Session ID でなく browser_context_id
**決定:** Session ID とは別に `browser_context_id` を持ち、Session ローテーションをまたいで新 Session へ
引き継ぐ。transaction には Session ID でなくその digest を bind する。cookie/URL には出さない。
**理由:** Session ID を bind に使うと、タブ1 の `Session.start()` ローテーション後にタブ2 の callback が
`session_mismatch` になり複数タブが壊れる。独立キー化だけでは不十分（レビュー指摘 3）。

## D-22. /authorize と /oauth/token の入力検証を厳格化
**決定:** `/authorize` で `response_type==code`、`openid` scope 必須、要求 scope ⊆ allowed_scopes、
`code_challenge_method==S256` 必須（一覧にも追加）、client active、state/nonce/challenge の長さ・形式、
重複拒否。token endpoint も重複/欠落/型/Content-Type を先に検証。AuthService に `allowed_scopes`/
`trusted_first_party`/`subject_type`/`status`/`id_token_signing_alg` を追加。RFC 9207 の `iss` は成功時
だけでなく、有効な redirect_uri へ返す authorization error response にも添える。
**理由:** 値の意味検証と downgrade 経路封じが不足していた（レビュー指摘 6）。

## D-23. sub は ObjectId でなく独立 subject_id（pairwise への布石）
**決定:** ObjectId を DB 主キーとして保持しつつ、OIDC の sub には別生成のランダム `subject_id` を使う。
AuthService に `subject_type`（public / 将来 pairwise）。
**理由:** 一度公開した sub は不変。ObjectId 露出は内部構造の漏洩。独立 subject_id なら将来 pairwise subject
（client 群ごとに別 sub を見せて名寄せを防ぐ）を内部 identity を変えずに後付けできる。オーナー判断で独立を採用
（レビュー指摘 10）。

## D-24. server 間 HTTP client の制約と、iss からの URL 組み立て禁止
**決定:** `AuthClient` に `timeout=(3,10)`, `allow_redirects=False`, TLS 検証維持, Content-Type 検証,
レスポンスサイズ制限, Authorization/`code_verifier` をログに残さない。複数 issuer 対応では callback の `iss`
から token endpoint URL を組み立てず、開始時に選んだ **信頼済み設定** から引き（`returned_iss == provider.
issuer` を確認）。**理由:** timeout 無しは運用障害、iss からの URL 生成は攻撃者制御 URL への送信を招く
（レビュー指摘 14）。

## D-25. signin 等に CSRF 対策
**決定:** 認証前 Session に CSRF token を持たせ `POST /v1/users/signin` で検証（+ Origin/Fetch Metadata）。
`request_handle`（どの認可要求を再開するか）と csrf_token（この POST が auth 画面から来たか）は別物。認証前
Session ID は認証後へ昇格させず必ずローテーション。
**理由:** `state` は quantz callback を守るが auth 自身の login form は守らない。login form も login CSRF の
対象（レビュー指摘 13）。

## D-26. code 消費と token 発行の原子性境界を明示
**決定:** 「Redis の binding 確認 → Mongo の User/generation 確認 → ID Token 署名 → `MULTI`{code 削除 +
access token 作成} → `EXEC`」。Mongo/Redis をまたぐ完全 transaction は不可なので、途中 crash 時は
「ログインをやり直す」で回復。token request に一般的な自動 retry を設定しない。
**理由:** 「検証・消費・作成が一まとまり」という説明と実装の順次処理が不一致だった（レビュー指摘 5）。

## D-27. logout は 3 種、デフォルトは global
**決定:** service logout（そのサービス Session のみ）/ auth logout（中央 Session のみ）/ global logout
（中央 + 全サービス失効通知）の 3 つを実装。**ログアウトボタンのデフォルト = global logout**、個別ログアウトも
残すが目立たせない。global logout は失効フロー（D-17）を再利用。
**理由:** 通常 logout が未定義だと、quantz logout 直後の再ログインで中央 Session が残りパスワード無しで戻る
（SSO として正常だがユーザー期待と違う）。ユーザーは通常「全部から抜けたい」ため global をデフォルトに
（オーナー判断。レビュー指摘 12）。

## D-A. JWKS / metadata を初版から公開、鍵ローテーションは自動化
**決定:** `GET /oauth/jwks` と `GET /.well-known/openid-configuration` を初版から公開。署名鍵は Mongo に
`status(active|next|retiring|retired)` で保持。ローテーションは決定論的スクリプト＋スケジューラで自動化
（生成→JWKS 追加→待機→active 切替→待機→retired）。**Claude Code 等の対話エージェントは使わない。**
**理由:** 直書き構成は無停止ローテーションができない（新公開鍵を全サービスへ先行 deploy が必要）。JWKS なら
新旧同時掲載で無停止。エンドポイント 2 本で DB/サーバーは増えない。ローテーション手順は分岐が無く自動化可能で、
決定論的処理はスクリプトが適し、LLM エージェントの「その場判断」はここでは短所。オーナー判断で初版採用。
**運用の実体:** 「ローテーションスクリプト 1 本を書く」。以後は自動、日常手作業ゼロ。

## D-B. staging / production の秘密分離（無条件）
**決定:** 本番の署名鍵・client_secret・ユーザーデータを staging と共有しない。staging はテストデータのみ。
**理由:** auth の staging には署名鍵・client_secret・パスワードハッシュが存在する。staging に常駐エージェントを
置く/侵害される場合でも、漏れるのは「捨ててよい staging 用の秘密」に限られるようにする。auth は「一度作れば
ほとんど変更しない」性質のため staging に常駐エージェント（Claude Code）は置かず、ローカル修正→デプロイ→
テストコマンド一発の運用にする（`05`）。

---

## 未確定・実装時に決める事項
- production の t3 サイズ（起動直前に staging 実測と最新料金で確定）。
- 鍵ローテーション周期の具体値（例 90 日）と緊急ローテーション運用手順書。
- payment 側の scheduler/worker 方式（payment 実装時。auth 範囲外。別途 payment 実装入力文書）。
