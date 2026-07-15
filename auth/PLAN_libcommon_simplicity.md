# libcommon / simplicity 変更計画 (auth 対応)

auth サービス導入に伴う変更計画。**両リポジトリのリファクタリング時にこの計画を入力として使う。**
原則: 変更は最小。auth のために新しい抽象を作らず、既存の契約 (レスポンス3型・デコレータ積層・
Session) に auth を「乗せる」。通信の約束 (PROTOCOL.md) は auth 側が protocol 番号で守るので、
libcommon/simplicity 側にバージョン対応表は持たない (会話での結論の通り)。

---

## A. libcommon

### A-1. 【新規】`web/auth_client.py` を追加

- 内容: 同梱の `libcommon_addition/auth_client.py` そのまま。
- 各サイトが auth と話す唯一の窓口。`AuthClient.authorize_url / verify_state /
  exchange_code / get_userinfo` と `@auth_login_required` デコレータ。
- **この層は「滅多に変えない」ことが成立条件** (libcommon が各サイトに複数バージョン
  vendoring されても、この部分が同じなら全サイトが auth と話せる)。
  変更が必要になるのは protocol 2 導入時のみ、を規約として CLAUDE.md に明記する。
- 依存追加: `requests` (各サイトの requirements.txt へ)。

### A-2. 【修正・重要】`web/flask_helpers.py` のアプリ依存を外す

現状 (実測):
```python
from models.data.user import User, UnauthorizedAccessError, UserNotFoundError  # NEEDSFIX: don't depend on data.user
```
共有ライブラリがアプリ側のモデルを import している逆依存。既に NEEDSFIX と自認されている。
**auth 自身も libcommon を使うため、これが実際のブロッカーになる**
(auth の User は quantz の User と構造が違うので、この import に引きずられる)。

対処 (最小):
- `flask_helpers.py` 内で `User` を使っている箇所 (`session_helper` 等) を特定し、
  User 依存部分を **アプリ側から注入する形** に変える:
  ```python
  # libcommon 側
  _user_loader = None
  def register_user_loader(func):        # アプリの init で一度呼ぶ
      global _user_loader
      _user_loader = func
  ```
  各アプリの `init_flask_app.py` で `register_user_loader(User.find_user_by_id)` を一行呼ぶ。
- import 時 ではなく初期化時に結線されるので、モジュール読み込み順の罠も消える。
- リファクタリング全体で予定している libcommon 契約テストに
  「flask_helpers が models.data.user を import しない」を lint/テストで固定する。

### A-3. 【追記】session cookie 名の分離を規約化

auth と各サイトが同一親ドメイン (サブドメイン構成) になった場合、cookie 名が同じだと
中央セッションとサイトセッションが衝突する。
- `SESSION_COOKIE_NAME` を Config 必須キーとし、**サイトごとに固有名** を規約にする
  (auth: `thinkx_auth_session`, quantz: `quantz_session`, ...)。
- libcommon の CLAUDE.md に「cookie 名はサイト固有。共有しない。SSO は cookie 共有では
  なく PROTOCOL.md のコードフローで行う」を明記。

### A-4. 【変更なし】そのまま auth に使えるもの (確認済み)

- `web/session.py` — RedisSessionInterface / Session。auth の中央セッションにそのまま使用
  (prefix だけ `auth_session:` に変える。コード変更不要)。
- `web/http_response_formatter.py` — SuccessFormat / APIErrorFormat。protocol の
  レスポンス外形はこれに準拠済み (PROTOCOL.md §1)。
- `web/google_oauth_helper.py` — verify_token。**Google ログインは今後 auth だけが持つ**。
  各サイトの googleoauth ハンドラは移行後に削除予定 (→ C-2)。
- `cipher.py`, `locale.py`, `logger.py`, `mongomodel.py` — そのまま。

---

## B. simplicity

### B-1. 【新規】auth リダイレクトの小ヘルパ (helpers/)

サイト側 JS がログインへ誘導するときの共通処理:
- 「ログイン」ボタン → 現在ページを覚えて (query に載せて) サイトの `/auth/login` へ遷移
  → サイトのサーバが `AuthClient.authorize_url()` へ redirect。
- callback 後にサイトが元ページへ戻すための `return_to` の付与・検証 (自ドメインのみ許可)。
- 実装は数十行の helper 1ファイル。**フレームワーク層は太らせない**
  (「パッケージ層を薄く保つ」原則の対象。ページ遷移の便利関数の範囲に留める)。

### B-2. 【新規・任意】ログイン/登録フォームコンポーネント

- auth の signin.html / signup.html が使うフォーム (email / password / Google ボタン) を
  simplicity のコンポーネントとして用意。TextField / Button 等の既存基底の組み合わせで
  実現できる見込みで、新規基底クラスは作らない。
- quantz-web に既にある signup/signin ページの view_components を**そのまま auth へ移植**
  するのが最短。simplicity への昇格 (共通化) は、2つ目のサイトが同じフォームを
  必要になった時点で行う (早すぎる共通化をしない)。

### B-3. 【変更なし】中核は無変更

InputPageViewController / バリデータ / i18n はそのまま auth の画面に使える。
auth の画面は「独立したマルチページフォーム」そのもので、simplicity の実ニッチに一致する。

---

## C. 各サイト側の移行 (参考: libcommon/simplicity の外だが順序に関わる)

### C-1. サイトに足すもの (quantz-web を最初の移行対象とする)

- config: `AUTH_BASE_URL / AUTH_SERVICE_ID / AUTH_SERVICE_SECRET / AUTH_CALLBACK_URL`
- ハンドラ2本 (合計 ~40 行):
  - `GET /auth/login` → `redirect(AuthClient.authorize_url(lang))`
  - `GET /auth/callback` → `verify_state()` → `exchange_code(code)` →
    `Session.start(userinfo['user_id'])` → return_to へ redirect
- 保護したいページ GET に `@auth_login_required` を積む (@language_wrapper の直後)。

### C-2. サイトから消えるもの (完了後)

- accounts.py の users/create, users/signin, googleoauth, verify_code 系ハンドラ群
- User モデルの password / google_id / verification_code フィールド
  (User は「user_id をキーとするサービス固有データ」に痩せる)
- **注意: 既存ユーザーの移行が必要** — quantz の users コレクションから
  email/password ハッシュ/google_id を auth の users へ移す一回きりのスクリプト。
  Cipher 形式が同一なのでハッシュはそのまま移せる (再設定不要)。

### C-3. 順序 (リファクタ全体計画への組み込み)

1. libcommon A-2 (flask_helpers の逆依存解消) — **auth 着工の前提**
2. auth サービス構築 (本コード) + nginx-root に auth の conf 追加
3. libcommon A-1 (auth_client) を追加し、この状態の libcommon を各サイトへ vendoring
4. quantz-web を C-1 で接続 (既存ログインと並走可: 新ページだけ @auth_login_required)
5. ユーザー移行スクリプト → 切り替え → C-2 の削除
6. thinkx / 新サイトは C-1 のみ (最初から auth 前提)

---

## D. 決めたこと・決めていないこと

**決めたこと (会話の結論):**
- auth は apps の一つ。全サービス共通アカウント。稼働サービスとして一つだけ立つ
- 契約は PROTOCOL.md の JSON 一つ。protocol 番号を持ち、後方互換の責任は auth 側に集約
- libcommon/simplicity にバージョン対応表は持たない
- 課金の真実は Stripe。auth は billing_status 4値に丸めて配るだけ

**未決 (着工前に決める):**
- auth のドメイン (auth.thinkx.com 等) と、それに伴う nginx-root の conf
- Stripe webhook -> User.stripe_subscription_status 更新の実装 (auth 内。コアの次)
- access_token を各サイトが保存するか (現設計では exchange 時に受け取るが保存は任意)
- 既存 quantz ユーザー移行の実施タイミング
