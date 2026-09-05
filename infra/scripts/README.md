# infra/scripts 仕様(ゼロから再実装できる要件)

各スクリプトが「何を満たすべきか」を書く。実装ではなく要件。
これだけ見れば同じ挙動のものを書き直せることを目標にする。指示が増えたらここに追記する。

## コーディング規約は coding_guides へ
setup_*.sh の記述原則・書式・verify、観測系/変更系、bash/python の規約は
`docs/coding_guides/`(genral.md / bash.md / python.md + thinkx_coding_axioms/guide)に集約。**書く前に読む。**
本書は各スクリプトの「要件(何を満たすか)」だけを書く。

## status.sh 【観測系】
今どのインフラが立っているかを表示。
- 引数 `[staging|prod]`(既定 staging・表示用。state は単一)。
- terraform state が空 → 「未作成(何も立っていない)」だけ出して終了。
- 空でなければ:
  - AWS `describe-instances`(tag Project=supercom, Env=<env>, state=pending/running/stopping/stopped)で
    各インスタンスの name / type / state / private_ip を表示。
  - `terraform output` の LB public IP・web public/private IP。
  - 推定月額(env で固定の文言)。「stopped でも EBS 課金継続」注記。

## plan-summary.sh 【観測系】
apply 前に「構成図 + 変更 + 料金」を出す。
- **図 = 模範 `runbooks/diagram.md` を env 置換してそのまま出す**(`{env}`→env, `{1|2}`→prod=1/staging=2)。
  **箱を自作 generate しない**(模範を変えない。箱 generator は却下済み)。
- **変更の着色 = リソース単位でブロック全体を色付け**。追加=緑 / 変更=黄 / 削除=赤。
  **変更なし(no-op)は普通に出す**(色なし)。全ゼロ作成なら図全体が緑・LB 削除ならその箱が赤・
  web の type 変更ならその EC2 箱が黄。
  - 実装方針: 図の各行を名前(`supercom-<env>-lb-sg` / `-web-sg` / `-igw` / `-rt` / `-lan` / `-lb` / `-web`、
    VPC は `Name: supercom-<env>`)で判定し、**直近に入ったリソースの色を次のリソースまで各行に及ぼす**。
    色は terraform plan の `show -json` → `resource_changes.actions`(create/update/delete)。**git 差分ではない**。
  - **境界**: VPC 最外箱の閉じ(**行頭が `└`**)以降は着色を打ち切る。SES/Route53・ドメイン振り分け表・
    ストレージ・実機リスト・月額 は terraform リソースでないので**無色**にする(引きずり色バグの防止)。
- 先頭に1行サマリ `変更: +N 追加 ~N 変更 -N 削除`(変更なしは「変更なし」)+ **変更リソースの箇条書き(色付き)**。
  図に描けないリソース(IAM 等)は箇条書きだけが唯一の表示になるため必須。
- 末尾に `cost-estimate.sh` の月額。

## cost-estimate.sh 【観測系】
月額概算。ap-northeast-1 on-demand の**静的料金表**をスクリプト内に持つ(ネット不要)。
- 引数 env。`HOURS`(既定 730=24/7)、`JPY_RATE` で円換算。
- 対象: EC2(web/lb)・EBS gp3・パブリック IPv4(2024-02 以降 課金)・データ転送(100GB無料枠)・VPC等(無料)。
- 注記: EBS は停止中も課金・destroy で $0・料金は静的スナップショット。

## cost-hook.sh 【観測系】
Claude Code PostToolUse フック本体。stdin の JSON から編集対象を読み、`infra/terraform/*.tf` のときだけ
概算(cost-estimate 相当)を出す。settings から薄く呼ぶ。

## stg.py 【観測系】staging の Claude 常駐セッションと claude_connect を Mac から観測
計画書 `infra/docs/STG_OBSERVE_PLAN.md`。目的は「毎回同じ観測」を Claude Code の承認プロンプト無しで回すこと。
`python3 infra/scripts/stg.py <sub>` は settings の ask(`ssh` / `curl` 前置一致)に掛からない。python3 標準ライブラリのみ。
- **観測のみ。** send-keys / kill / restart / logout を持たない(変更系は人間が attach_claude.sh で行う)。
- **リモートで走る文字列は全て固定リテラル。** 引数で受けない(`exec <任意>` を作らない)。値引数は整数の範囲検査か
  ホワイトリスト(`--unit` は claude_connect / claude-session)に限り、置換で埋める。
- ssh は `ssh -o ConnectTimeout=8 -o BatchMode=yes supercom-web1-stg`(ログイン ubuntu・`sudo -n` 可)。
  state は `http://web1:8008/connect/state`(bind は private IP のみ。127.0.0.1 は不可。web1 は dns.tf の内部名)。
- **ログイン URL を出さない。** state の url は yes/no、pane に折れて描かれた URL は塊ごと `<url hidden>`。`--show-url` で解除。
- `check`: uptime / `systemctl is-active claude-session claude_connect nginx uwsgi_thinkx` / `sudo -n -u kaz tmux ls` と
  pane_current_command / state JSON / pane 末尾 8 行(空行・Permission 行を除く)/ 外形 `https://staging.thinkxinc.com`
  の `/` `/connect/` `/connect/state` を curl(OS の信頼ストア)で取り **401 が正常**。最終行 `OK: stg check state=<state> ...` / `FAIL: ...`。
- `watch [--interval 5] [--max 54] [--log-lines 8]`: リモート側の 1 ループで state を取り、変化時だけ `HH:MM:SSZ <state> url=yes/no`。
  connected で抜けて OK。上限到達は FAIL(最終 state を出す)。終了時に claude_connect の journal から `GET /connect/state` を除いた末尾 N 行。
- `log [--unit claude_connect] [--since-min 30] [-n 50]`: `sudo -n journalctl -u <unit> --since -<N>min -o cat`。相対時刻なので
  サーバー TZ(UTC)を意識しない。0 行なら黄色でその旨。
- `doctor`: 前提 9 件を key=value で取り期待値と照合(user=ubuntu / hostname=web1-stg / sudo=ok / tz=Etc/UTC /
  listen=192.168.2.11:8008 / web1=192.168.2.11 / 両 unit enabled / state_http=200)。1 件でも NG なら
  `FAIL: ... stg.py の定数と infra/findings.md を更新`。staging 再構築後に最初に叩く。
- 戻り値 0/1(`sys.exit(main())`)。ssh 不達(rc 255)は `FAIL: stg <sub> ssh 到達不可(staging 停止中?)`。引数無しは使い方を出して 1。
- 昇格ルール: 同じ形の ssh/curl 調査を 3 回書いたらサブコマンドに足す(計画書改訂→オーナー承認)。1 回きりは素の ssh で承認 1 回。

## setup_user.sh 【変更系】
RUN_USER 前処理(`docs/user_setup.md` 準拠)。ssh で各 EC2 に流す。
- `RUN_USER`(既定 kaz)を作成 → repo ごとに read-only Deploy key を `~<user>/.ssh/deploy_<repo>` に生成 →
  `~/.ssh/config` に host 別名(`github-<repo>` / IdentitiesOnly yes)→ 公開鍵を表示。冪等。
- `REPOS` で対象(web=`thinkx kazukiotsuka` / lb=`loadbalancer`)。手動: 表示 pub を GitHub Deploy keys 登録。

## setup_webserver.sh 【変更系】web(supercom2)構築
原本 `docs/raw/🌲Setup Supercom2 (Web server).md` を同 OS(Ubuntu22.04)へ**ほぼ忠実に**流す(1スクリプト=1サーバー種別)。
`ssh ubuntu@<web> 'bash -s' < setup/setup_webserver.sh`。前提: setup_user.sh 済み(冒頭 guard)。
- ミドルウェア(原本忠実): essential packages・**Python 3.9.6 ソースビルド**・redis-tools・**Node(apt npm → n stable)**+ globals(@babel/cli・npm-run-all・gulp-cli 等)・nginx・git-lfs。
- **既定オフ**(infra/CLAUDE.md #5=静的サイトに不要。コメントで残し有効化可): Docker/MongoDB/Qdrant/vectordb/rabbitmq/autoenv/.env平文鍵。
- app: clone thinkx/kazukiotsuka(Deploy key host 別名)→ venv(python3.9・--without-pip+get-pip)+依存 → front build → uwsgi(unix socket)→ nginx → 起動。
- ★F4: 本番 web nginx(8005)配線は実機照合後(setup/nginx/thinkx.conf は再構成ドラフト)。

## setup_loadbalancer.sh 【変更系】LB(supercom3L)構築
原本 `docs/raw/⭐️【Summary】supercom3L setup.md` を忠実に。`WEB_IP=<web_priv> ssh ubuntu@<lb> 'bash -s' < setup/setup_loadbalancer.sh`。
- ミドルウェア: iftop/sysstat/nload/traceroute・nginx・screen・multitail・certbot(+dns-route53)・/run/nginx 権限・sslgroup/serveradmins。
- app: clone loadbalancer → conf.d の backend IP を WEB_IP へ sed → 証明書(prod=certbot --dns-route53 / **staging=自己署名**)→ nginx 起動。

## フロー
`setup_user.sh(kaz + Deploy key・要手動 GitHub 登録)→ setup_webserver.sh / setup_loadbalancer.sh`。
各 setup が原本忠実にミドルウェア + app を一括で入れる(env-setup のような分離はしない=オーナー裁定)。

## web-smoke.sh / lb-smoke.sh 【変更系】
(参考・現方針は実 setup)鍵不要の最小経路検証。nginx ダミー 200 を web:8005 / LB:80→web で疎通確認。
