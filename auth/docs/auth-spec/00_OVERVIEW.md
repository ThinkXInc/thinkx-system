# Auth 認証基盤 — 設計仕様（実装者向け）

このディレクトリは、共通認証サービス `auth` の認証フロー設計仕様である。
実装を開始する前に、まず本ファイルを読み、続いて番号順に読むこと。

各ファイルの役割は次のとおり。

- `00_OVERVIEW.md`（本ファイル）— 全体像、用語、設計の大原則、他ドキュメントとの関係。
- `01_PROTOCOL_FLOW.md` — 認証フローの完全な手続き。誰がどのリクエストを送り、何が返るか。実際のコードに近い形で記述。
- `02_SECURITY_CONCEPTS.md` — フローに登場する各値（state, PKCE, nonce, ID Token, iss/aud/sub 等）が「何の攻撃を防ぐために存在するか」。フローの各ステップの根拠。
- `03_DATA_AND_INFRA.md` — データモデル、Redis のキー設計、サーバー構成、cookie・失効・鍵管理・JWKS・logout。
- `04_DECISIONS_AND_RATIONALE.md` — 設計判断の記録。検討したが採らなかった案と理由。「なぜこうなっているか」で再議論しないために読む。
- `05_TESTING_AND_OPERATIONS.md` — 完了条件、テスト構成（論理層＋E2E疎通層）、negative test 一覧、開発運用フロー、鍵ローテーション。

---

## この設計が何であるか（要約）

`auth` は、複数の自社サービス（`quantz` 等）に対する中央認証サービスである。
ユーザーのパスワードは `auth` だけが扱い、各サービスはパスワードを一切受け取らない。
`auth` は認証結果を、**盗難・すり替え・偽造のいずれにも耐える形で**各サービスへ渡す。
この要件を満たすため、設計は **OpenID Connect (OIDC) の Authorization Code Flow + PKCE(S256)** に準拠する。

各サービスはログイン成立後、**従来どおり自前のローカル Session でユーザーを判定する**。
通常のページ表示で毎回 `auth` へ問い合わせることはない。変わるのはログインの入口だけである。

```
変更前: 各サービスが自前でパスワード検証 → Session.start(user_id)
変更後: auth がパスワード検証 → OIDC で認証結果を受け渡し → Session.start(local_user_id)
```

`Session.start()` 以降の各サービスの構造は、変更前と同じである。

---

## 正確な呼称（重要）

この実装を、無条件に「OIDC 準拠」と呼ばないこと。初版が対象とするのは次に限定される。

> 静的登録された first-party confidential web client 向けの、
> OpenID Connect Core Authorization Code Flow + PKCE(S256) 実装

`prompt` / `display` / `ui_locales` / `max_age` / `acr_values` などの汎用 OP 要件は初版スコープ外。
これらは外部 RP へ開放する段階で足す。OpenID Foundation の conformance suite 通過を「OIDC Core 準拠」と
名乗る条件とし、それは外部開放時の完了条件に置く（初版の完了条件は `05` のテスト通過）。

---

## なぜ OIDC 準拠なのか（背景）

当初は「OAuth 風の独自プロトコル + opaque token」での最小実装も検討したが、OIDC 完全準拠を採用した。

1. **インフラコストが増えない。** 追加されるのは署名鍵ペアと read-only な JWKS/metadata エンドポイント
   だけで、サーバー台数・DB・プロセスは増えない（`03`）。追加コストはソースコード上の署名手続きに閉じる。
2. **プラットフォーマー戦略上の価値。** 認証 API を将来外部（他社アプリ）へ開放できる余地が生まれる。
   独自プロトコルではこの開放が困難。
3. **既存知見の延長。** `quantz` は既に JWT を利用しており、OIDC の心臓部（署名・検証、iss/aud/exp 検証）は
   その直接の延長である。

---

## 使用するライブラリ・自作範囲

- **使用するライブラリは JWT のみ**（`quantz` で使用実績のあるもの、PyJWT を想定）。
- **Authlib 等の OAuth/OIDC フレームワークは使用しない。** 既存の MongoEngine User / Redis Session /
  libcommon Session を、フレームワークが要求する Mixin へ翻訳する「アダプタ層」の実装・保守コストが、
  肩代わりされる処理量を上回るため。また「ソースコードと契約テストを契約の正本にする」方針（D-14）と、
  フレームワーク内部のブラックボックス化が衝突するため。詳細は `04` D-02。
- **アダプタ層は存在しない。** 自作するため、モデルを外部仕様へ翻訳する層が不要。
- 各ハンドラを読めば入力・検証・認証・レスポンス・エラーがすべて見える状態を保つこと。

---

## 用語（全体で統一）

| 用語 | 意味 |
|---|---|
| auth | 中央認証サービス。パスワード検証・ID Token 発行を担う。OIDC の Authorization Server。 |
| サービス / client | auth を利用する各サービス（quantz 等）。OIDC の Client / Relying Party。 |
| 中央 Session | ユーザーが auth にログイン済みであることを表す Session（auth 所有 Redis）。 |
| ローカル Session | ユーザーが各サービスにログイン済みであることを表す Session（各サービス所有 Redis）。 |
| authorization code | auth が発行する短命（60秒）・一回限りの引換券。認証結果そのものは含まない。 |
| ID Token | auth が秘密鍵で署名した JWT。「誰であるか」の証明。認証 claim 中心（email 等は含めない）。 |
| access token | opaque な短期トークン（1時間）。ログイン後の情報再取得（/userinfo）用。 |
| authorization request | auth 側で signin を挟む間、再開に必要な認可要求を保持する一時レコード（専用 Store）。 |
| client transaction | quantz 側で、ログイン開始〜callback を紐付ける一時レコード（専用 Store）。 |
| browser_context_id | Session ID とは別の、ブラウザ識別子。Session ローテーションをまたいで引き継ぐ。認証資格ではない。 |
| subject_id (sub) | ユーザーの恒久 identity。ObjectId とは別に生成するランダム値。OIDC の sub。 |
| auth_generation | 失効の世代番号。code / access token に刻み、reset 時に増やして一括失効する。 |

### 命名規約（内部名 vs wire 名）

自分たちで決められる名前は実態に合わせ、外部プロトコルが固定する名前はそれに従う（矛盾しない）。

| 内部名（コード内） | wire 名（URL/HTTP 上） | 備考 |
|---|---|---|
| `authorization_transaction_id` | `state` | wire 名は OAuth 標準の予約語。境界で読み替える。 |
| `SERVICE_ID` | `client_id` | 標準名に統一。 |
| （auth 自身の識別子）`AUTH_ID` | — | auth デプロイメントの識別子。接続サービスの `SERVICE_ID` とは別。 |

---

## 読む順序と、各ドキュメントが答える問い

1. `01` — 「実装として何を作るのか」
2. `02` — 「なぜ各ステップにその値が必要なのか」
3. `03` — 「どこに何を保存し、どう配置するのか」
4. `04` — 「なぜ他の案ではなくこれなのか」
5. `05` — 「何が完成なら完成なのか、どう開発・運用するのか」

`01` と `02` は対。ステップ番号と概念が相互参照する。実装中に「この検証は何のためか」と迷ったら `02`、
「なぜこの構成か」と迷ったら `04`、「どこまでやれば完了か」と迷ったら `05` を参照。

---

## この設計が守り続けるべき不変条件（実装中の指針）

1. パスワードは auth だけが受け取る。サービスは一切受け取らない。
2. 秘密（認証結果・access token・client_secret・code_verifier）はブラウザの URL に載せない。
3. sub は一意・不変・非再利用（identity の土台）。ObjectId とは分離した `subject_id` を使う。
4. redirect_uri / return_to は完全一致 / 相対パスのみ（宛先の固定）。
5. authorization code / client transaction は「検証してから削除」。検証前に消さない。
6. Session ID は必ずローテーションし、`browser_context_id` だけを引き継ぐ。
7. 全ハンドラを読めば契約が見える（ソースコードが正本）。
8. Redis は消えても回復可能なものだけ、MongoDB だけをバックアップ。
9. 本番の署名鍵・client_secret・ユーザーデータを staging と共有しない。
