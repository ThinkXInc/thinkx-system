# 05 — 完了条件・テスト構成・開発運用

「何が完成なら完成か」「どう開発・運用するか」を定義する。

---

## 初版の完了条件

初版は次をすべて満たした時点で完了とする。

1. `01` のフロー全体が staging（auth・quantz が別ホスト）で通しで動く。
2. 下記 **negative test 一覧**がすべて自動テストで通る。
3. 2 層テスト構成（論理層 + E2E 疎通層）と seed コマンドが整備されている。
4. JWKS / metadata エンドポイントが公開され、ID Token が `kid` 経由で検証できる。
5. 鍵ローテーションスクリプトが存在し、staging で新旧鍵の同時検証が確認できる。

**OpenID Foundation の conformance suite 通過は初版の完了条件に含めない。** それは prompt/display/
max_age/acr_values 等、first-party 内部利用では不要な OP 要件まで問うため、`00`/D-01 の「最小構成・
first-party 限定」方針を超える。conformance suite は **外部 RP へ開放する段階の完了条件**に置く。

---

## テストは 2 層に分ける

**論理層（単体テスト、実サーバー不要、ローカル/CI で一発）**
認証ロジックの正しさを、サーバーを立てずに検証する。negative test の大半はここ。デプロイ前にほとんどの
バグを捕まえる主戦力。

**E2E 疎通層（staging、最小シナリオ）**
論理を論理層で固めた上で、「auth と quantz が別ホストで実際につながるか」（cookie・redirect・サーバー間
POST・JWKS 取得）だけを確認する。全ケースをここで試さない。**実ブラウザ自動化（Playwright 等）は使わず、
cookie を保持する HTTP クライアント（requests の Session）でリダイレクトを追う簡易 E2E で足りる**。auth の
フローはブラウザ固有挙動に依存しない（リダイレクトと cookie と POST だけ）ため、これで数秒で終わる。UI の
見た目確認が必要になったら Playwright を後で足す。

**seed コマンド**
staging の auth を一発で初期化できること。テスト用 User（パスワードハッシュ入り）、テスト用 AuthService
（client_id/secret/redirect_uri/allowed_scopes 登録済み）、署名鍵を投入・リセットする。これが無いと
「テストコマンド一発」が成立しない。

---

## negative test 一覧（自動化必須）

契約テストとして最低限これらを自動化する。各項目は `01`/`02`/`04` の該当設計に対応する。

**認証 transaction / 複数タブ / 状態遷移（D-19,20,21）**
- 同一ブラウザで 2 つの認証を並行開始できる。
- 1 つ目の Session ローテーション後も 2 つ目が成功する（browser_context_id 引き継ぎ）。
- 別ブラウザの state では transaction が削除されない。
- wrong iss では transaction が削除されない。
- 同じ code の同時使用は一方だけ成功する（processing ロック）。

**PKCE / code（D-03,06,26）**
- wrong code_verifier では code が削除されない。
- code_challenge_method が S256 以外は拒否される。
- 同じ code の二度目の引き換えは失敗する。

**auth_generation 失効（D-04b,17）**
- password reset 後の古い code は失敗する。
- password reset 後の古い access token（/userinfo）は失敗する。

**ID Token 検証（D-07b,08）**
- 必須 claim（iss/sub/aud/exp/iat/nonce）欠落の ID Token は認証失敗になる。
- wrong aud / wrong iss / wrong nonce を拒否する。
- 複数 aud で azp が client_id と不一致なら拒否する。
- UserInfo の sub が ID Token の sub と違えば拒否する。

**鍵ローテーション（D-A）**
- 新旧 2 つの signing key を rotation 期間中に両方検証できる。
- retired 鍵は JWKS に現れず、その kid の ID Token は検証失敗する。

**identity mapping（D-13）**
- ServicePrincipal の同時作成（並行初回 callback）で 1 件だけ作られる。

**失効通知（D-17）**
- 失効 webhook の再送は一度だけ適用される（revocation_id 冪等）。
- 古い（timestamp 逸脱）または改ざん済み webhook を拒否する。
- auth 停止・service 停止後も失効通知が outbox から再送される。

**入力検証 / CSRF（D-22,25）**
- 重複パラメータ / 必須欠落を invalid_request で拒否する。
- 要求 scope が allowed_scopes 外なら invalid_scope。
- 未登録 / 不一致 redirect_uri では error redirect せず自前エラーページ。
- signin CSRF（token 無し / Origin 不正）を拒否する。

**HTTP client（D-24）**
- token endpoint 通信の timeout が効く。
- callback の iss から token endpoint URL を組み立てず、信頼済み設定から引く。

---

## 開発運用フロー

auth は「一度作ればほとんど変更しない」性質のため、**staging に常駐エージェント（Claude Code 等）を置かない**
（`04` D-B）。開発は次の構成で行う。

```
ローカル（開発機）で修正
      ↓ デプロイ
staging（auth・quantz が別ホスト、テストデータのみ）
      ↓ テストコマンド一発
論理層テスト + E2E 疎通テストが走り、動作を確認
```

この構成が成立する条件は「完了条件 3」の 2 層テスト + seed コマンド。これらを最初に整備すること。
定型作業（鍵ローテーション等）は決定論的スクリプト＋スケジューラで行い、対話エージェントは使わない。

### staging / production 分離（無条件、`04` D-B）

本番の署名鍵・client_secret・ユーザーデータを staging と共有しない。staging の署名鍵・client_secret は本番と
別物、staging のユーザーはテストデータのみ。staging が侵害されても、漏れるのは捨ててよい staging 用の秘密に
限られる。

---

## 鍵ローテーション運用（`03` 鍵管理・`04` D-A）

`rotate_keys` スクリプト 1 本を用意し、スケジューラ（例 90 日周期）に乗せる。手順は決定論的:

```
1. 新鍵ペア生成、新 kid、status=next で保存
2. 既存トークン TTL（最大 access token 1時間）を超える待機
3. active を新鍵へ切替、旧鍵 status=retiring
4. さらに待機
5. 旧鍵 status=retired（JWKS から消える）
```

漏洩時は同じスクリプトを手動トリガー（緊急ローテーション）。日常の手作業はゼロ。切替期間中 JWKS に新旧両方の
公開鍵が並ぶため無停止。この手順を staging で検証することを完了条件 5 に含める。

---

## 参考: 実装の着手順序（推奨）

1. データモデル（User, AuthService, ServicePrincipal, 署名鍵）と seed コマンド。
2. 署名鍵と JWKS / metadata エンドポイント（先に鍵基盤を固める）。
3. auth: `/oauth/authorize` → signin → `/oauth/token` の happy path。
4. quantz: `/auth/signin` → `/auth/callback` → `AuthClient` → `IDTokenVerifier` の happy path。
5. 論理層 negative test を上記に対して埋めていく（transaction 状態遷移・PKCE・generation・ID Token 検証）。
6. 失効フロー（revoke_all, 失効通知 outbox, /v1/sessions/revoke）と logout 3 種。
7. E2E 疎通テストを staging で通す。
8. 鍵ローテーションスクリプトと staging での検証。
