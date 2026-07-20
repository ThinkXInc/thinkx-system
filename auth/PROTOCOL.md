# ThinkX Auth Protocol v1 (確定版)

> **位置付けの変更:** 正本は `docs/auth-spec/` とソースコード・契約テストである。
> 本ファイルは旧設計を記録した参照プランに格下げし、実装上の契約として使用しない。

全サービス共通アカウントシステム (auth) と各サイトの間の通信契約。
この文書が唯一の契約であり、auth の内部実装・libcommon のバージョンとは独立に安定させる。

## 0. 設計原則 (この形に決めた理由の要約)

1. **手続きの形は OAuth2 認可コードフローから借りる。**
   複数の .com ドメインにまたがるため Cookie 共有はできない。
   「中央でログイン → 一回限りのコードをブラウザ経由で渡す → サイトのサーバがコードを交換する」
   という手続きは、ブラウザという信用できない経路に本物の情報を流さないための、実証済みの形。
2. **署名付きトークン (JWT) と refresh_token は持たない。**
   それらは「信用できない他人のアプリ」と「発行元に問い合わせられない規模」のための装置。
   現段階の我々は全サービスが身内で、検証は auth への問い合わせ (Redis) で足りる。
   必要になる条件は §7 に明文化してあり、その時に protocol_version 2 として追加する。
   追加は既存サイトを壊さない (§6)。
3. **命名は「キーを見て中身が完全にわかる」を優先する。**
   OAuth/JWT の略語 (sub, aud, iss 等) は採用しない。
   Google と直接話す境界 (libcommon/web/google_oauth_helper.py) だけは Google の名前で読む。
   フローの形を定義する語 (redirect_uri, state) は、認可コードフローの標準名として残す。

## 1. 登場人物と経路

| 名前 | 実体 |
|---|---|
| ブラウザ | ユーザーの手元。**信用できない経路 (フロントチャネル)**。URL・履歴・ログに露出しうる |
| サイト | quantz-web, podcast 等の各サービスのサーバ |
| auth | 共通アカウントサービス。アカウント DB とパスワードを持つ唯一の場所 |
| バックチャネル | サイトのサーバ ⇄ auth の直接 TLS 通信。ブラウザを経由しない |

原則: **フロントチャネルには一回限りの auth_code だけを流す。ユーザー情報と access_token は
バックチャネルでしか渡さない。** パスワードはブラウザと auth の間だけを通り、サイトは永遠に見ない。

## 2. 手続き: ログイン (SSO)

1. ユーザーがサイトの保護ページ (例: quantz のマイページ) にアクセスする。
   サイトはログイン状態 (自サイトのセッション) が無いことを確認し、
   ランダムな `state` を生成して自サイトのセッションに保存した上で、ブラウザを auth へ 302 で飛ばす:
   `https://auth.thinkx.com/authorize?service_id=quantz&redirect_uri=https://quantz.../auth/callback&state=...`
2. ブラウザが auth に着地する。**ここからユーザーは auth と直接話す。サイトは介在しない。**
   auth に中央セッションが無ければ、ログイン画面 (メール+パスワード、または Google ログイン) を表示する。
   ユーザーが認証する。auth に中央セッションが既にあれば、この段は画面なしで即座に通過する
   (= 2つ目のサイトからは「ログイン画面を見ずにログインされる」。これが SSO の体感になる)。
3. auth は `redirect_uri` が service_id に登録済みの値と完全一致することを確認し
   (オープンリダイレクト防止)、一回限りの `auth_code` (Redis 保存・60秒 TTL) を発行して、
   ブラウザを `{redirect_uri}?auth_code=...&state=...` へ 302 で戻す。【フロントチャネル】
4. サイトは受け取った `state` が手順1で保存した値と一致することを確認する (CSRF 防止)。
   一致したら、サーバから auth へ直接 POST する。【バックチャネル】
   `POST /v1/token/exchange` `{"auth_code": "...", "service_id": "quantz", "service_secret": "..."}`
5. auth は service_secret を照合し、auth_code を消費する (読んだ瞬間に無効化。二度目は失敗する)。
   正当なら UserInfo (§3) + `access_token` + `expires_in` を返す。
6. サイトは `Session.start(userinfo['user_id'])` で**自サイトのローカルセッション**を開始し、
   ユーザーを元のページへ戻す。以後の通常アクセスはローカルセッションだけで判定し、
   **ページ表示のたびに auth へ問い合わせない** (auth が真、サイトはそのキャッシュ、更新は明示的に)。
7. 【後日の再確認】決済直後など課金状態を取り直したいとき、次のどちらかで行う。
   - `GET /v1/userinfo` に `Authorization: Bearer {access_token}` (exchange で得た token、TTL 1時間)
   - `GET /v1/users/{user_id}` に service_id + service_secret (サーバ間。token の期限に依存しない)
   後者が基本。これが「ユーザー不在でも身内のサーバは照会できる」という、
   refresh_token のファーストパーティ版に当たる。
8. 【ログアウト】サイトは先に自サイトのセッションを破棄し、その後ブラウザを
   `https://auth.thinkx.com/v1/logout?redirect_uri=...` (登録済み URI のみ) へ飛ばして
   中央セッションも破棄する。

## 3. UserInfo (全サイトが依存する唯一の JSON)

`/v1/token/exchange`・`/v1/userinfo`・`/v1/users/{user_id}` の成功レスポンス本体。

```json
{
  "protocol_version": 1,

  "user_id": "665f1c2ab8e4d21f3c9a7e01",
  "email": "user@example.com",
  "email_verified": true,
  "name": "Taro Yamada",
  "picture_url": "https://auth.thinkx.com/media/avatars/665f1c2a.png",
  "locale": "ja",

  "services": {
    "quantz":  { "plan": "pro",  "billing_status": "active" },
    "podcast": { "plan": "free", "billing_status": "none" }
  },

  "access_token": "(exchange のレスポンスのみ)",
  "expires_in": 3600,

  "code": 200,
  "message": "ok"
}
```

| キー | 型 | 意味 |
|---|---|---|
| `protocol_version` | int | この契約のバージョン。全レスポンスに必ず含める |
| `user_id` | string | ユーザーの不変 ID。**サイト側が保存してよい唯一のキー** (Session のキー名とも一致) |
| `email` | string | 表示用。変更されうるのでキーとして保存しない |
| `email_verified` | bool | 確認コード検証済みか (Google ログイン経由は常に true) |
| `name` / `picture_url` | string\|null | 表示名 / アバター URL |
| `locale` | string | ユーザーの言語 |
| `services` | object | **サービスごと**の課金状態。キーは service_id。各サイトは `services[自分の service_id]` を読む。エントリが無いサービスは未利用。キー一覧が「利用可能なサービス一覧」を兼ねる (同じ事実を別フィールドに二重に持たない)。エントリはそのサービスへの初回ログイン成立時に plan "free" で作られ、課金イベントで更新される |
| `services.*.plan` | string | そのサービスでのプラン。`"free"` / `"pro"` 等 |
| `services.*.billing_status` | string | そのサービスでの課金状態。`"none"` / `"active"` / `"past_due"` / `"canceled"` の4値。Stripe の生ステータスは auth が丸める。全サイトを Stripe の仕様から絶縁するため |
| `access_token` / `expires_in` | string / int | exchange のレスポンスにのみ含む。再照会用と残り秒数 |
| `code` / `message` | int / string | libcommon の既存レスポンス外形 (全サイト共通契約なのでここでは改名しない) |

補足: exchange のリクエストキーを `code` でなく `auth_code` とするのは、
レスポンス側に libcommon 外形の `code: 200` が存在し、同じやり取りの中で
同名キーが別の意味を持つ衝突を避けるため。

課金をサービス単位の構造にした理由: 課金の実体 (Stripe の subscription) はサービス単位で
発生するので、これが真実の構造。アカウント全体で一つのプランに統一する事業判断をした場合も、
この構造のまま全エントリに同じ値を入れれば表現できる。逆にフラットな `plan` で v1 を凍結すると、
後からサービス別が必要になったとき §6 の改名禁止により行き止まりになる。
また、フラットな `plan` は「どの範囲のプランか」がキーから読めず、命名原則
(キーを見て中身が完全にわかる) に反する。スコープは名前だけでなく構造でも自明にする。

サービスごとの出し分け: exchange は service_id を知っているので、必要になれば
サービスごとに返すフィールドを変えられる (素の JSON をサーバ側で組み立てているため)。
v1 では全サービス同一とする。

## 4. エンドポイント一覧

| メソッドとパス | 経路 | 認証 | 用途 |
|---|---|---|---|
| `GET /authorize` | フロント | 中央セッション | §2 手順1〜3。query: `service_id`, `redirect_uri`, `state` |
| `POST /v1/token/exchange` | バック | service_secret | §2 手順4〜5。body: `auth_code`, `service_id`, `service_secret` |
| `GET /v1/userinfo` | バック | Bearer access_token | 再照会 (token 有効期間内) |
| `GET /v1/users/{user_id}` | バック | service_id + service_secret | 再照会 (サーバ間の基本ルート)。資格情報はヘッダ `X-Service-Id` / `X-Service-Secret` で送る (この2名のみ。別名なし) |
| `GET /v1/logout` | フロント | 中央セッション | 中央セッション破棄。query: `redirect_uri` (登録済のみ) |

## 5. エラー形式

libcommon の APIErrorFormat に `protocol_version` を加えたもの。

```json
{ "field_name": "auth_code", "code": 401, "message": "...", "reason": "UNAUTHORIZED", "protocol_version": 1 }
```

| ケース | HTTP | reason |
|---|---|---|
| auth_code が不正・期限切れ・使用済み | 401 | UNAUTHORIZED |
| service_secret 不一致 | 401 | UNAUTHORIZED |
| service_id 未登録 / redirect_uri 不一致 | 403 / 400 | FORBIDDEN / BAD_REQUEST |

補足: 必須フィールド欠落などのフィールド検証エラーは、libcommon 全体で共通の
errors 配列型 (全アプリ共有の既存契約) をそのまま返す。protocol_version を含むのは
上記の単体エラー形式のみ。

## 6. 互換性ルール

1. v1 のフィールドは削除・改名・型変更しない。**追加のみ許す** (v1 の消費者は未知のキーを無視する)。
2. 破壊的変更は `protocol_version: 2` を新設し、リクエストで 2 を明示した
   サービスにだけ 2 を返す。無指定は永久に 1。古いサイトは何もしなくても動き続ける。
3. 消費側 (libcommon auth_client) は受信 JSON の `protocol_version` を検査し、
   期待値と違えば UserInfo を信用せず再ログインへ誘導する。

## 7. protocol_version 2 への昇格条件 (明文化された引き金)

次のいずれかの事業判断・状況が生じた時点で、v2 の設計に着手する。
**先回りで実装はしない。** 理由: フィールド追加は §6 により後からでも既存サイトを壊さずに
できる一方、署名鍵の運用 (発行・配布・ローテーション・失効) は必要になった時点でしか
正しく作れず、先に作ると使われないまま契約に永久凍結されるため。

- (a) **他社のアプリが、ThinkX のユーザー本人のデータへ、本人の同意の下でアクセスする**
  (ユーザー委任)。→ 同意画面・scope・refresh_token・署名付きトークンが必要になる。
  詳細は PROTOCOL_ROADMAP.md の第3段階。
- (b) トークンやユーザー情報を**フロントチャネルに流す**必要が生じる
  (例: SPA がサイトのサーバを介さず直接 auth と話す構成)。→ 署名が必要になる。
- (c) 検証量が auth への問い合わせで捌けない規模になる。→ ローカル検証 (署名) が必要になる。
- (d) サイトを**別リージョン・別インフラに分離**し、auth が落ちても各サイトの認証を
  継続させたい。→ ローカル検証 (署名) が必要になる。

注意: **レコメンド API の他社提供は、それ自体はこの引き金ではない** (相手企業が自社データで
API を使う限り、ユーザー委任は発生しない)。それは v1 への追加で対応できる別の段階であり、
PROTOCOL_ROADMAP.md の第2段階に定義する。他社が「ThinkX ユーザーのデータに基づく
レコメンド」を求めた瞬間に (a) が成立し、この節が発動する。
