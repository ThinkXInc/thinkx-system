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

### 2-補足. なぜこの設定が要るか・何が変わるか(2026-09-17 確認済み)

- production ブランチのルールセット `production protection`(2026-08-07 作成)は「削除禁止」「履歴の巻き戻し禁止」
  「変更は Pull Request 経由でなければならない」の 3 つ。**誰が push しても適用される**(人の git push も staging の鍵の push も、
  PR を通さない限り拒否される)。「本番に反映」が `GH013: Changes must be made through a pull request` で失敗するのはこれ。
- Mac の `deploy_production_from_staging.sh` が通るのは、直接 push ではなく `gh` で PR を作ってマージしているから。
  staging にあるのは Deploy key だけで、Deploy key は ssh の git 操作専用。PR を作る GitHub API は呼べない。
- Bypass list は「このルールを免除する相手」を**役割で**指定する。「Deploy keys」を選ぶと、鍵を 1 本ずつ選ぶのではなく
  **「Deploy key という種類の認証で来た push は通す」**という設定になる。人が自分のアカウント(個人の ssh 鍵・gh の token)で
  push した場合は Deploy key ではないので、今までどおり PR が必須のまま。
- このリポジトリの Deploy key は 2 本: `supercom-web`(2026-08-07・staging web の `/home/kaz/.ssh/deploy_thinkx-system`・書き込み可)と
  `thinkx-system-rw`(2026-07-19・旧箱の鍵・未使用 → 削除推奨)。
- **守りが一段弱くなる点**: D-50 の「PR がゲート」は staging の鍵に対しては外れる。staging の箱を乗っ取られたら production に
  push できる。受け入れる根拠は「押す=承認」(オーナー裁定 2026-09-06)と、staging の鍵が書き込み可な時点で develop/release は
  既に同じ状態だったこと。
- 確認結果(API): `rules: [deletion, non_fast_forward, pull_request]` / `bypass: [{actor_type: DeployKey, bypass_mode: always}]`(13:48 更新)。

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

1. ユーザー名を入力する(例: kobito)
```
cd ~/Sources/thinkx-system
read -r REMOTE_USER
```
2. パスワードを入力する(画面には出ない)
```
read -rs REMOTE_PASS
```
3. 本番 web の .env に書き、thinkx を再起動する(最後に `active` が出ること)
```
ssh supercom-web1 "printf 'REMOTE_BASIC_AUTH_USER=%s\nREMOTE_BASIC_AUTH_PASS=%s\n' '$REMOTE_USER' '$REMOTE_PASS' | sudo tee -a /src/thinkx/web-server/.env > /dev/null && sudo systemctl restart uwsgi_thinkx && sleep 2 && systemctl is-active uwsgi_thinkx"
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
- 2026-09-17 2-補足(バイパスの意味・影響・確認結果)を追加。
