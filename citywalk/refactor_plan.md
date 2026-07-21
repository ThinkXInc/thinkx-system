<!-- 配置: thinkx-system/monorepo/citywalk/refactor_plan.md -->

# citywalk 再構築計画書 v3.0

作成日: 2026-07-07 / v3.0 改訂: 2026-07-20
- v2.0: monorepo 移行後の前提へ全面改訂
- v3.0: (1) auth が OIDC Authorization Code Flow + PKCE(S256) の本格仕様に確定したため C-5 を全面書き換え、
  C-3 を ServicePrincipal 対応に精密化、PyJWT を依存に追加。(2) C-0c を「デモ動画=完全な正解(ground truth)」
  + アニメーションフロー・オラクル(静止画/動的/人間目視の3層)へ全面改訂。作業項目の骨格は不変。

対象: citywalk(旧 `ThinkXInc/citywalkservers`。monorepo サブディレクトリ `monorepo/citywalk/`)
実行環境の前提: Python 3.10以上、git、pip、Node.js、Git LFS(デモ動画)、実ブラウザ(C-0c のアニメ収録)。
本物のインフラ不要(fakeredis / mongomock。D-16)。ただし C-0c は実ブラウザで旧アプリを起動する(後述)。
関連文書(すべて thinkx-system 起点):
- `monorepo/docs/CITYWALK_TRACK.md`(トラック規約・上位方針)
- `monorepo/citywalk/CLAUDE.md`(リポ規範)
- **`monorepo/auth/docs/00_OVERVIEW.md`〜`05_TESTING_AND_OPERATIONS.md`(auth 認証基盤の正本仕様。C-5 の唯一の正)**
- `monorepo/docs/conventions/AXIOMS.md`(公理層)
- `monorepo/docs/COMMON_LIB_POLICY.md`(B案・D-35。vendored libcommon/simplicity の運用)
- `monorepo/docs/ROADMAP.md`(Phase 4c/4d)/ `monorepo/docs/DECISIONS.md`(D-36/D-37)

**本計画は他計画と同一セッションで扱わない(1セッション=1計画書。D-13)。**

---

## v3.0 で何が変わったか(必読)

### (A) auth が本格 OIDC 仕様に確定した

auth は簡易版(opaque token・`/v1/token/exchange`・`sub`/`entitlements` のフラット UserInfo)から、
**OpenID Connect Authorization Code Flow + PKCE(S256)** の本格実装へ確定した(auth/docs/ 全6本が正本)。
これにより citywalk が「auth を使う側(client / Relying Party)」として実装すべきものが具体化する:

- citywalk 側に **client 実装**を持つ: `ClientTransactionStore`・`AuthClient`・`IDTokenVerifier`・
  `ServicePrincipal`、およびハンドラ `/auth/signin`・`/auth/callback`・`/v1/sessions/revoke`・logout(3種)。
- **PyJWT が新規依存**(ID Token = 署名付き JWT の検証に必須。quantz で使用実績あり)。
- 人物同一性は `ServicePrincipal(issuer, subject) → local_user_id` のマッピングで表す
  (subject を直接持つのではない。C-3 で精密化)。
- 失効(global logout / password reset)は auth からの webhook で届く。`/v1/sessions/revoke` を実装し
  `Session.revoke_all` する。
- citywalk 内で書かないもの: パスワード検証・確認コード・**ID Token の発行**(検証はする)・
  authorization code / access token の発行・JWKS の発行。これらは全て auth 側。

**重要**: 本計画は auth 仕様の具体(エンドポイント名・claim 名・検証手順)を計画本文に焼き込まない。
唯一の正は `monorepo/auth/docs/`。計画は「auth/docs を正として、citywalk の client 実装を作る」と参照する。
auth 仕様が更新されたら citywalk は auth/docs に追随する(quantz と同型の client として)。

### (B) C-0c が「デモ動画=完全な正解」+ アニメーションフロー・オラクルになった

citywalk の UI はアニメーション(地図へのスポット配置モーション、パネル/メニューのスライド、画面遷移)が
本体であり、静止画スクショだけでは知覚不変を保証できない(最終フレームしか捕まえられない)。
オーナー提供の **createguide デモ動画(135秒・往時の本番の記録・主要アニメーションを全て含む)を
完全な正解(ground truth)** として据え、3層オラクルにする(C-0c 参照)。

---

## 大原則

1. **本計画は「再構築(rebuild)」である。ただし知覚不変域を持つ(オーナー明確化)。**
   二等級制:
   - **[UI不変]** — **ユーザーが見て・触って知覚する面**(見た目・レイアウト・画面遷移・操作への反応・
     文言・**アニメーションの流れ**)を変えない。**内部コード・DOM 構造・クラス名・マークアップは自由に
     変える**(そうでなければリファクタにならない)。HTML は知覚面ではなく内部表現。
     正解 = デモ動画(ground truth)+ C-0c で凍結する3層オラクル。
   - **[再構築]** — サーバ実装・ワイヤ契約・アカウントモデル・ディレクトリ構成・ビルドは意図的に変える。
     正解 = 本計画が定義する新ゴールデン(D-20 の3点セット思想)。
   等級は各作業項目に明記する。**明記のない知覚面の変更は違反**であり、内部構造の変更は歓迎される。
2. **機械オラクルが全変更に先行する(D-4)。** [UI不変]域は「デモ動画照合 + スクショ回帰 + アニメーション
   フレーム列 + jsdom 知覚特性テスト」、[再構築]域は「pytest + 新ゴールデン」を、対象に触る前に構築する。
3. **現行の canonical simplicity / libcommon(v2.1.0)に対して書く。** vendored コピーを焼き B案(D-35)で
   運用。**存在しない libcommon API を推測して書かない。** ImportError の握り潰し・hasattr 探りは禁止。
   API 面の実測典拠は monorepo 内の既存消費者(thinkx/auth の web-server)。
4. **アカウントは auth(OIDC)の単一アカウントに統一する(D-29)。** ビジネスアカウント(OrganizationMember
   による独立認証)という概念は廃止する。人物同一性は `ServicePrincipal(issuer, subject) → local_user_id`。
   一つのアカウントがユーザー機能とビジネス機能を兼ね、ビジネス機能へのアクセス権は
   organization_membership(local_user_id + organization_id + role)で表す。
   **citywalk に独自のパスワード・確認コードを新規に書かない**(認証は auth の管轄。auth/docs が正)。
5. **citywalk/CLAUDE.md が実装より先(D-25 条件2・D-26)。** 本計画同梱の CLAUDE.md を C-0b で配置してから
   実装項目に入る。
6. ブランチは monorepo の運用に従う(1論理単位=1コミット。D-14 / ROADMAP E)。
7. 依存は exact ピン(D-3)。requirements から Jupyter 系を除去し web 依存だけにする。**PyJWT を追加**(C-5)。
8. 発見事項は `monorepo/citywalk/findings.md` へ(§6)。**Security exception(D-22)は即停止・人間へ報告。**
9. **build → test の順を厳守(D-30)。** 古い dist への green は検証ではない。

---

## §1.0 稼働状態(オーナー確定事実)

**citywalk は現在一切稼働していない。** 破壊的改善が最も安い。[UI不変]の「正解」は稼働中サービスの挙動
ではなく、**オーナー提供のデモ動画(往時の本番の記録)+ 旧コードを実ブラウザで動かした知覚出力**である。
iOS テレメトリ API のワイヤ凍結も不要(消費者が未稼働のため自由に再設計)。

---

## §1 現状理解(計画作成時の実測。2026-07-07、develop HEAD)

### 1.1〜1.3(構成・サーバ・フロントの事実)

v2.0 から不変。要点:
- 旧 `citywalkservers`(develop・最終 2023-03)。submodule 2本(playbooks・**旧世代 libcommon**)は
  取り込み時に焼き込まず破棄。node_modules がコミットされている。requirements に Jupyter 系混在。
- API は独自形式(`api_response.py` の `{'error':{...}}`)。モデルは旧 `MongoBase.__structure__`。
- **二重アカウント構造**(User と OrganizationMember が独立 email/password/session、Redis db 0/1 分離)。
- フロントは coffee(heritage 9本)+ 素 JS 34本。simplicity 未使用。less/scss 併存。PNG 33枚。
- `views/business.py` に Basic 認証ハードコード(→ D-22 報告済み・C-0a で redact 裁定済み)。

### 1.4 等級の割当(v3.0 更新)

| 領域 | 等級 | 正解の定義 |
|---|---|---|
| createguide 画面のアニメーション・操作反応・地図連動 | **[UI不変]** | **デモ動画(ground truth)** + C-0c 3層オラクル |
| その他 `/business/*` 各画面の見た目・レイアウト・遷移・文言 | **[UI不変]** | C-0c スクショ回帰 + jsdom 知覚特性テスト |
| DOM 構造・クラス名・マークアップ・テンプレートの書き方 | **[再構築](知覚不変の内側で自由)** | ゴールデン照合の対象外 |
| サーバのワイヤ契約(レスポンス外形・エンドポイント) | **[再構築]** | libcommon.web 形式 + 新ゴールデン |
| アカウント/認証(User/OrganizationMember → auth OIDC client) | **[再構築]** | auth/docs 準拠の client 実装 + ServicePrincipal |
| ディレクトリ構成・ビルド・依存 | **[再構築]** | 既存サービス(thinkx/auth)同型 |
| アイコン画像(PNG→SVG) | **[再構築だが知覚同一]** | C-7 の寸法・配置不変 + スクショ回帰 |

### 1.5 計画作成時の発見事項(findings.md に転記。C-0b)

F-1〜F-8 は v2.0 から不変(node_modules / Jupyter 混在 / date_utils 二重 / errorhandler(400) pass /
分析ノート / 旧 libcommon 別系統 / coffee 二重 / メール二重化)。§1.5 の表を参照。

---

## §2 到達形(新構成)

```
monorepo/citywalk/
├── CLAUDE.md / refactor_plan.md / findings.md
├── web-server/
│   ├── main.py / config.py / requirements.txt   # requirements に PyJWT 追加(C-5)
│   ├── libcommon/                # C-2: canonical v2.1.0 vendored(B案・編集可)
│   ├── api/                      # blueprint 群(libcommon.web 形式)
│   ├── auth_client/              # C-5: OIDC client 実装(下記)。auth/docs 準拠
│   │   ├── client_transaction_store.py   # code_verifier/nonce/return_to/expected_issuer を Redis 保持
│   │   ├── auth_client.py                 # /oauth/token を叩く(PKCE code_verifier 送出)
│   │   └── id_token_verifier.py           # ID Token(JWT)を JWKS 公開鍵で検証・nonce/aud/iss 照合
│   ├── models/data/              # MongoModel。service_principal / user_profile / organization_membership
│   ├── views/
│   │   ├── src/js/               # アプリ JS(simplicity 消費側)
│   │   ├── src/js/simplicity/    # C-2: simplicity dist vendored(B案・編集可)
│   │   ├── src/less/ / templates/ / img/(SVG 基本)
│   ├── locales/
│   └── tests/
│       ├── golden/ui_legacy/
│       │   ├── ground_truth/     # C-0c: デモ動画(Git LFS)+ 抽出キーフレーム
│       │   ├── static/           # 静止画スクショ基準
│       │   └── motion/           # アニメーションフレーム列
│       ├── inventory/            # ルート・テンプレ・ECMA・PNG 台帳
│       └── CHECKSUMS
├── analytics/                    # C-8: ノート隔離
└── legacy/                       # 旧 www ツリー(完了ゲートまで温存)
```

- auth_client を citywalk 固有 `auth_client/` に置くか libcommon.web に共通化するかは C-5 着手時に auth の
  成果物(quantz 側の client 実装が libcommon に入っているか)を確認して決める。**先回りで場所を固定しない。**

---

## §3 作業項目

C-0a → C-0b → C-0c → C-1 → C-2 → C-3 → C-4 → C-5 → C-6 → C-7 → C-8 → C-10。

### C-0a monorepo 取り込みと秘密検査 [オラクル前提]

- 旧 develop HEAD 作業ツリーを `.git` 除外でコピーし `citywalk/legacy/` に配置。submodule 破棄。
- **秘密機械検査(M-4 相当)を通す。** 既知・裁定済みクラス((A)Basic認証=redact /(B)クライアント配信型
  GCP キー=残置・要リファラ制限(人間) /(C)クライアント非配信で再構築後 config 化される鍵=redact)は
  規定処理。それ以外の実秘密は D-22 で即停止・報告(値は記録しない)。
- ルート `ARCHIVE.md` に出所行を追記(旧 URL・develop HEAD SHA・日付)。
- ルート・テンプレ・ECMA・PNG の台帳を `web-server/tests/inventory/*_legacy.txt` に凍結。
- §7 の回答済み裁定を findings「前提」欄へ転記。**§7-4(データ移行)未回答のまま C-3 に入らない。**
- 完了条件: legacy 配置・秘密検査 green・ARCHIVE 追記・台帳凍結・コミット。

### C-0b 規範配置と findings 初期化

- CLAUDE.md を配置(実装より先)。findings.md 新設(F-1〜F-8 転記)。CHECKSUMS 新設。

### C-0c UI 知覚オラクル構築 **[UI不変域の床。デモ動画=完全な正解]**

**前提工事: 旧アプリを実ブラウザで起動する。** legacy を Jinja2 直レンダリングでなく本物のブラウザで
動く状態にする(開発時にローカルブラウザで起動していた実績あり)。JS とアニメーションが実際に動くこと。
起動不能/アニメが動かない場合は静止画で妥協せず D-21 で停止・報告。

**ground_truth(デモ動画):**
- オーナー提供の createguide デモ動画(135秒・1490×856・主要アニメーションを全て含む)を
  `tests/golden/ui_legacy/ground_truth/` に配置。**Git LFS で管理**(monorepo を膨らませない・M-F8 尊重)。
  LFS 不可なら停止して相談。
- 動画からキーフレーム列を決定的に抽出し連番 PNG で置く(通常 git 管理)。抽出条件を台帳に明記。
- 動画に含まれる主要アニメーション/遷移を棚卸しして findings に記録(地図へのスポット配置モーション・
  パネル/メニューのスライド・翻訳パネルの展開・画面遷移など)。これが「守るべき動きの正解セット」。

**3層オラクル:**
- (層1・静的)安定状態の静止画スクショ回帰 → `static/`。地図タイル領域はマスク(Google Maps 仕様変更の
  経時変化を許容)、他は厳密比較。
- (層2・動的)旧アプリを実ブラウザで動かし、デモ動画と同じ操作を再現してアニメーションフレーム列を
  `motion/` に凍結。**ローカル再現とデモ動画キーフレームを照合**し「ローカル環境が往時を正しく再現できて
  いる」ことを確認。判定基準は**ピクセル一致ではなくアニメーションフロー全体の一貫性**(オーナー明示:
  流れ・順序・タイミング・軌跡の一致。地図タイルの中身の経時変化は許容)。可能な数値(CSS transition の
  duration/easing・フレーム数・移動軌跡の座標列)も固定。ずれたら箇所を findings 記録して停止・報告
  (勝手に基準を緩めない。Maps 由来の許容か本物の破れかはオーナー判断)。
- (層3・人間)デモ動画・ローカル再現(・後に再構築後)を並べて再生できる形で出力し、**オーナーが全静止画 +
  各アニメーションを目視承認するまで C-1 に進まない**。承認記録を CHECKSUMS/findings に残す。
- 完了条件: 3層が凍結され green、デモ動画との照合 OK、**オーナー目視承認済み**、CHECKSUMS 記録。

### C-1 新スケルトン [再構築]

- §2 の web-server 骨格。既存サービス同型。config.py は check_config 方式(D-18)。
- 完了条件: pytest(空でも green)+ healthcheck 応答。

### C-2 vendoring(simplicity + libcommon)[再構築]

- **B案で焼く(D-35)**: libcommon v2.1.0 を実体コピー、VERSION 記録、tree_sha を既存消費者(thinkx)と一致。
  simplicity dist をコピー、VERSION 記録。build → test 厳守(D-30)。編集禁止 deny は設けない(消費に徹する)。
- 完了条件: 2 VERSION 存在・tree_sha 一致(libcommon)・CHECKSUMS 記録。

### C-3 モデル層の再構築 [再構築](auth OIDC 対応に精密化)

- 旧 `__structure__` モデルを `MongoModel` 形式へ移植: organization / content / item / history / rating /
  address / jppostal / storeinfo / enums。
- **アカウント/identity(大原則4 / D-29 / auth/docs 準拠):**
  - 旧 User・旧 OrganizationMember は新規実装しない。
  - **`ServicePrincipal`(issuer + subject の複合ユニーク → local_user_id)** を実装する
    (auth/docs 03 の quantz 側 ServicePrincipal と同型。初版は新規のみ・移行なし・突合キーにメールを
    使わない・複合ユニークインデックス必須・並行初回 callback の二重作成防止)。
  - citywalk 固有属性は `user_profile`(local_user_id をキー)、ビジネス権限は
    `organization_membership`(local_user_id + organization_id + role)。**email/password/確認コードを持たない。**
  - Organization から認証関連を外し business プロフィールに純化。
- 旧→新フィールド対応表を `web-server/docs_migration_map.md` に残す。
- 完了条件: 全モデル mongomock green。ServicePrincipal の複合ユニーク・二重作成防止のテスト green。
  対応表が旧 `__structure__` キー全量を仕分け(機械突合で漏れゼロ)。
- **前提**: §7-4(データ移行)裁定が findings「前提」欄にあること。

### C-4 API 層の再構築 [再構築](blueprint ごとにサブコミット)

- libcommon.web のデコレータ積層 + pydantic レスポンス族。私設エラーヘルパ・独自 ErrorResponse 禁止。
- 順序: C-4a contents → C-4b items+storeinfo → C-4c ratings → C-4d addresses+geo →
  C-4e histories(§1.0 により自由に再設計)→ C-4f apps → C-4g purchase(§7-3 裁定に従う)。
- **users/organizations の認証系は移植しない**(認証は auth。C-5 に集約)。廃止一覧を routes_map.md に全行仕分け。
- 完了条件: 各サブ項目で新ゴールデン凍結 + pytest green。routes_map.md が旧 67 行を全行カバー。

### C-5 auth 統合 [再構築]**(v3.0 全面書き換え — OIDC client の実装)**

規範は `monorepo/auth/docs/`(01 フロー・02 セキュリティ・03 データ/Redis・05 テスト)。citywalk は
auth/docs の「各サービス(quantz)側」に書かれた client 実装を、citywalk 用に作る。**auth/docs を唯一の正とし、
計画本文に手順を焼き込まない**(auth 仕様が動いたら auth/docs に追随)。

実装するもの(auth/docs 01 の「新規に書くもの: quantz」に対応):
- **`ClientTransactionStore`**: ログイン開始〜callback を紐付ける一時レコード(Redis、prefix
  `oidc:client_transaction:*`)。`code_verifier`・`nonce`・`return_to`・`expected_issuer`・`status` を保持。
  bind は Session ID ではなく **`browser_context_id` の digest**(Session ローテーションをまたぐ・複数タブ対応)。
  `create` / `claim_for_callback`(検証してから状態遷移・削除しない)/ `complete` / `release`。
- **`/auth/signin`**: `state`(内部名 authorization_transaction_id)・`code_verifier`・`code_challenge`(S256)・
  `nonce` を生成、transaction 保存、auth の `/oauth/authorize` へ redirect(URL は urlencode で構築)。
- **`/auth/callback`**: transaction を claim(browser_context 照合・iss 照合・pending→processing)→
  `AuthClient.exchange`(PKCE code_verifier 送出)→ `IDTokenVerifier.verify`(nonce 照合)→
  `ServicePrincipal.find_or_create(issuer, subject)` → `Session.start(local_user_id, browser_context_id=)` →
  transaction complete → `return_to`(相対パスのみ・safe_return_to)へ redirect。
- **`AuthClient`**: `/oauth/token` をサーバー間で叩く(HTTP Basic で client_secret・form encoding・
  timeout・redirect 拒否・Content-Type 検査)。token endpoint URL は callback の iss から組み立てず
  **信頼済み設定(TRUSTED_PROVIDERS)から引く**。
- **`IDTokenVerifier`**(PyJWT): `kid` → JWKS 公開鍵で RS256 検証、`aud`=client_id・`iss`・必須 claim
  (iss/sub/aud/exp/iat/nonce)・nonce 照合・azp 照合。ID Token は認証 claim のみ(email 等は /userinfo)。
- **`/v1/sessions/revoke`**: auth からの失効 webhook 受け口。署名・timestamp・issuer 検証、
  `revocation_id` 冪等、`ServicePrincipal(issuer, subject) → local_user_id` を引いて `Session.revoke_all`。
- **logout(3種)**: service_logout / auth_logout / global_logout(auth/docs 01)。UI の「ログアウト」は
  global がデフォルト。
- 画面保護: `@auth_login_required`(ローカル Session を見る)。business 画面はさらに organization_membership の
  role 検査デコレータ(api/ に1つ定義・alias 禁止)。
- Session: `libcommon.web.session` を **citywalk 所有 Redis・cookie 名 `citywalk_session_id`・prefix
  `citywalk:session:*`** で使う(auth/docs 03 の「同じクラス・別インスタンス」)。`browser_context_id` の
  引き継ぎ・Session ローテーションを守る。

禁止(citywalk 内で書かない): パスワード検証・確認コード・**ID Token の発行**・authorization code /
access token の発行・JWKS 発行・JWT(認証以外の独自 JWT)。UserInfo/ID Token を verifier 以外で解釈すること。

ローカル開発・テスト: auth のローカル/staging インスタンス(auth トラック成果物)と、auth/docs 05 の
seed コマンド・論理層テストに乗る。citywalk 側の契約テストは negative test(auth/docs 05 の client 側項目:
wrong nonce/aud/iss 拒否・PKCE・transaction の複数タブ・失効 webhook 冪等 等)を自動化する。

完了条件: 上記 client 実装の契約テスト(auth/docs 05 の client 側 negative test)green +
ログイン必須画面のアクセス制御が知覚特性テストで固定。

### C-6 フロントエンドの再構築 [UI不変]**(デモ動画照合)**

- `/business/*` 各画面と index を simplicity で再構成。coffee/旧素 JS は持ち込まない。DOM は自由に作り直す。
- **合格判定は C-0c の3層 + デモ動画照合**: 再構築後の createguide を同じ操作で撮り、**デモ動画(ground truth)
  とアニメーションフロー一貫性で照合**する。地図タイルの経時変化は許容、動きの流れ・タイミング・軌跡を守る。
  auth 化で知覚が変わる箇所(signin/signup → auth 導線。§7-7)は「意図した知覚差分」として基準を更新し理由を
  findings 記録。
- 1画面=1サブコミット。build → test 厳守。**視覚の最終確認はオーナー目視**(デモ動画・再構築後を並置)。
- 完了条件: 全画面3層一致 + createguide のデモ動画照合 OK + オーナー目視承認。

### C-7 PNG → SVG [再構築だが知覚同一]

- PNG 33枚を SVG 化(design/icons 原本)/ ベクタ化不能は PNG 維持記録 / 未使用は廃止記録。同寸・同配置。
  スクショ回帰で知覚同一を担保。完了条件: 仕分け表が33枚全量カバー + スクショ一致 + 目視1回に含める。

### C-8 分析・ML 資産の分離とインフラ移設 [再構築]

- notebooks を `analytics/` へ移設。requirements から Jupyter 除去。node_modules 除去 + .gitignore(F-1)。
  旧 www/local の nginx/uwsgi 等は monorepo/infra への移設先を記録(実配線は I トラック)。
- 完了条件: web-server が analytics/ に依存しない grep ゲート + 新 requirements で全テスト green。

### C-10 完了ゲート

- 全ゲート green: pytest(契約・規約・知覚特性・auth client negative test)/ スクショ回帰 /
  デモ動画照合 / lint / CHECKSUMS / routes_map・モデル対応表・PNG 仕分けの全量カバー / vendored tree_sha 一致。
- legacy/ 削除可否を人間に諮る。ROADMAP 更新は人間。

---

## §4 やらないことリスト

- 本番デプロイ・DNS 切替・データ移行の実行(I トラック / 人間)。
- iOS アプリ本体の改修(サーバ側の再設計のみ)。旧リポの履歴パージ(§7-1 は人間)。
- **auth サービス側の実装**(citywalk は client のみ。ID Token 発行・code 発行・JWKS は auth の管轄)。
- canonical libcommon / simplicity の破壊的変更(消費に徹する。必要なら findings → 原本へ還流)。
- レコメンド・ML の再学習。新機能追加・i18n 言語追加。
- JWT の独自利用(認証は auth の OIDC に一本化。citywalk は ID Token 検証のみ)。

---

## §5 セッション運用(実行者への指示)

1. ルート CLAUDE.md → 本計画(大原則・§1.0・§1・§4・§6)→ citywalk/CLAUDE.md → **C-5 着手前に
   auth/docs 全6本** を読む。
2. 現在地と規範ファイルの実パス・版数を宣言してから着手。
3. パスは明示列挙(D-21)。実環境と食い違ったら D-21 の修復手順。推測で進まない。build → test の順(D-30)。
4. §7-4 裁定が findings「前提」欄に転記されるまで C-3 に着手しない。他項目は依存順で先行可。
5. C-0c は**オーナー目視承認**が C-1 への関門。承認前に先へ進まない。

---

## §6 発見事項の報告ルール

- 修正せず findings.md に「ファイル:行 / 事実 / ID」で1行追記。解釈を書かない(Phase 3 の入力・D-20)。
- **Security exception(D-22)**: 秘密の疑いは即停止・人間へ報告。exploit 手順・秘密値を書かない。
  C-0a の秘密裁定クラス (A)(B)(C) は既定処理、それ以外は停止。

---

## §7 未決事項(人間の判断待ち)

1. **旧 public リポの秘匿情報(実行より先に対応推奨)。** Basic 認証・GCP キー(残置裁定・要リファラ制限)・
   分析ノート。旧リポの private 化・キーのリファラ制限は人間。取り込み側は C-0a の秘密検査で門番。
2. ~~iOS~~ → §1.0 で解決。
3. **purchase の扱い**(Stripe 移行/廃止)。→ C-4g。
4. **既存 MongoDB データの移行。** 旧 User/OrganizationMember を auth へ移すか。auth/docs 03/D-13 は
   「初版は新規のみ・移行なし」なので、移行するなら auth 側の受け入れ設計と時期を人間が決める。→ C-3 の前提。
5. **リポ名 citywalk 確定**(旧 GitHub 改名/凍結は人間)。
6. **less/scss 併存の解消**(推奨 less)。→ C-6 前。
7. **signin/signup の auth 導線化。** auth 統合で両画面は auth の `/oauth/authorize` へ redirect に置換され、
   知覚が変わる唯一の箇所。推奨: 旧レイアウトの枠を保ちつつ導線を差し替え、差分を基準更新 + findings 記録
   (C-6)。auth 側 signin 画面(既存 simplicity UI)のデザインは auth トラック管轄。

---

## §8 完了の定義

C-10 全ゲート green + §7 全項目に裁定記録 + C-0c/C-6 のオーナー目視承認。判定と ROADMAP 更新は人間。