<!-- 配置: thinkx-system/monorepo/citywalk/CLAUDE.md -->

# citywalk — リポジトリ規範(CLAUDE.md)

> 層状配置: 組織公理は `monorepo/docs/conventions/AXIOMS.md`。契約層は libcommon CLAUDE.md(L-7)と
> **auth 認証基盤の仕様 `monorepo/auth/docs/`(00〜05)**。本書はリポ固有の規約のみを重ねる。
> 実行の規範は `monorepo/citywalk/refactor_plan.md` v3.0(本計画が本書より優先)。

## このリポジトリは何か

CITYWALK(音声ガイド)のサーバ + ビジネスコンソール。monorepo サブディレクトリとして再構築中(v3.0)。
**現在一切稼働していない**(破壊的改善が安い)。アカウントは auth(OIDC)の単一アカウント。
**ビジネスアカウントという独立概念は無い**(D-29)。人物同一性は
`ServicePrincipal(issuer, subject) → local_user_id`。ビジネス機能へのアクセス権は
organization_membership(local_user_id + organization_id + role)。

## 二等級制(必読)

- **[UI不変]**: ユーザーが**見て・触って知覚する面**(見た目・レイアウト・遷移・操作反応・文言・
  **アニメーションの流れ**)。正解は **createguide デモ動画(ground truth)** + `tests/golden/ui_legacy/` の
  3層オラクル(静止画スクショ回帰 / アニメーションフレーム列 / jsdom 知覚特性)。明記なき知覚面の変更は違反。
- **[再構築]**: サーバ実装・ワイヤ契約・モデル・構成、**および DOM 構造・クラス名・マークアップ**。
  正解は本計画の新ゴールデン。DOM は内部表現であり自由に作り直す(そうでなければリファクタでない)。

## auth 統合(OIDC client。auth/docs が唯一の正)

citywalk は auth の **client(Relying Party)** である。auth は OIDC Authorization Code Flow + PKCE(S256)。
citywalk が実装するのは auth/docs 01 の「各サービス(quantz)側」に対応する client 実装のみ:

- `auth_client/`: `ClientTransactionStore`(code_verifier/nonce/return_to/expected_issuer を Redis prefix
  `oidc:client_transaction:*` に保持。bind は browser_context_id の digest)・`AuthClient`(/oauth/token を
  サーバー間で叩く)・`IDTokenVerifier`(PyJWT で ID Token を JWKS 公開鍵検証・nonce/aud/iss 照合)。
- ハンドラ: `/auth/signin`・`/auth/callback`・`/v1/sessions/revoke`(失効 webhook)・logout(3種)。
- identity: `ServicePrincipal(issuer, subject) → local_user_id`(複合ユニーク・二重作成防止)。
- Session: `libcommon.web.session` を citywalk 所有 Redis・cookie `citywalk_session_id`・prefix
  `citywalk:session:*` で使う。browser_context_id 引き継ぎと Session ローテーションを守る。

**citywalk 内で絶対に書かないもの(auth の管轄)**: パスワード検証・確認コード・**ID Token の発行**・
authorization code / access token の発行・JWKS 発行・認証以外の独自 JWT。ID Token/UserInfo を
verifier 以外で組み立て/解釈すること。auth 仕様が更新されたら auth/docs に追随する(先回りしない)。

## vendored libcommon / simplicity の扱い(B案・D-35)

- `web-server/libcommon/`・`web-server/views/src/js/simplicity/` は canonical v2.1.0 から焼いた実体コピー。
  **B案で編集可**だが本計画中は消費に徹する。変更が要れば findings 記録 → 原本(`/src/libcommon/.git` 等)へ還流。
- vendored libcommon の tree_sha は既存消費者(thinkx)と一致させる(CHECKSUMS 照合)。
- **存在しない libcommon API を推測しない。** ImportError 握り潰し・hasattr 探り禁止。API 面の実測典拠は
  monorepo 内の既存消費者(thinkx/auth の web-server)。

## ハンドラの書き方(既存サービスと同流儀)

- デコレータ正順: route → content_type_check_json → required_fields_check / validate_request →
  session/認可 → 本体。ハンドラ内での必須/形式チェックの再実装(私設 `_api_error`・独自 ErrorResponse)禁止。
  レスポンスは libcommon の SuccessFormat / 名前付きエラークラス。旧 `api_response.py` 形式を持ち込まない。

## libcommon / simplicity の使い方

- 多言語: `libcommon.locale.Locale` + `locales/*.json`。locale.get を try/except で包むフォールバック禁止
  (fail loudly)。ログ: `libcommon.logger.Logger` + `libcommon.color`。print デバッグ禁止。
- モデル: `libcommon.mongomodel.MongoModel`(旧 `MongoBase.__structure__` は持ち込まない)。
- simplicity: src への import/export/require 禁止(D-1)。拡張は「基底 + 1段」(AXIOMS 継承規約)。
  View 内で HTTP 通信しない(最小権限)。**build → test の順を厳守(D-30)。**

## 命名(静的ゲートの検査対象)

- 一つの事実に一つの名前。alias の並存禁止。**禁止命名**: `business_account`/`organization_member`
  (旧二重アカウント語彙)、`date_utils` と `dateutils` の並存、旧 ErrorCode/ErrorResponse 系。
- 外部境界(auth ワイヤ)だけは auth/docs の名前(state/client_id/sub 等)で読み書きし、内部では使わない
  (内部名 authorization_transaction_id ↔ wire 名 state、内部 SERVICE_ID ↔ wire client_id)。

## 禁止事項

- パスワードハッシュ・確認コード・JWT 発行の実装(認証は auth。D-9)。ID Token/UserInfo を verifier 以外で解釈。
- `tests/golden/` の凍結済みゴールデン・スクショ/アニメ基準・デモ動画・`refactor_plan.md` の編集。
- `request.get_json(silent=True)`。ImportError の握り潰し。秘匿情報のコード直書き(D-22: 即停止・報告)。

## 起動・テスト

```
pip install -r web-server/requirements.txt   # exact ピン(PyJWT 含む)
python3 -m pytest -q web-server/tests        # 外部インフラ不要(fakeredis/mongomock)
python3 web-server/main.py                   # local
```