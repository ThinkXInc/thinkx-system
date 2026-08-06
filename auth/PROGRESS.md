# auth/PROGRESS.md

auth Phase 4d の作業状態と、次セッションの再開点を記録する。

更新日: 2026-08-05

現在フェーズ: C reference client 実装（core checkpoint 完了、route/E2E 未完了）

## ここまで完了

- L/A security hotfixとして、canonical libcommon v2.2.1をreleaseした。
- Session本体prefixを`Session.configure()`と`RedisSessionInterface`で単一化し、不一致時は起動を拒否する。
- Session cookieのSecure/HttpOnly/SameSite/path/domainを実際のSet-Cookie・削除Cookieへ反映した。
- `Session.start()` / `clear_current()` / `revoke_all()`のRedis mutation失敗を呼び出し元へ再送出する。
- 実Cookieを使う2 client試験で、global logout後に別端末の認証が継続しないことを固定した。
- auth snapshotをcanonical v2.2.1へ再bakeし、prefix設定を`auth_session:`へ統一した。
- `auth/reference-client/`を、auth serverとcookie・Redis・MongoDB・requirementsを共有しない独立componentとして作成した。
- reference clientへcanonical libcommon v2.2.1を正規bakeした。
- `ClientTransactionStore`を実装した。raw stateをRedis keyへ出さず、digest key・TTL・
  browser context/issuer照合・WATCH/MULTIによる`pending -> processing`・claim ownership・
  `complete/release`を持つ。
- `AuthClient`を実装した。信頼済みprovider設定以外からURLを作らず、HTTP Basic、form encoding、
  `timeout=(3, 10)`、redirect拒否、TLS検証、JSON Content-Type、64 KiB上限、自動retryなしを固定した。
- `IDTokenVerifier`を実装した。RS256、既知kid/JWKS、iss/sub/aud/exp/iat/nonce/auth_time、
  nonce定数時間比較、複数aud時のazpを検証する。
- `ServicePrincipal` / `LocalUser` / `RevocationReceipt`のdurable model基盤を追加した。
- C coreの詳細・既知の統合ギャップは`auth/findings.md`へ記録済み。

## 現在greenの検証

- canonical libcommon: 88 tests passed、ruff green、pyright 0 errors。
- auth L/A hotfix後: 92 passed / 1 opt-in skipped / 1既存warning、compileall green、pip check green。
- reference-client core: 47 tests passed。
- reference-client authored source/tests: ruff green、compileall green、model/protocol smoke green。
- `auth/reference-client/web-server/libcommon`と`auth/web-server/libcommon`はbyte identical。
- 両snapshotの`VERSION` tree hashは
  `c49c15a98ef29865f3aaa6eb7663831228df68c78997c73b528d0fda2ef69b89`。

## オーナー指示・確定境界

- Cの作業場所は`auth/reference-client/`。旧`quantz-web`は初版Cでは触らない。
- citywalkその他のトラックはauth作業の対象外。他セッションの変更はGit操作時だけ明示pathで隔離する。
- vendored libcommonを直接編集しない。修正はcanonicalで行い、tagから正規bakeする。
- secretは環境変数からのみ受け取り、tracked file・log・responseへ残さない。
- Authlibは追加せず、JWTの新規依存はPyJWTだけとする。
- `revoke_all()`とsigninの同時実行競合はCへ持ち込まず、別security判断として`auth/findings.md`に残している。
- 作業を終了する前に、本ファイルへ完了範囲・green検証・未完了・次回開始点・主要コミットを更新してpushする。

## 未完了

- reference-clientのFlask app組み立てとローカルSession配線。
- `GET /auth/signin`と`GET /auth/callback`のroute統合。
- callbackでのUserInfo取得と、ID Token `sub`との完全一致検証。
- callback成功時のServicePrincipal作成、browser_context引継ぎ、Session rotation、safe `return_to` redirect。
- `POST /v1/sessions/revoke`の署名・schema・issuer・timestamp・revocation_id冪等性検証とSession全失効。
- service/auth/globalの3 logout route。defaultはglobal。
- Session cookie、複数タブ、wrong state/iss、UserInfo sub mismatch、ServicePrincipal並行初回、webhook再送のroute-level test。
- requests.Sessionを使うauth別hostとのHTTP E2E。Playwrightは使用しない。
- reference-client専用venvでのrequirements再現確認。
- 現行authのglobal logoutは、reference-client originからauth cookieを伴って安全に開始する経路がない。
  auth同一originのlogout開始経路を最小追加してからCへ接続する必要がある。
- auth outboxのpayloadは作成時`issued_at`を固定して再送するため、receiverの古いtimestamp拒否と長期再送が
  両立しない。delivery時刻を再署名する等、auth側の最小修正と契約テストが必要。
- したがってPhase 4d C全体は未完了。Iまたは旧quantz統合へ進んではならない。

## 次回の開始点

1. `CLAUDE.md`、`CLAUDE_GENERAL.md`、`.codex/GUIDELINES.md`、`auth/CLAUDE.md`、
   `auth/PROGRESS.md`、`auth/findings.md`を読み、commit `128312f`のC coreを復元する。
2. auth同一originのlogout開始経路と、outbox再送時timestampの2つの統合ギャップを、auth内の最小変更と
   negative testで解消する。
3. reference-clientのapp/sessionとsignin/callback routeをcore classesへ配線する。
4. revocation receiverとlogout 3種を実装し、Redis失敗時は成功を返さずauth outboxの再送を生かす。
5. route-level negative testsとrequests.Session HTTP E2Eを追加する。
6. reference-client専用venv、全test、ruff、compileall、pip check、全libcommon snapshot hashを検証する。
7. `auth/**`の明示pathだけをcommit/pushし、C完了条件を再監査する。

## 守る条件

- `.env`、credential、private key、webhook secret、client secretの値を読まない・表示しない・保存しない。
- callbackの`iss`からtoken/JWKS/UserInfo URLを組み立てない。開始時に選んだ信頼済み設定だけを使う。
- authorization code、code_verifier、access token、ID TokenをURL・log・永続MongoDBへ残さない。
- wrong browser context / wrong issではclient transactionを削除・変更しない。
- token交換の自動retryを追加しない。一時HTTP失敗だけtransactionをreleaseする。
- Session IDは認証成立時に必ずrotationし、`browser_context_id`だけを引き継ぐ。
- vendored snapshotのwhitespace等を直接整形しない。byte同一性を優先する。
- 共有branchでは`git add -A`、`git add .`、`commit -a`を使わず、authの明示pathだけを扱う。

## 主要コミット

- canonical libcommon `1d9fc36` / tag `v2.2.1`: Session prefix・cookie・Redis error hotfix。
- `4557ab7`: 共有worktree競合によりcitywalk題名のcommitへ含まれたauth v2.2.1再bakeと実Cookie回帰試験。
- `128312f`: reference-client scaffold、v2.2.1 snapshot、OIDC core primitives、47 core tests。
