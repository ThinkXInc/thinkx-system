# thinkx-system/infra/docs/KOBITO_セットアップ手順.md
#
# KOBITO サーバークラウド(リモコン /remote_control/ と接続ページ /connect/)を使うために、
# リポジトリの外で手で行う設定を全部ここに集める。GitHub の画面・AWS・サーバーの .env が対象。
# KOBITO を導入するユーザー全員が同じ手順を踏むので、迷わない粒度で書く(オーナー指示 2026-09-17)。
# 同じ仕組みを使うのに必要な設定が新しく出てきたら、この文書に追記する。
#
# 前提: infra/docs/構築手順.md で staging と本番の 2 環境が建っていること。
#

## 1. GitHub: staging の Deploy key に書き込み権限(1 回)

staging の web が develop / release / production へ push するための鍵。読み取り専用だと「本番に反映」が release の push で止まる。

1. staging の web で公開鍵を表示する
```
cd ~/Sources/thinkx-system
ssh supercom-web1-stg 'sudo -u kaz cat /home/kaz/.ssh/deploy_thinkx-system.pub'
```
2. GitHub のリポジトリ → Settings → Deploy keys → Add deploy key
3. Title: `supercom-web` / Key: 上の公開鍵 / **Allow write access にチェック** → Add key
4. 確認(Mac から。`read_only=false` が出ること)
```
cd ~/Sources/thinkx-system
gh api repos/ThinkXInc/thinkx-system/keys --jq '.[] | "\(.title)\tread_only=\(.read_only)"'
```

## 2. GitHub: production ブランチのルールセット(1 回)

人の操作は PR 経由に限定し、staging の鍵(=「本番に反映」ボタン)だけを通す。

1. GitHub のリポジトリ → Settings → Rules → Rulesets → New ruleset → New branch ruleset
2. Ruleset Name: `production protection` / Enforcement status: Active
3. Target branches → Add target → Include by pattern → `production`
4. Rules で次の 3 つにチェック: Restrict deletions / Block force pushes / Require a pull request before merging
5. **Bypass list → Add bypass → 「Deploy keys」を選ぶ → Add selected**(これが無いと「本番に反映」が `GH013: Changes must be made through a pull request` で失敗する)
6. Create(既存なら Save changes)
7. 確認(Mac から。`pull_request` と、bypass に `DeployKey` が出ること)
```
cd ~/Sources/thinkx-system
gh api repos/ThinkXInc/thinkx-system/rulesets --jq '.[] | "\(.id)\t\(.name)\t\(.enforcement)"'
gh api "repos/ThinkXInc/thinkx-system/rulesets/$(gh api repos/ThinkXInc/thinkx-system/rulesets --jq '.[] | select(.name=="production protection") | .id')" --jq '{rules: [.rules[].type], bypass: [.bypass_actors[].actor_type]}'
```

### 2-補足. なぜこの設定が要るか・何が変わるか(2026-09-17 の説明。Evernote「KOBITOセットアップ」からそのまま転記。下線は原文の下線)

**今の状態**

<u>GitHub の production ブランチには「production protection」というルールセットが効いています(2026-08-07 作成)。中身は 3 つで、「削除禁止」「履歴の巻き戻し禁止」「変更は Pull Request 経由でなければならない」です</u>。
このルールは「誰が push しても」適用されます。<u>人が git push しても、staging の鍵で push しても、**PR を通さない限り拒否されます**</u>。今回「本番に反映」ボタンが `GH013: Changes must be made through a pull request` で失敗したのはこれが理由です。
Mac から動かす <u>deploy_production_from_develop.sh が通るのは、直接 push ではなく gh コマンドで PR を作ってマージしているからです。</u>

**ボタンが通らない理由**

staging の web にあるのは Deploy key(GitHub 上の名前 supercom-web)だけです。Deploy key は ssh での git 操作専用で、PR を作ったりマージしたりする GitHub の API は呼べません。だからボタンは「PR を通す」ことができず、直接 push しかできない。その直接 push がルールで拒否される、という構図です。

**「バイパスに Deploy keys を加える」とは**

ルールセットには「このルールを免除する相手」を指定する Bypass list があります。ここに「Deploy keys」を加えると、Deploy key で認証した push に限って「PR 必須」のルールが免除されます。
- staging の鍵(supercom-web)での push → PR なしで production に入る → ボタンが動く
- オーナーや他の人が自分のアカウントで push → 今までどおり PR が必須のまま
- 削除禁止・巻き戻し禁止は Deploy key に対しても残るので、production を消したり履歴を戻したりは相変わらずできません

**何が変わるか(正直な評価)**

<u>D-50 で「PR がゲート」としていた仕組みは、staging の鍵に対しては外れます。つまり staging の箱を乗っ取られたら production に push できる、という意味では守りが一段弱くなります</u>。ただしオーナーが「ボタンを押す＝承認で、非エンジニアが使う」と決めた時点で、staging から本番へ出す経路を認めることになっているので、それと整合する設定です。秘密(トークン)を増やさずに済む点で、他の 2 案より単純です。

**「Add bypass → Deploy keys」が何をしているか**

<u>ルールセットの Bypass list は「このルールを免除する相手」の一覧で、相手は「役割」で指定します</u>(例: リポジトリ管理者、特定のチーム、特定のアプリ、そして Deploy keys)。<u>「Deploy keys」を選ぶと、このリポジトリに登録されている Deploy key で認証して来た push は、PR 必須のルールを免除する、という設定になります</u>。<u>**鍵を 1 本ずつ選ぶ形ではなく、「Deploy key という種類の認証で来たものは通す」という指定**</u>です。

**Deploy keys があれば通す、ということか**

そうです。ただし<u>「Deploy key で認証した push」に限ります。人が自分の GitHub アカウント(ssh の個人鍵や gh の token)で push した場合は、Deploy key ではないので今までどおり PR が必須のままです</u>。免除されるのは「PR 必須」のルールだけで、「削除禁止」「履歴の巻き戻し禁止」は Deploy key に対しても効き続けます。

**その Deploy key は staging サーバーの鍵か**

はい。<u>このリポジトリに登録されている Deploy key は 2 本で、supercom-web(2026-08-07、staging の web の /home/kaz/.ssh/deploy_thinkx-system、書き込み可)と thinkx-system-rw(2026-07-19、旧箱の鍵で今は使われていない)</u>です。「本番に反映」ボタンは staging の web 上で動き、この supercom-web の鍵で push するので、バイパスの対象になります。
補足として、thinkx-system-rw は旧箱と一緒に消えた鍵の登録だけが GitHub に残っているものです。バイパスは「Deploy keys 全部」に効くので、使っていない鍵の登録は削除しておくのが安全です(削除は GitHub の Settings → Deploy keys から。オーナー判断です)。

確認結果(API・2026-09-17 13:48): `rules: [deletion, non_fast_forward, pull_request]` / `bypass: [{actor_type: DeployKey, bypass_mode: always}]`

## 3. AWS: 本番 web に staging 電源用の IAM ロール(1 回・terraform)

リモコンの「staging を起動/停止」が使う。権限は staging(タグ Project=supercom, Env=staging)の describe / start / stop だけ。
定義は `infra/terraform/iam.tf`(prod のみ count で作る)と `instances.tf`(web に profile と IMDSv2)。

1. plan と apply(承認プロンプトで `3 to add, 1 to change, 0 to destroy` を確認して yes)
```
cd ~/Sources/thinkx-system
bash infra/scripts/terraform_apply.sh prod
```
2. 確認(本番 web でロール名が出ること)
```
cd ~/Sources/thinkx-system
ssh supercom-web1 'TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60"); curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/info | grep -o "supercom-prod-web"'
```

## 4. 本番 web の .env: リモコン入口の Basic 認証(1 回)

`https://<本番ドメイン>/remote_control/` を開くときのユーザー名とパスワード。staging の Basic 認証とは別にする。
書き先は thinkx の clone ルートの `.env`(`/src/thinkx/.env`。`web-server/.env` ではない)。スクリプトが対話で聞き、
既存の値は置き換え、thinkx を再起動し、本番 URL に認証つきで 200 が返ることまで確認する。

```
cd ~/Sources/thinkx-system
bash infra/etc/push_remote_auth.sh supercom-web1
```

## 5. staging LB: 本番 web からの中継を通す(リポジトリ内・自動)

`loadbalancer/conf.d/staging.thinkxinc.com.conf` の `location /connect/` に本番 web の固定 IP(`allow 57.182.151.177`)が
書いてある。本番 web の EIP が変わったらこの行を直す(EIP は台帳 D-53 で固定なので通常は変わらない)。deploy で反映される。

## 6. 動作確認

1. staging を停止した状態で `https://thinkxinc.com/remote_control/` を開く(手順 4 の Basic 認証)→ 電源カードだけが出る
2. 「staging を起動」→ 段階表示が「準備完了」になる → 接続と本番への反映のカードが現れる
3. 「Claude を開く」でチャット画面が開く
4. 「staging を停止」→ 電源カードだけに戻る

## 変更履歴

- 2026-09-17 新設。1(書き込み鍵)・2(ルールセットと Deploy keys のバイパス)・3(IAM ロール)・4(.env)・5(LB)。
- 2026-09-17 2-補足を Evernote の説明の原文どおりに置き換え(圧縮しない・オーナー指示)。
- 2026-09-17 4 を push_remote_auth.sh に置き換え(宛先の誤り `/src/thinkx/web-server/.env` → `/src/thinkx/.env`・貼り付けの折り返し対策)。
