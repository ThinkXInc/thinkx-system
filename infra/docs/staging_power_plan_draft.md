# KOBITO リモコン(本番入口 + staging 電源) 実装計画(下書き・P トラック)

作成日: 2026-09-06 / 状態: **下書き**(実行者が起こした案。オーナーが採用するときに `STAGING_POWER_PLAN.md` へ改名して正本にする)
対象: 本番 web(web1)の thinkx サイト内 + terraform(IAM) + `infra/claude_connect/index.html`(相対パス化) / 性質: 既存の運用フローを変えない追加
前提となる議論: 2026-09-06 のセッション(findings 同日)。staging 側の接続ページ(`CLAUDE_CONNECT_PLAN.md`)はそのまま残し、予備の入口にする。

## 目的

利用者(手元にソースを持たない非エンジニアを含む)が **1 つの URL・1 つの認証** で、staging の起動/停止・Claude への
接続の復旧・Claude を開く・本番への反映をすべて行えるようにする(オーナー 2026-09-06「画面と URL が 1 つにできるならその方がいい」)。

```
https://thinkxinc.com/remote/                 (本番の Flask・Basic 認証)
KOBITO(ロゴ)
┌ staging の電源 ───────────────┐   ← 本番だけに出る(電源 API が本番にしか無い)
│ ● 停止中   [ staging を起動 ]  │
└───────────────────────────────┘
┌ 接続 ─────────────────────────┐   ← staging が応答しているときだけ出る(中継)
│ ● 接続中   [ Claude を開く ]   │
└───────────────────────────────┘
┌ 本番への反映 ─────────────────┐   ← 同上
│ [ 本番に反映 ]                 │
└───────────────────────────────┘
```

## 仕組み(1 画面にする方法)

- 本番の Flask に `/remote/` を置き、**`/src/thinkx-system/infra/claude_connect/index.html` をそのまま返す**
  (本番 web にも production の checkout があるので同じファイルが読める。画面のソースは 1 つ。コピーを作らない)。
- 接続ページが呼ぶ API(`state` / `session` / `code` / `deploy`)は**相対パス**にする。staging で直接開けば `/connect/state` に、
  本番の `/remote/` で開けば `/remote/state` に飛ぶ。本番の Flask は `/remote/<api>` を `https://staging.thinkxinc.com/connect/<api>` へ
  中継する(requests 2.32.5 は thinkx に導入済み)。staging の Basic 認証は本番の `.env` に持ち、利用者には見せない。
- 電源カードは同じ index.html に足し、相対パス `power/state` が 200 を返すときだけ表示する(staging で直接開くと 404 → 隠れる)。
- staging が止まっているときは中継が失敗するので、接続・本番反映のカードは出さず、電源カードに「停止中」と「起動」だけ。
  起動後、中継が応答し始めたら同じページにカードが現れる(5 秒ごとの状態取得はそのまま)。

## 大原則

1. **新しいプロセス・unit を作らない。** thinkx の Flask(main.py)にルートを足すだけ(filedrop と同じ型。オーナー指示 2026-09-06)。
2. **本番の web に付ける AWS 権限は staging の電源だけ。** `ec2:DescribeInstances`(表示用)と
   `ec2:StartInstances` / `ec2:StopInstances`(Condition: `ec2:ResourceTag/Project = supercom` かつ `ec2:ResourceTag/Env = staging`)。
   terminate・設定変更・本番インスタンスへの操作は含めない。SECURITY.md「web: ロールなし」の**明示的な例外**として記録する。
3. **ハンドラーは入力を受け取らない。** 対象インスタンスはタグで固定し、電源のボタンは「起動」「停止」の 2 種だけ。
   中継は `state` / `session` / `code` / `deploy` の 4 つに固定(任意パスを中継しない)。
4. **本番のみ。** staging では `/remote/*` を 404(filedrop の逆。判定はホスト名 `-stg` の有無・D-46)。
5. **認証は Flask 内の Basic 認証。** `.env` の `REMOTE_BASIC_AUTH_USER/PASS`。staging の Basic 認証とは**別のパスワード**。
   中継用の staging 側の認証情報は `.env` の `STAGING_BASIC_AUTH_USER/PASS`(loadbalancer の .env と同じ値)。HTTPS のみ。
6. **IMDSv2 を必須にする**(`metadata_options { http_tokens = "required" }`)。in-place 変更で再作成は起きない(plan で確認してから apply)。
7. 依存を増やさない(boto3 1.34.122・requests 2.32.5 は thinkx に導入済み)。1 項目 = 1 コミット + push。発見は `infra/findings.md`。
8. 画面の見た目・段階表示・文言は今の接続ページを踏襲する(1 ファイル・外部アセットなし・D-69)。

## 前提(P-0 で機械確認)

- 本番 web で thinkx の venv から `import boto3, requests` が通る。`/src/thinkx-system/infra/claude_connect/index.html` が読める。
- terraform の全体 plan が No changes(差分が混ざる状態で IAM を apply しない)。
- `aws ec2 describe-instances --filters Name=tag:Env,Values=staging Name=tag:Project,Values=supercom` が staging 2 台だけを返す
  (start_staging.sh / stop_staging.sh と同じフィルタ。**本番が混ざらないことを目視**)。
- 本番 web から `https://staging.thinkxinc.com/connect/state` に Basic 認証つきで到達できる(公開経路・staging 稼働時)。
- thinkx のルートゴールデンが green。

## 配置

```
infra/terraform/iam.tf            aws_iam_role.web + role_policy(staging 電源・タグ条件) + instance_profile.web
infra/terraform/instances.tf      web に iam_instance_profile と metadata_options(IMDSv2)
infra/claude_connect/index.html   API を相対パスに。電源カード(power/state が 200 のときだけ表示)
thinkx/web-server/main.py         /remote/(index.html を返す) /remote/power/{state,start,stop} /remote/{state,session,code,deploy}(中継)
                                  Basic 認証。staging では 404
thinkx/web-server/config.py / .env   REMOTE_BASIC_AUTH_USER/PASS, STAGING_BASIC_AUTH_USER/PASS
thinkx/web-server/tests/golden/route_sweep.json   /remote/ を追加(本番 401・staging 404)
infra/docs/SECURITY.md / DECISIONS.md   例外の記録(人間)
infra/runbooks/claude-connect.md        入口が本番 /remote/ になったことと中継の説明
```

## 作業項目(実行順)

### P-0 前提ゲート
- 変更なし。前提を全部コマンドで確認し findings に貼る。いずれか不成立なら着手しない。
- コミット: `docs(infra): findings — remote preflight`

### P-1 接続ページの相対パス化と電源カード(staging 側で先に検証)
- 変更: index.html の `/connect/…` を相対(`state` 等)に。電源カードを追加し、`power/state` が 200 のときだけ表示。
  staging の server.py には `power/*` を作らない(404 のまま = 隠れる)。
- 完了条件: staging の `/connect/` が今までどおり動く(状態・再接続・コード・本番反映)。電源カードは出ない。
- 戻し方: index.html を前の版に戻す。
- コミット: `feat(infra): claude_connect page — API を相対パスに、電源カード(本番でだけ出る)`

### P-2 IAM ロールと IMDSv2(terraform)
- 変更: iam.tf に `aws_iam_role.web`(EC2 が assume)、`aws_iam_role_policy.web_staging_power`(3 操作・タグ条件)、
  `aws_iam_instance_profile.web`。instances.tf の web に `iam_instance_profile` と `metadata_options { http_tokens = "required" }`。
  .tf は両 env 共有なので staging の web にも同じロールが付く(使わないが害はない。分けるなら `is_prod` で条件化 — 決めてもらう)。
- 完了条件: `terraform fmt -check` / `validate` / `plan` が **update in-place のみ**(`must be replaced` が 1 つでもあれば止めて報告)。
  `terraform_apply.sh prod`(承認)後、本番 web で IMDSv2 トークン付きの `curl …/meta-data/iam/info` がロール名を返し、
  `aws sts get-caller-identity` がそのロールになる。
- 戻し方: 追加した resource を削除して apply(ロールを外すだけ。インスタンスは残る)。
- コミット: `feat(infra): web に staging 電源だけの IAM ロールと IMDSv2 を付ける`

### P-3 Flask ハンドラー(本番のみ・Basic 認証・電源と中継)
- 変更: main.py に `/remote/`(index.html を返す)、`/remote/power/state`(2 台の state と起動時刻)、
  `/remote/power/start` / `/remote/power/stop`(POST・引数なし)、`/remote/state|session|code|deploy`(staging へ中継。deploy は
  タイムアウト 150 秒)。boto3 は `describe_instances(Filters=[Project=supercom, Env=staging])` で対象を毎回引き、その ID だけを操作。
  ホスト名が `-stg` なら全部 404。Basic 認証が無ければ 401 + `WWW-Authenticate`。電源操作は logger に残す。
  staging が応答しないときの中継は 503 と短い理由(ページはそれを「停止中」と解釈する)。
- 完了条件: 本番で `curl -u … https://thinkxinc.com/remote/` が 200、認証なしで 401、staging で 404。
  `/remote/state` が staging の state をそのまま返す。ルートゴールデン green(追加行込み)。
- 戻し方: ルートとテンプレート参照の削除、ゴールデンの行削除。
- コミット: `feat(thinkx): /remote/ — KOBITO リモコンの本番入口(staging 電源 + 接続ページの中継・Basic 認証・本番のみ)`

### P-4 最終検証(スマホのみ)
- 停止中の staging に対して `https://thinkxinc.com/remote/` から: (a) 電源カードだけが出る → (b) 起動 → 準備中の段階表示 →
  (c) 接続・本番反映のカードが現れる → (d) Claude を開く → (e) 停止 → 電源カードだけに戻る。所要を findings に。
- コミット: `docs(infra): findings — remote end-to-end on phone`

### P-5 記録
- SECURITY.md に例外(web のロール・範囲・理由)、DECISIONS に D-xx、運用.md の STOP/START 節と Claude Code Session 節に URL、
  runbook に「入口は本番 `/remote/`、staging の `/connect/` は予備」。SECURITY/DECISIONS への追記は人間。実行者は文面を提案する。

## やらないこと

| 禁止 | 理由 |
|---|---|
| 本番インスタンスの start/stop | 権限のタグ条件で構造的に不可にする |
| terraform apply / destroy のボタン化 | 箱の生成・破壊は承認プロンプトつきの CLI に残す(オーナー 2026-09-06) |
| 任意パスの中継 | 4 つに固定。オープンプロキシにしない |
| .env の平文 AWS キーの利用 | 権限が広い。ロールで絞る |
| 常駐プロセス・unit の追加 | Flask のルートで足りる |
| 画面のコピー(thinkx 側に別の HTML) | ソースは infra/claude_connect/index.html の 1 つ。本番はそれを読んで返す |

## 決めてもらうこと(着手前)

1. SECURITY.md「web: ロールなし」の例外を認めるか(範囲は大原則 2 のとおり)。
2. 入口のパス `/remote/` でよいか(将来「リモートのソースコードをローカルに fetch」等が `/remote/…` に並ぶ想定)。
3. staging の web にも同じロールが付くことを許容するか(条件化して本番だけにするか)。
4. 本番の `.env` に staging の Basic 認証(中継用)を置くことを許容するか。
