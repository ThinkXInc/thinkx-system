# 02 — セキュリティ概念（各値は何を守るために存在するか）

`01` の各ステップに登場する値が「どの攻撃を防ぐために存在するか」を説明する。
実装中に迷ったら本ファイルの該当アンカーを参照。

全体をひとことで言えば、この設計は
**「auth だけがパスワードを扱い、その認証結果を、盗まれても・すり替えられても・偽造されても
悪用できない形で各サービスへ渡す」** ためにある。以下の各値は、そのうち 1 つの穴を塞ぐ。

---

## authorization code — 「秘密を載せない使い捨て番号」

**防ぐもの: 認証結果そのものの盗難。**

認証結果を URL に載せると履歴・ログ・Referer に残り、後で読まれると盗まれる。そこで auth は
**中身が空の引換券（code）** だけをブラウザに持たせる。実データは後で quantz がサーバー間の裏経路（⑦）で
その番号を提示して受け取る。この目的から性質が導かれる: 60 秒で消える / 一度使ったら消える / 中身が空。

---

<a id="state"></a>
## state（内部名 authorization_transaction_id）— 「なりすましログインの強要」を防ぐ

**防ぐもの: login CSRF。**

攻撃者が自分向けの code を含む callback URL を罠として被害者に踏ませると、被害者は「攻撃者のアカウント」で
ログインさせられ、以後の入力（クレカ・文書）を攻撃者が読める。対策として quantz はログイン開始時に乱数
`state` を作り、そのブラウザに紐付けて保存し（`01` ①）、callback で戻った `state` と一致しなければ拒否する。

**守るもの:「この callback は、確かにこのブラウザ自身が始めたログインの結果か」。**
実態は照合用の一時 ID なので内部名は `authorization_transaction_id`。wire 名は OAuth 予約語の `state`。

> なお、この bind は Session ID ではなく `browser_context_id` の digest で行う。理由は下の「複数タブ」。

---

<a id="pkce"></a>
## PKCE（code_challenge / code_verifier）— 「盗まれた code」を無効化する

**防ぐもの: code 自体の盗難・すり替え。**

state はブラウザを守るが、code が URL に一瞬でも現れる以上、盗難経路はゼロにできない。対策として quantz は
ログイン開始時に秘密の乱数 `code_verifier` を作り **自分のサーバー内（transaction store）にしまう**。その
ハッシュ `code_challenge = SHA256(code_verifier)` だけを auth に送り、auth は code に結び付ける（`01` ⑤）。
引き換え時（`01` ⑦）、quantz は元の `code_verifier` を送り、auth が `SHA256(verifier)` と challenge を照合する。

`code_verifier` は次のように扱われる（`04` D-18 の訂正）:
- ブラウザを通る authorization request や callback URL には **出ない**
- quantz の Redis（transaction store）に保存する
- token request で **quantz backend → auth backend へ TLS で送る**（サーバー間ログに残さないこと）

ハッシュは一方向なので challenge から verifier は逆算できない。したがって code を盗んでも、URL 経路に
出ない verifier を出せない攻撃者は引き換えられない。**守るもの:「引き換えようとしているのは、この code の
発行を始めた本人か」。** `S256` を常に必須とし、`plain` や challenge 無しを拒否する（downgrade 防止）。

---

<a id="client_secret"></a>
## client_id / client_secret — 「サービスのなりすまし」を防ぐ

**防ぐもの: token endpoint への不正アクセス。**

quantz は token endpoint を叩くとき `client_secret`（auth と quantz だけが知る合言葉）を添える。これは
**サーバー間通信でのみ使い、ブラウザには絶対渡さない**。`01` ⑦ がブラウザを経由しないのはこのため。
`client_id`＝名乗り（公開）、`client_secret`＝証明（秘密）。secret を高エントロピー乱数にして SHA-256 で
保存する理由（Argon2id でない）は `04` D-12。

---

<a id="redirect"></a>
## redirect_uri の完全一致 — 「code を攻撃者のサーバーへ送らせない」

auth は事前登録された正規 URL と **完全一致**するときだけ code を返す（`startswith` は
`quantz.example.evil.com` を通すので不可）。不正な redirect_uri には **そのURLへエラーを返さず**、auth 自身の
エラーページを出す（`01` ②）。quantz 側の `return_to` も外部 URL を許さず **サービス内相対パスのみ**
（`safe_return_to`）。オープンリダイレクタ化を防ぐため。

---

# ここから OIDC 固有（OAuth を「認証」に拡張する部分）

---

<a id="idtoken"></a>
## ID Token — 「認証結果を偽造できない証明書にする」

**防ぐもの: 認証結果の偽造。**

ID Token は **auth が秘密鍵で署名した JWT**。中に iss/sub/aud/exp が書かれ、全体に署名が付く。quantz は
auth の **公開鍵**で検証する。鍵の非対称性が本質: auth だけが秘密鍵を持つので auth だけが有効な ID Token を
作れ、quantz は検証だけできて偽造はできない。これが「サービスが auth を信頼できる」根拠であり、将来
認証を外部へ開放できる土台になる。quantz は既に JWT を使っているが、そこでは「自作・自検証」だった。OIDC は
「auth が作り、別サービスが検証する」——この分離が新しい。

**ID Token には認証 claim だけを入れる**（iss/sub/aud/exp/iat/nonce/auth_time）。email 等プロフィールや
頻繁に変わる billing 状態は入れない。理由は `04` D-08（発行直後に古くなる／責務分離）。プロフィールは
`/userinfo` から取得する。

---

## ID Token の中身: iss / aud / exp / sub

<a id="iss"></a>
### iss（issuer）— 発行元 auth の固定

このトークンを発行した auth の URL。**複数の auth instance を持つ計画がある**ため、片方向けトークンを
もう片方に持ち込む攻撃を防ぐ。混同しないよう、iss 検証は 2 箇所ある:

1. **callback の `iss` パラメータ**（`01` ⑤⑥、RFC 9207）— authorization server mix-up 対策。開始時に
   `expected_issuer` を保存し、callback の `iss` と照合してから、その issuer の token endpoint へ code を送る。
   **成功時だけでなく、有効な redirect_uri へ返す authorization error response にも `iss` を添える**（`04` D-22）。
2. **ID Token 内の `iss` クレーム**（`01` ⑧）— トークン自体の発行元検証。

<a id="aud"></a>
### aud（audience）— トークンの宛先固定

宛先サービス（`aud=quantz`）。別サービス X 向けの ID Token を盗んで quantz に出しても `aud` が X なので
弾く。複数 audience の場合は `azp`（authorized party）が client_id と一致することも確認する（`04` D-07b）。

### exp — 有効期限。盗まれても期限切れなら使えない。

<a id="sub"></a>
### sub（subject）— 不変・一意の背番号

**issuer 内で一意、かつ二度と再利用されない**識別子。メール（変わりうる）ではなく専用の `subject_id` を使う。
**ObjectId を直接 sub にしない**——DB 主キーと外部 identity を分離し、将来 pairwise subject へ進める余地を
残すため（`04` D-23）。quantz はこの `sub` を `ServicePrincipal(issuer, subject) → local_user_id` へ対応付ける。

> sub の一意性・不変・非再利用は OIDC を名乗る以上の必須契約。初版から `subject_id` 設計に組み込む。
> 後から変えると既存ユーザーの identity が壊れる。

---

<a id="nonce"></a>
## nonce — 「ID Token のリプレイ」を防ぐ

quantz はログイン開始時に nonce を作り transaction store に保存し auth へ送る（`01` ①）。auth は ID Token に
埋めて署名する（`01` ⑦）。quantz は受け取った nonce が開始時のものと一致するか確かめる（`01` ⑧）。過去に
正規発行された ID Token を攻撃者が入手しても、過去の nonce が入っているため今回の nonce と一致せず再利用不可。
**守るもの:「この ID Token は、まさに今回のこのログインのために発行されたか」。**

---

<a id="generation"></a>
## auth_generation — 「発行済みトークンの一括失効」

`User.auth_generation`（整数）を code / access token に刻む。password reset・アカウント保護・global logout 時に
インクリメントする。**利用時に generation を再検証する**（`01` ⑦ の code 引き換え、`/userinfo` の access token
利用）ことで、Redis を全走査せずに古い code / access token を無効化する。

重要な限界: これが無効化するのは「利用時に generation を再検証するもの」だけ。既にサービスへ受理され
ローカル Session に変換済みの過去 ID Token は無効化できない。その部分は失効通知（`01` の失効フロー）が担う。

> 注意: access token の失効は「record に generation を保存する」だけでは成立しない。`/userinfo` で
> **現在の User generation と実際に比較する**必要がある（`04` D-04b。当初コードはこの比較が抜けていた）。

---

<a id="browser_context"></a>
## browser_context_id — 「Session ローテーションをまたぐ複数タブ」を成立させる

**防ぐもの: 正当な並行ログインの誤破壊。**

同一ブラウザの 2 タブが同じ匿名 Session から認証を始め、タブ1が成功して `Session.start()` で Session ID が
A→C にローテーションすると、タブ2の callback は cookie C を送るのに transaction には A が保存されていて
不一致になる。単に transaction を独立キーにしただけでは、**Session ID を bind に使う限りこれは壊れる**。

対策: Session ID とは別に `browser_context_id` を持ち、**Session ローテーションをまたいで新 Session へ引き継ぐ**。
transaction には Session ID ではなくこの digest（`browser_context_hash`）を bind する。cookie/URL には出さない
ので、単独では Session を取得できず Session fixation 対策も壊さない。同じ仕組みを auth 側の認証要求にも使う。

---

<a id="csrf"></a>
## signin の CSRF token — 「login form 自体への CSRF」を防ぐ

`state` は quantz の callback を守るが、auth 自身の `POST /v1/users/signin` を守る値ではない。login form も
login CSRF の対象になり得るため、認証前 Session に CSRF token を持たせ signin POST で検証する（加えて厳格な
`Origin` / Fetch Metadata 検証）。`request_handle`（どの認可要求を再開するか）と csrf_token（この POST が
auth 画面から来たか）は別物。認証前 Session ID は認証後へそのまま昇格させず必ずローテーションする。

---

## transaction を「検証前に削除しない」理由

`01` ⑥ で transaction を `claim_for_callback`（読む→ブラウザ照合→iss 照合→pending 確認→processing へ変更、を
原子的に）してから token 交換し、成否で `complete`/`release` する。もし先に削除してから検証すると、漏れた
`state` を別ブラウザから送るだけで正規 transaction を破壊できる（DoS）し、通信失敗時に再試行できない。
`pending → processing → completed` の状態遷移で、並行 callback を 1 つだけ通す（`04` D-20）。

---

## 3 つの「照合値」の役割整理（混同しやすいので必読）

| 値 | 何と何を結ぶか | 防ぐ攻撃 |
|---|---|---|
| **state** | ブラウザ（browser_context）↔ 認証フロー | login CSRF |
| **PKCE** (verifier/challenge) | code の発行 ↔ code の引き換え | 盗まれた code の悪用 |
| **nonce** | ログイン開始 ↔ ID Token | 古い ID Token のリプレイ |

3 つとも `secrets.token_urlsafe` で作る乱数だが、守る対象が「ブラウザ」「code」「ID Token」と 3 層に分かれる。
冗長ではなく、別々の穴を塞ぐ。

---

## 2 種類のトークンがある理由（ID Token vs access token）

- **ID Token** =「この人は誰か」の証明。ログインの瞬間だけ使い、ローカル Session を開始したら役目終了。
  TTL は 5〜10 分で足りる。
- **access token** =「この人の情報にアクセスする権利」。ログイン後 `/userinfo` を叩く鍵。opaque、TTL 1 時間。

ID Token で「誰か」を確定し、access token で「後から情報を取りに行く」。OIDC の標準的な役割分担。

---

## この設計の複雑さは、すべて 1 つの要件から導かれる

> パスワードは auth だけが扱い、認証結果を盗難・すり替え・偽造に耐える形でサービスへ渡す。

code=秘密を載せない使い捨て番号 / state=ブラウザの保証 / PKCE=code の保証 / client_secret=サービスの証明 /
redirect 完全一致=宛先の固定 / ID Token=偽造不能な身分証 / iss・aud・exp・sub・nonce=各種すり替え・リプレイ
防止 / auth_generation=失効 / browser_context_id=ローテーションをまたぐ本人性 / csrf_token=login form の保護。
いずれも別の攻撃に対応する。
