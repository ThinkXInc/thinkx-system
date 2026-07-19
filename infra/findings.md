# infra findings

作業中に気づいた点を随時追記。日付 / 該当 / 事実 / 対応方針。

## 2026-07-15 I-STEP2 開始要求 → 前提未達で停止(着手せず)

I-STEP2(本番カットオーバー)の開始要求を受けたが、規範(ROADMAP I-STEP2 / infra/CLAUDE.md
承認点)が定める**前提が未達**のため terraform に着手せず停止・報告した。実測した事実:

- ~~**2026refactor→master マージ未実施 / v2.1.0 タグ不在**~~ → **これはブロッカーではない(訂正)**。
  「2026refactor→master + v2.1.0」は infra/CLAUDE.md の **polyrepo 時代の記述**で、各サイト個別リポの
  master/タグを指す。monorepo 集約後は個別リポをデプロイしないため無効(**doc drift**)。
  monorepo 時代の正規前提は ROADMAP I-STEP2「M 完了 + staging で monorepo 稼働・全ゴールデン green」で、
  master マージは含まれない。prod デプロイ ref はオーナー指示どおり **thinkx-system の monorepo ブランチ**
  (存在・push 済み)。→ infra/CLAUDE.md 制約2/承認点 L78 の「master 前提」文言は要更新(I-STEP2b で反映)。
- **構造所見(M トラック整地課題・I-STEP2 の障害ではない)**: thinkx-system の `master`(docs 系統・8 commits)と
  `monorepo`(取り込み系統・4 commits)は **共通祖先ゼロ=無関係な orphan 履歴**(`git merge-base` 空)。
  MONOREPO_PLAN M-1 は「monorepo を master に載せる」想定だったが実際は orphan `monorepo` に落ちている。
  GitHub 既定 base も master。要オーナー判断(M トラックで整地)。
- **M トラック未完了**(MONOREPO_PLAN の M-0..M-7 全て未チェック・完了判定「M-5 sweep green + M-6 push
  + ARCHIVE 全行」未確認。既知: M-4 で discord webhook env 化 + 秘密ローテ保留)。
- **staging で monorepo 未稼働**(monorepo は staging で一度も run されていない。全ゴールデン green の
  実績なし)。既存 staging は I-STEP1 昇格版(旧デプロイ)。
- **既知ブロッカー F4 未解消**: prod web nginx 設定が repo に無い(要オンプレ回収・実機照合)。
  未解消のまま acceptance(8005 curl golden sweep)は web 層で失敗する。
- **秘密・状態の不在**: terraform 未 init(`.terraform` 無し)・tfstate/tfvars/creds/cert/.env は
  git に無く読み取りも禁止。prod plan は AWS creds + backend/state が要る → 値を推測・生成せず人間の投入待ち。

### 追記 2026-07-15 前提の訂正と prod plan 実行(green)
- 上記の「master マージ」「staging monorepo green」は**どちらも撤回**(前者=polyrepo 時代 doc drift、
  後者=ROADMAP L58 が L61/L69 の「prod first・staging は手本」と矛盾。オーナー裁定で prod 先行)。
- `my_office_ip` は tfvars を読まず **稼働 staging SG + 端末 egress の二経路で回収 → `153.195.60.70/32`** に確定。
  三重一致(staging SG lb/web・checkip・オーナー「staging と一緒」)。`123.226.234.127` は supercom 実機の
  GIP=本移行で廃止対象、SSH 許可に使わない。
- **⚠️ my_office_ip は動的(ルーター端)。変わると新 prod 箱から SSH 締め出し**。対処を I-STEP2b で用意:
  SG の 22 許可 CIDR 更新 runbook、または SSM Session Manager で 22 を塞ぐ(改善候補・人間判断)。
- `terraform init` + `terraform plan -var=env=prod -var=my_office_ip=153.195.60.70/32` 実行 →
  **Plan: 19 add / 0 change / 0 destroy**(VPC/subnet/IGW/RT/RTA・lb(t3.small,20GB)/web(t3.medium,50GB)・
  EIP×2・SG×2・IAM role+profile(lb, route53 for certbot dns)・Route53 private zone supercom.internal + web1/lb1・
  DHCP options。AMI ami-07ee404670b78454a Ubuntu 自動選択)。既存 staging 不触(名前/CIDR 分離)。
- **apply 時前提**: EC2 キーペア **`supercom-key`** が account 027421896362 に既存であること(staging も使用 → 存在見込みだが未確認)。
  無ければ apply 失敗。cert/.env は setup 段で必要(未投入)。
- 本セッションは S トラック(サイト config.py マスク修正 c362d92/079f6ec)を既にコミット済み。
  同一セッションで I-STEP2(I トラック大工程)へ跨ぐのは「1セッション=1計画書」に抵触。I-STEP2 は
  独立セッションで開始すべき。
- `aaf43e0 update settings for monorepo`(settings.json -54/+22)が push 済み。CLAUDE.md/infra 禁止事項
  「settings 自体を書き換えない」との整合は人間確認事項として残す。

## 2026-07-12 環境セットアップ設計レビュー(docs/raw 原本 + 実リポジトリ照合)

### F1 Git 認証(🔴ブロッカー)
- 原本(`【作成済】supercom3_ git.md`): 各マシンで `ssh-keygen -t ed25519` → pubkey を GitHub **アカウント** Settings>SSH keys に**手動登録**。repo deploy key ではない。HTTPS/PAT 不使用。鍵は `/home/kaz/.ssh/id_github`、`~/.ssh/config` Host github.com。
- fresh EC2 は鍵ゼロ。EC2 既定ユーザ `ubuntu` だが鍵/サービスは `User=kaz` 前提 → ユーザ不一致。
- 対応: 鍵方式を決定(下記いずれか)。(a) EC2 で生成+pubkey を GitHub 手動登録[原本準拠・推奨] (b) 既存秘密鍵を Mac→EC2 配布 (c) repo deploy key。clone を ubuntu/kaz どちらで走らせるかも決める。

### F2 LB nginx は証明書が無いと起動しない(🔴ブロッカー)
- 実物 `loadbalancer/nginx.conf` は `include conf.d/*conf`。各 443 server が下記 cert を参照:
  - `/etc/letsencrypt/live/thinkxinc.com/{fullchain,privkey}.pem` … thinkxinc.com, nntm.thinkxinc.com, quantz.thinkxinc.com
  - `/etc/letsencrypt/live/nntmapp.com/…` … nntmapp.com
  - `/etc/letsencrypt/live/truetechjapan.com/…` … truetechjapan.com
  - `/etc/letsencrypt/live/transformism.art/…` … transformism.art
  - `/etc/letsencrypt/live/kazukiotsuka.com/…` … kazukiotsuka.com
  - `/etc/ssl/certs/jessicas.online.crt` + `/etc/ssl/private/jessicas.online.key` … demosites.conf(自己管理・デモ)
- staging は DO_CERTBOT=no で cert 不在 → `nginx -t` 失敗 → LB 起動せず → 手順3(https)不可。
- 対応: staging は上記パスに自己署名を生成して起動可にする、または conf.d を対象サイトだけに絞る(demosites/transformism/quantz/nntmapp を除外)。

### F3 Python 3.9.6 ソースビルド(要約版設計の取りこぼし)
- 原本は全 docs で `Python-3.9.6.tgz` をソースビルド + `python3.9 -m venv`(3.10 は皆無)。native ext は 3.9 向けにビルドされている(例: celery doc の torchaudio .so が python3.9 パス)。
- 現 web-setup は system `python3`(22.04=3.10)→ 不整合。
- 対応: web-setup を 3.9.6 ソースビルドに合わせる(オーナー方針: ソースビルドは必須・コマンド固定)。3.10 へ上げるのは要判断。

### F4 uwsgi は unix socket / web も nginx 必須
- 原本: uwsgi は `unix:/tmp/uwsgi_*.sock`。TCP 800x を listen するのは **web 側 nginx**(socket へ proxy + `views/` 静的配信)。
- 現 web-setup の web nginx リンクは `if [ -f … ]` 頼みで弱い。無ければ 8005 が返らない。スモーク `curl localhost:8005` は web nginx が立って初めて成立。
- 対応: web nginx.conf/service の設置・起動を確実化。thinkx `web-server/nginx/nginx.conf` を要取得・照合。

### F5 ポート/backend 実態(LB nginx.conf 実物)
- backend は主に `192.168.1.8`。port map: 8005=thinkxinc/nntmapp/truetechjapan/nntm(共有 uwsgi_thinkx)、8006=transformism、8007=kazukiotsuka、8000/8001/8009=quantz(.8/.9/.7・対象外)。
- web SG は LB SG から 8000-8009 許可済み → 網羅。

### F6 lb-setup の sed は `.8` のみ置換
- 現 lb-setup は `192.168.1.8 → WEB_IP`。対象サイト(thinkx/kazukiotsuka/truetech=.8)は妥当。
- ただし demosites=`192.168.1.11`、quantz stream/files=`.9/.7`、experiment=`.21` は置換対象外。staging 対象サイトのみなら可。conf.d を絞れば無害化。

### F7 私の暫定編集
- web-setup を Node NodeSource 18 に変更済み。原本は `apt npm`+`n stable`(未ピン)→ 相違。CLAUDE.md「Node 18+」には沿う。ピンするか原本踏襲か要判断。
- lb-setup の ref を strict 化(`|| master` 撤去)→ CLAUDE.md #2 準拠・維持推奨。

### 判定
方向性は妥当(トポロジ/意図的相違=libcommon vendoring・dns-route53・MongoDB 不要 は正しい)。ただし F1/F2 が片づき、F3/F4 を原本準拠に直すまで apply 保留を推奨。thinkx の web nginx.conf は未取得。

## 2026-07-12 決定: git 鍵方式 → 正本 `infra/docs/github_deploy_key.md`(D-1/D-2/D-3)
- **D-1** 方式 = (c) Deploy key(read-only・repo 単位)。setup の clone URL を host 別名へ。
  実装済: web-setup(`github-thinkx`/`github-kazukiotsuka`/`github-transformism`)、lb-setup(`github-loadbalancer`)。
- **D-2** 登録は手動ブラウザ・自動化しない(PAT/SSM/IAM は割に合わない)。
- **D-3** I-STEP1 リハーサルは鍵不要(ダミー静的ページで経路検証)。鍵は I-STEP2 直前に生成・登録。
  → `setup/web-smoke.sh` / `setup/lb-smoke.sh`(鍵レス・TLS なし)で疎通確認。
- **F1 解決(オーナー裁定 = kaz)**: clone は `sudo -u kaz` のまま。Deploy key と `~/.ssh/config` は
  **kaz 側 `/home/kaz/.ssh/`** に置く。サービスも `User=kaz` で整合。
- **正本追加 `infra/docs/user_setup.md`(RUN_USER 前処理)**: 全 EC2 は ubuntu 以外の RUN_USER で統一
  (既定 kaz・パラメータ化)。手作業は `sudo -u "$RUN_USER" -H` + 絶対パス。setup の前段アタッチメント。
  - **D-4 実装済**: web-setup / lb-setup に「clone 前ガード = `/home/$APP_USER/.ssh` の鍵・config が
    無ければ明示停止し user_setup.md を案内」を追加。
  - **lb-setup を RUN_USER=kaz に統一**(旧: ubuntu)。ユーザ作成・`/src` を kaz 所有・`sudo -u kaz` で clone。
- 注意: thinkx の playbooks submodule が別 repo なら playbooks 用 Deploy key/alias も要る(.gitmodules を実機確認)。
- 別途 F2(LB 証明書)・F3(Python3.9.6)・F4(web nginx.conf)は実 setup 実行前に要対応。

## 2026-07-12 実装: F2/F3 + ssh 鍵 + 図の plan 由来化
- **F2 実装**: lb-setup の DO_CERTBOT=no(staging)分岐で、loadbalancer/conf.d が参照する ssl_certificate パス
  (`/etc/letsencrypt/live/{thinkxinc.com,nntmapp.com,truetechjapan.com,transformism.art,kazukiotsuka.com}/`,
  demosites の `/etc/ssl/certs/jessicas.online.crt`)に**自己署名を生成**→ `nginx -t` が通り nginx 起動可。手順3は -k で検証。
- **F3 実装**: web-setup で **Python 3.9.6 をソースビルド**(原本の configure/make/altinstall)+ venv を
  `python3.9 -m venv --without-pip` + get-pip に変更。system python3(3.10)は使わない・上書きしない。
- **ssh 鍵**: outputs.tf(ssh_lb/ssh_web/setup_hint)と step1-rehearsal.md 手順2を `ssh -i ~/.ssh/supercom.pem` に統一。
- **図の plan 由来化**: plan-summary.sh は diagram.md 静的テンプレを廃し、`terraform show -json` の実値から構成図を
  生成・リソースごとに +緑/~黄/-赤/淡色。変更検出=terraform plan(git 差分ではない)。手順1に `terraform state list`(現状確認)を追加。
- **残 F4**: thinkx `web-server/nginx/nginx.conf` は未取得(8005 配信の確定は実機 or 取得で)。

## 2026-07-12 terraform 実行ユーザの実態
- terraform / aws CLI(Mac)の認証は IAM ユーザ **`transcript-deployer`**(account 027421896362)。
  EC2/VPC 系権限はあるが **iam:\* が無い** → iam.tf(D-22 の LB ロール)の apply が 403。
- EC2 インスタンス側の IAM は D-22 以前は皆無(certbot --dns-route53 が動かなかった根因)。
- **出自調査**: `transcript-deployer` は workspace 全 docs(raw 34 本含む)に言及ゼロ = 文書化されずに
  作られた。名前と時期(Transcript Scraper Machine Setup, 2023-10)から scraper デプロイ用のアドホック作成と推定。
- **削除可否**: 即削除は危険。(1) Mac の terraform/CLI がこのユーザで稼働中(sts で確認済み)。
  (2) オンプレ .env の平文キー(<REDACTED-AWS-KEY-ID>=supercom2/3a/quantz、<REDACTED-AWS-KEY-ID>=3c)が
  同一アカウント。**同ユーザのキーかは iam 権限が無く未確認**(管理者がコンソールの
  Users > transcript-deployer > Access keys と Last used で要確認)。SES 送信がこのキーなら削除で本番メール停止。
- **方針(オーナー)**: IAM ユーザ `supercom` を新設し移行 → transcript-deployer は使用実態ゼロを確認後に削除。
  IAM の正式ドキュメントはオーナーが別途用意。transcript-deployer 参照のソース/doc は存在しないため名称置換は不要。
  Mac 側 ~/.aws の差し替えと .env キーの扱い(ロール化 D-22)が移行の実作業。
- **確認結果(コンソール・2026-07-12)**: .env の 2 キーは transcript-deployer に**無い**(別ユーザ所有)
  → 削除してもオンプレ SES は壊れない。使用実態: IAM/EC2=今日(=terraform)、S3=904日前(scraper 残骸)、
  ELB/CW/ASG=なし。現行ポリシーは S3FullAccess / EC2FullAccess で広すぎ。
- **完了(2026-07-12 夜)**: supercom 移行済み(sts=user/supercom)。iam.tf apply 成功
  (+role/policy/instance_profile、lb へ in-place 付与。途中 `iam:TagInstanceProfile` 不足で 403 → ポリシーに追加して解消)。
  LB メタデータで `supercom-staging-lb` 確認。**certbot --dns-route53 --test-cert で thinkxinc.com の発行成功**
  = D-22 チェーン実証完了。transcript-deployer は削除可能な状態(削除実施は未確認)。
- **certbot の躓き(記録)**: (1) certbot 未導入 → apt で導入。(2) `python3-certbot-nginx` が入っており
  **`python3-certbot-dns-route53` が未導入**で "plugin does not appear to be installed" → 正しくは
  `sudo apt-get install -y certbot python3-certbot-dns-route53`(setup_loadbalancer.sh に要記載)。
  (3) sudo 無し実行は lock で Permission denied(常に sudo)。
- **TLS 自動更新**: apt 版 certbot の **systemd timer(certbot.timer)が標準で有効**(1日2回 renew・
  dns-route53 設定は renewal conf に保存済み・認証は IAM ロール)= 更新は無人。
  **残り**: 更新後の nginx reload 用 deploy hook(`/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh`)を
  setup_loadbalancer.sh に追加(旧 cron 案は timer と二重になるため hook 方式を推奨)。
  prod 移行時は --test-cert を外して再発行(既存 test 系譜の置換に --force-renewal が要る点に注意)。
- **needrestart 対話**: apt 中の「Daemons using outdated libraries」は無人実行を止める →
  setup_*.sh 冒頭の `export NEEDRESTART_MODE=a` で抑止(3本とも導入済み)。
- **ssh 別名**: Mac の ~/.ssh/config に supercom-lb / supercom-web(staging は一時 IP のため再作成時に HostName 更新)。
- **supercom ユーザの権限セット(確定案)**: inline 2本のみ — `supercom-terraform-ec2`
  (ec2:* を ap-northeast-1 限定 + Project=supercom タグ無しリソースの terminate/削除を明示 Deny)+
  `supercom-terraform-iam`(iam:CreateRole 等を role/supercom-* に限定 + PassRole は EC2 サービス限定。
  **iam:TagInstanceProfile / UntagInstanceProfile も必要** — instance profile にも default_tags が付くため。
  初版に抜けており apply が 403 になった)。
  S3/ELB/ASG/CW は付けない。移行順: supercom 作成 → Mac ~/.aws 差し替え → sts/plan 確認 → apply →
  transcript-deployer 削除(旧 role/transcript も残骸なら削除)。

## 2026-07-15 セッション終了時の現在地(次セッション復元用)
- **稼働**: staging.thinkxinc.com(Basic 認証 user=thinkx / pass は loadbalancer/.env)= LB→web1→uwsgi_thinkx(2026refactor)200・動画表示 OK。
- **.env 移行済み**: `.env` は `<site>/.env`(サイト clone ルート)。配布は **push_env.sh**(.env)/ **push_assets.sh**(video)/ **push_secrets.sh**(certs/deploykeys)の**3本分離**(D-14/D-40/D-41…)。infra/env は廃止。
- **問い合わせ→Discord**: 実装 = `/inquiry/submit` `/apply/submit`(POST JSON name/email/phone/job_title/company_name/message)→ `send_discord(webhook, …)` + SES 確認メール。**Discord webhook URL は thinkx/.env にある**(オーナー確認済み)。テスト: フォーム送信 → `journalctl -u uwsgi_thinkx | grep discord` で `sent successfully` か `skipped`。
- **staging.<domain> 実運用化(進行中)**: オーナーが Route53 に staging.truetechjapan.com / staging.nntmapp.com の A(→16.76.147.168)追加済み。**certbot(証明書がワイルドカードか)未確認** → `ssh supercom-lb 'sudo certbot certificates'` で Domains 確認が次の一手。確認後 loadbalancer repo(2026refactor)に staging vhost(Host を本番ドメインに書換)を作り push→pull。truetechjapan/nntmapp は uwsgi_thinkx が host 振り分けで配信(app は 200)。kazukiotsukacom(8007)/transformism(8006)は未起動。
- **未コミット多数**: infra(setup 各種・run/・etc の push_env/push_assets/push_secrets・docs D-14〜D-43・coding_guides)は未 push。loadbalancer は 2026refactor push 済み(web1+staging vhost)。nginx-web-root は push 済み。
- **S トラック申し送り**: thinkx の polyfill.io 参照削除(恒久修正・sub_filter 不採用)/ config.py が秘密を journald に平文ログ。

## 2026-07-14 ★ 棚卸し(rebuild 漏れ)解決
オーナー指摘「setup 実行だけでサイトが立つべき」に基づき ad-hoc 修正を script 化:
- setup_kazukiotsukacom.sh: .env 配置 / front build(babel+lessc)/ uwsgi drop-in(SIGQUIT)追加。
- setup_loadbalancer.sh: cert を secrets.tgz 経由 / htpasswd を env/loadbalancer/.env から生成(chmod 644)/
  clone 後 `git checkout 2026refactor` / 末尾 verify を色付きに。
- loadbalancer repo **2026refactor**: proxy_pass 192.168.1.8→web1.supercom.internal(全静的サイト)+ staging vhost。
  **master はオンプレ本番のまま不変**(AWS 変更を master に載せかけたが origin/master は無傷と確認・2026refactor に是正)。
- env dir 綴りミス kazukitotsukacom→kazukiotsukacom リネーム。
- 実証: LB を 2026refactor に切替 → staging.thinkxinc.com 200(.env 資格情報)。D-37/38/39 記録。
- 残: ④ env/kazukiotsukacom/.env 中身(オーナー)/ Route53 staging A は手動(D-38)/ quantz-web は D-27 後。

## 2026-07-14 🔴 thinkx が polyfill.io を参照(サプライチェーン脆弱性・S トラック)
- ブラウザで staging.thinkxinc.com を開くと `https://polyfill.io` 由来の Basic 認証プロンプトが出た
  (= ページが polyfill.io の script を読み込んでいる。ユーザ設定の認証ではない・資格情報を入れてはいけない)。
- 該当: thinkx `web-server/views/templates/index.html:281` と `about/philosophy.html:23`:
  `<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>`
- polyfill.io は 2024 にドメインが売却されマルウェア注入した既知のサプライチェーン攻撃。参照は危険。
- 対応(S トラック・thinkx repo): script 行を削除(es6 polyfill は現代ブラウザで不要)or 安全なミラーに差し替え。
  infra では直さない(読み取り専用・トラック規律)。staging リハがこれを炙り出した。
- **オーナー裁定(2026-07-15)**: 恒久修正=thinkx repo(2026refactor)から該当 script 行を削除。LB の sub_filter 暫定対策は**入れない**。
  対象: index.html:281 / about/philosophy.html:23 の polyfill.io script 行。

## 2026-07-14 ★ staging 経路 end-to-end 実証(thinkx)
- https://staging.thinkxinc.com → LB(EIP 16.76.147.168・*.thinkxinc.com ワイルドカード実証明書=lb-certs.tgz 由来・警告なし)
  → web1.supercom.internal:8005(内部 DNS)→ nginx-web-root → uwsgi_thinkx(2026refactor)→ **200**。
- 2026refactor は master の上位互換(master tip が共通祖先。欠落機能なし。vendored libcommon + conf.d + golden tests を追加)。
- Route53: staging.thinkxinc.com A → LB EIP は**コンソールで手動追加**(apex 無変更)。今後 staging.<domain> で揃える(D 化候補)。
- **未コミット**: LB の staging vhost は /src/loadbalancer/conf.d/staging.thinkxinc.com.conf を **EC2 上で直接作成**(D-28 の正道は
  loadbalancer repo にコミット)。リビルド再現のため repo 化が必要。証明書パスは既存 /etc/letsencrypt/live/thinkxinc.com/(ワイルドカード)を参照。
- 既知の注意: thinkx config は production/develop のみ(staging 概念なし)。HOST_URL=production のため絶対リンクが本番へ飛ぶ場合あり
  → staging 完結は S トラック対応。表示・基本操作の確認は可能。

## 2026-07-14 thinkx 起動時の秘密ログ / 環境変数の出所(🔴 要対応)
- thinkx の config.py が起動時に**全 config 値を journald に平文ログ出力**しており、
  `Config.AWS_SECRET_ACCESS_KEY: <REDACTED>…` が丸見え。ログに秘密を残さない規約に反する。
  thinkx repo 側のコードのため勝手に直さず報告(修正は原本 repo で・S トラック)。
- AWS キーの出所 = **/src/thinkx/.env の中**(grep 確定)。infra/env/thinkx/.env に実 SES キーが入っている
  (おそらくメール機能用にオーナーが追加)。infra/env/(gitignore)格納なら扱いは適正。
  → 本当の問題は上記の config.py が秘密を journald に出す点(それ以外は想定内)。要オーナー確認。

## 2026-07-14 uwsgi restart がハングする(SIGTERM=reload)
- uwsgi_thinkx.service は Type=simple・KillSignal なし、uwsgi.ini に die-on-term なし。
  uwsgi は SIGTERM を reload 扱いするため systemctl stop/restart が TimeoutStopSec(90秒)待ちでハング。
  そのため run/restart スクリプトの journal 出力に到達せず「ログが見えない」。
- infra 側修正: systemd drop-in `/etc/systemd/system/uwsgi_thinkx.service.d/override.conf` に
  `KillSignal=SIGQUIT` + `TimeoutStopSec=10`(uwsgi は SIGQUIT で即 shutdown)。setup_thinkx に恒久化。
  原本側の正攻法は uwsgi.ini に `die-on-term = true`(S トラック)。

## 2026-07-14 setup_thinkx 実行で判明
- **get-pip 3.9**: `https://bootstrap.pypa.io/get-pip.py`(汎用)は Python 3.10+ 必須になり 3.9 で
  `ERROR: does not work on Python 3.9` → pip 未生成 → `./venv/bin/pip: command not found` → 依存未install
  → uwsgi app 起動失敗 → socket 無し → 8005 が 000。修正: `.../pip/3.9/get-pip.py`(setup_quantz は既に正)。
  setup_thinkx / setup_kazukiotsukacom を修正済み。
- **front build 誤り**: setup_thinkx の `npx npm-run-all … copy:simplicity:js copy:simplicity:css` は quantz-web 用タスクで
  thinkx に無い(`Task not found`)。thinkx の compile:views:* は **--watch 付きで常駐**。非 watch ビルドタスクが
  2026refactor にあるか要確認。暫定で該当行を無効化(dist 済み assets 前提で 200 を狙う)。
- **playbooks**: submodule が素の github.com URL で Deploy key alias 未経由 → Permission denied。
  オーナー「playbooks は使わないので無視」→ setup_thinkx から submodule 取得行を削除。
- verify(D-36)の赤 `FAIL: thinkx 8005 -> 000` が末尾に出て、ログを追わず一目で失敗と分かった(色分け有効)。

## 2026-07-13 Deploy key を preflight 化(check_deploykey.py)
- 起点: nginx-web-root 新設時に Deploy key 未登録で clone が silent 失敗。setup_user の REPOS ループが
  鍵管理を抱え、repo 追加のたびに人手の記憶に依存していた(構造欠陥)。
- 確定設計(D-33/D-34/D-35): 鍵の真実 = Mac の infra/deploykeys/。各 setup_{service} 冒頭で
  check_deploykey.py <repo> を呼び、install(上書き)+ config.d alias + ssh -T 検証。未整備は公開鍵表示 +
  戻り値1(exit で ssh を切らない)。EC2 再作成でも scp+再実行で復元・GitHub 再登録不要(方式 b)。
- setup_deploykey.sh(前案)は廃止・削除。setup_user.sh は user + Include 骨格のみ(分岐ゼロ)。
- **要確認(CLAUDE.md #1 との整合)**: setup_quantz.sh は今も `git submodule update --remote --recursive` で
  libcommon を取得しうる(url.insteadOf に libcommon 行あり)。CLAUDE.md #1 は「libcommon は vendoring 済み、
  submodule 取得を書かない・残っていたら削除」。deploy key の checkは llm/simplicity のみに絞った(libcommon 除外)が、
  submodule update 行と libcommon の insteadOf は未修整で残置。**この矛盾の解消は deploy key タスク外のため保留・要指示**。

## 2026-07-13 Route53 最小権限 と 料金反映
- supercom ユーザの Route53 権限はオーナーが段階式最小構成に締めた(CreateHostedZone は Resource 絞り不可 /
  GetChange は change/* / zone 操作は hostedzone/*・第2段階で zone ID 固定 / ListHostedZones・Associate 系は除外)。
- **穴を1つ検出**: dns.tf の zone には tags(+provider default_tags)が付くため **route53:ChangeTagsForResource
  (hostedzone/\*)が必要**。無いと apply が 403。→ ポリシーに追加を依頼(議論の「タグを付けていなければ不要」は
  現物と不一致だった)。
- 料金反映の検証: EIP は既存「Public IPv4」行と同単価で反映済みだったが、**Route53 private zone $0.50/月が未計上**
  → cost-estimate.sh に追加(staging 24/7 合計 40.93 → **41.43 USD/月**)。private zone のクエリ($0.40/100万)は無視。

## 2026-07-12 F4 調査(thinkx repo を clone して確認)= 🔴 新ブロッカー
- uwsgi: `web-server/uwsgi/uwsgi.ini` は **socket=`/tmp/uwsgi_thinkx.sock`(unix)**・module main:app・venv ./venv。
  `uwsgi_thinkx.service` は `User=kaz`・ExecStart `venv/bin/uwsgi --ini uwsgi/uwsgi.ini`。→ F5 の unix socket 確定。
- **本番用の web nginx 設定が repo に無い**。存在するのは `local/nginx/`(ローカル開発用: Mac 絶対パス
  `/Users/K00TSUKA/...`・`daemon off`・`listen 8000`・`server_name thinkx.localhost`・`unix:/tmp/uwsgi.sock`)。
- `web-setup.sh` は `thinkx/web-server/nginx/nginx.service` を symlink するが**そのパスは存在しない**(`if [ -f ]` で無言スキップ)。
  → **web 箱は 8005 で配信できない**(LB→web:8005 が到達しない)。
- 対応候補(要判断): (a) `local/nginx/webserver.conf` を本番用に改変(listen 8005・socket 名 `/tmp/uwsgi_thinkx.sock`・
  Mac パス→`/src/thinkx/web-server`・truetechjapan/nntm 各 server ブロック追加)して infra 側に持つ、
  (b) オンプレ実機から本番 web nginx.conf を回収(git 外),(c) web-setup が生成する。
- 「本番同様のリハ」を 8005 まで通すには F4 の解決が必須。

## 2026-07-12 bash 規約(docs/coding_guides/bash.md)適合
- 規約: 観測系(見るだけ)は `set -e`/`set -u`/`pipefail`/`exit` **禁止**(関数+return・cd はサブシェル)。
  変更系(状態変更)は `set -euo pipefail` を**使う**。
- 現状の逸脱(観測系なのに set -e/exit 使用): ~~`plan-summary.sh`~~(D で観測系準拠へ直済)・
  `cost-estimate.sh` `cost-hook.sh`(未・順次)。status.sh(オーナー作)も観測系だが set -e/exit あり → オーナー判断。
- 変更系(web-setup/lb-setup/user-setup/smoke)は `set -euo pipefail` で規約通り。

## 2026-07-12 F4 判断: 本番 web nginx 設定
- thinkx は読み取り専用 → 本番 web nginx 設定は **infra 側に持つ**(`infra/setup/nginx/`)。
- **正 = オンプレ実機から本番設定を回収**。git のは `local/nginx`(開発用)のみで、truetechjapan/kazukiotsuka
  ブロック無し・nntmapp の振り分け曖昧 → 完全な再構成は不可(推測になる)。
- 暫定: `infra/setup/nginx/web-thinkx.conf` を再構成ドラフトとして作成(8005→uwsgi_thinkx.sock、
  thinkx/truetechjapan/nntm)。**実機照合が必須**。web-setup への配線は照合後(現状 section 8 は
  存在しないパスを symlink=無言スキップ、要修正)。

## 2026-07-17 I-STEP2 事前検査: キーペア名の抜けを検出(🔴 apply 前に要修正)
- terraform `variables.tf` の既定 `key_name = "supercom-key"` は **AWS に存在しない**
  (`aws ec2 describe-key-pairs --key-names supercom-key` → InvalidKeyPair.NotFound)。
- 実在するキーペアは **`supercom`**(ap-northeast-1。staging の supercom-staging-web/lb が現に使用中)。
  staging は tfvars で `key_name=supercom` を上書きして通していたと推定(tfvars は読取禁止のため未確認)。
- **提示済みの prod plan はこの既定値のままなので、そのまま apply すると EC2 作成で失敗する。**
- 対応(I-STEP2b の流儀 = 手作業で埋めず repo に反映):
  1. 即応: plan/apply に `-var=key_name=supercom` を明示。
  2. 恒久: `infra/terraform/variables.tf` の default を `supercom` に修正(+ plan 再提示)。
- AWS アカウントの確認も完了: **027421896362**(IAM user supercom)が唯一の実在アカウントで、
  staging・旧サイト EC2 群すべてがここに居る。prod も同アカウントに新設で正しい(別本番アカウントの形跡なし)。

## 2026-07-17 plan-summary.sh: ハング原因の可視化 + my_office_ip の恒久解
- 症状: `scripts/plan-summary.sh prod` が無言で返らない。二因: ①必須変数 my_office_ip に既定なし
  → terraform plan が対話プロンプト(>/dev/null に飲まれ無言)で停止 ②その停止プロセスが state ロック保持。
- 恒久解(設計どおり): **`infra/terraform/terraform.tfvars`(gitignore 済み)を作成**し my_office_ip/key_name を置く。
  terraform が自動読込するので以後 `-var` 不要。実ファイル未作成だったのが原因。雛形 terraform.tfvars.example あり。
  ※ tfvars は Claude 書込禁止 → オーナーが作成(paste-ready を提示)。
- スクリプト修正: `-input=false`(プロンプトで固まらせない)+ `-lock-timeout=10s`(ロック中も無限待ちしない)+
  実行前に .terraform.tfstate.lock.info を読んで Who/Operation/ID を表示 + 失敗時は terraform 生エラーと
  検出理由(ロック/tfvars 未作成)を表示。無言ハングを排除。
- 付随知見: ローカル backend は state ロックが1つ。apply の承認待ち中は plan-summary を同時実行できない(仕様)。

## 2026-07-17 F4 クローズ + setup の monorepo 化(prod 構築)
- **F4 は解決済みだった(私の findings が stale)**: web の 8005/8006/8007 配信は
  「nginx-web-root(サイト非依存 nginx 基盤・monorepo 収載)+ 各サイト repo 内
  `web-server/nginx/conf.d/*.conf`」の合成で、staging で確立・全 Host 200 を実測確認。
  オンプレで 8005 を握る実体は旧 quantz-web nginx 基盤(nginx-web-root の前身)。調査不要、staging が手本。
- **setup の monorepo 化(I-STEP2b)**: prod は polyrepo 個別 clone ではなく monorepo を 1 回 clone。
  - 新設 `setup/clone_monorepo.sh`: thinkx-system(branch monorepo)を /src へ clone し、
    /src/{thinkx,kazukiotsukacom,transformism,nginx-web-root,loadbalancer} を symlink で staging と同一レイアウトに。
    libcommon(a316494)/simplicity(53f0639)原本は鍵があれば並置 clone(lb では WARN スキップ)。
  - setup_{thinkx,kazukiotsukacom,transformism,nginx-web-root,loadbalancer}.sh の clone 節を
    「symlink 存在ガード」に差し替え。他は staging 実績のまま不変。
  - deploy key は **thinkx-system 1本 +(web のみ)libcommon/simplicity** に集約(staging は 6 本)。

## 2026-07-17 受け入れ試験スクリプト新設 + staging 実測 green
- 新設 `infra/scripts/acceptance-sweep.sh <LB_IP>`(観測系): 3サイトの tests/golden/route_sweep.json
  全 GET ルートを `--resolve` で Host→LB IP 固定の https で当て、status を全件照合(DNS 非依存)。
  ルール→URL 変換は test_route_sweep.py の _concrete と同一(<lang>→en / 他→x)。
- staging LB(16.76.147.168)で実測: **thinkx 56/56・kazukiotsukacom 4/4・transformism 2/2 = 62/62 green**。
  prod 受け入れは同スクリプトを prod LB(52.197.179.70)へ向けるだけ。

## 2026-07-17 prod web 8005/6/7 無応答の原因と修正
- 症状: サイト setup の verify が `FAIL: transformism 8006 -> 000` 等。サービスは全 active。
- 原因: `setup_nginx-web-root.sh` の `systemctl enable --now nginx` は**既に起動中の apt 版 nginx を再起動しない**。
  unit を nginx-web-root に差し替えても旧プロセス(80番のみ)が残り、8005/6/7 を誰も listen しない。
  さらに verify が `is-active` のみだったため「OK: nginx-web-root up」と偽緑。
- 修正: ①enable + **restart** に変更 ②verify を「実プロセス cmdline に nginx-web-root を含む + 8005 応答」に強化
  ③手順8の順番を nginx-web-root → サイト3つ に変更(各サイト verify がその場で成立)。
- 箱は restart で復旧、3サイト 200 実測。

## 2026-07-18 動的 IP 締め出しが現実化 → add_current_office_ip.sh 新設
- 予告済みリスク(2026-07-15 記録)が発生: ルーター外向き IP が 153.195.60.70 → 116.82.241.252 に変化し、
  prod web/lb への SSH(22)が SG で締め出し。配信(80/443)は無影響。
- 恒久対応: `infra/scripts/add_current_office_ip.sh`(変更系)を新設。現在 IP を検出し、
  prod = tfvars 書き換え + terraform apply(in-place)、staging = SG の 22 番ルールを CLI で入れ替え、
  末尾に4台への SSH 到達を色付きで判定。IP が変わるたびオーナーがこれを1本流すだけ。
- 根治(inbound 22 の廃止 = SSM Session Manager 化)は I-STEP2b 改善候補のまま維持。

## F13: LB の default server が旧サイト jessicas.online に落ちる(2026-07-18)

- 事象: `https://52.197.179.70/`(Host なし=IP 直打ち)が CN=jessicas.online の**期限切れ証明書**(2025-07-07 失効)+ 502 を返す。ブラウザでは証明書エラーで「つながらない」ように見える(vhost 方式なので IP 直打ちが本番サイトを返さないこと自体は正常。Host つきは 200)。
- 原因: loadbalancer conf にオンプレ時代の旧サイト(jessicas.online)の server ブロックが残存し、default server に選ばれている。stray `192.168.1.7:8009` と同類の掃除課題。
- 対応: I-STEP3(またはカットオーバー後の conf 掃除)で旧 server ブロック撤去 + default server を明示(444 を返す catch-all 等)。実施前にオーナー判断。

## 受け入れ green(I-STEP2 構築完了・2026-07-18)

- 経路疎通 check_request_path: 20項目 全緑(私+オーナー双方の実行で一致)
- 受け入れ acceptance-sweep: **62/62 全ルート一致**(thinkx 56 / kazukiotsukacom 4 / transformism 2)
- 残: kazukiotsukacom 動画未配布(push_assets.sh → DNS切替手順の手順1に組込済)
- DNS 実測: 3ドメインとも Route53、apex A=123.226.234.127、TTL 300s、www レコード無し。切替対象は apex 3件のみ
- 切替手順は `docs/DNS切替手順.md`(切替・戻し・凍結まで)。実行はオーナー承認ゲート

## F14: TLS 証明書の期限 2026-09-15・自動更新未設定(2026-07-18)

- 実測: 3ドメインとも notAfter=2026-09-15(オンプレ回収の lb-certs.tgz 由来)
- 新 LB に certbot 自動更新が無い。放置すると 9/15 に全サイト証明書エラー
- 対応(I-STEP2b): certbot --dns-route53 + EC2 IAM ロール(infra/CLAUDE.md 制約6の通り)。**8月中に要実施**

## run/ スクリプトの D-36 未適用を全面適用(2026-07-18)

- 露出: restart_loadbalancer.sh が緑判定なしで手順に使われた(オーナー指摘)
- 判定なしだった6本(loadbalancer/quantz 各 run/restart/stop)に色つき判定を追加
- 全15本の判定行に**スクリプト名を名乗らせた**(複数実行時の帰属問題の再発防止)
- restart/run の nginx 系は D-48 どおり「is-active + 実プロセスの設定パス + ポート応答」で判定

## office_ip_report.sh 初回実測と2バグ修正(2026-07-18)

- バグ1: SG クエリが空を返す(JMESPath 組立)→ D-35 どおり JSON+Python に書換。supercom 管理外も含む全 SG の 22 番許可を列挙、0.0.0.0/0 は赤表示に強化
- バグ2: 最終アクセスが「Jul」で切れる(syslog タイムスタンプ3語を1語で捕捉)→ datetime パース(年跨ぎ補正つき)に修正
- 実測結果: supercom 4 SG の許可は 153.195.60.70/32 と 116.82.241.252/32 のみ・両方使用実績あり・撤去候補なし

## F15: 旧世代 SG 12個が SSH(22) を 0.0.0.0/0 開放(2026-07-18)

- 実測: launch-wizard-1〜13 と webserver が 22 番を全世界開放。ただし**稼働中インスタンスへの紐付けは無し**(running 4台はすべて supercom-*-sg のみ)→ 即時の実害なし
- 対応候補: 未使用 SG の削除(オンプレ移行完了後の掃除・I-STEP3 か旧環境凍結時にまとめて)。削除は変更系のためオーナー承認

## F14 対応実装(2026-07-18)

- 実測: IAM ロール(supercom-prod-lb)は付与済み・certbot+dns-route53 プラグイン導入済み・reload hook あり・timer 稼働中。欠落は renewal conf 5件の authenticator=manual のみ
- 対応(D-49): setup_loadbalancer.sh に冪等 sed(manual→dns-route53)を組込・verify を「manual 残 0 件」まで判定するよう強化。検証は scripts/check_cert_renewal.sh(dry-run)
- クローズ条件: LB で切替実行後、check_cert_renewal.sh が green(次回自動更新は 8/16 頃・期限 9/15 の 30 日前)

## F14 クローズ + 動画 WARN の正体(2026-07-18)

- F14: オーナー実行の check_cert_renewal.sh が green(dry-run 5ドメイン成功)。自動更新成立、クローズ
- 「kazukiotsukacom 動画未配布」WARN は偽警告だった: staging 実測で動画を持つのは thinkx のみ(8本・prod 配布済み)。kazukiotsukacom / transformism は元々動画なし。setup_kazukiotsukacom.sh に thinkx 由来の展開ブロックが残っていたのが原因 → 除去。DNS切替手順の事前チェックも push_assets thinkx に修正

## staging in-place monorepo 差し替えの事前点検(2026-07-19・D-50)

- staging /src は polyrepo 実ディレクトリ(thinkx / kazukiotsukacom / transformism / nginx-web-root / quantz-web)。`ln -sfn` は差し替え先が実ディレクトリだと中にリンクを作る → clone_monorepo.sh に退避(/src/_old_polyrepo/)を追加。quantz-web は対象外・不触
- deploy key は追加作業不要: push_secrets.sh が infra/deploykeys(thinkx-system/libcommon/simplicity の3鍵)を運ぶ。GitHub 側登録はリポジトリ単位で済み
- 手順10/11 の LB_IP が staging で terraform output 不可(state は旧 infra リポジトリ)→ LB_IP を prerequisites の環境ブロックへ移動(staging=16.76.147.168 直値)
- staging lb にも IAM ロール(supercom-staging-lb)付与済みを実測 → setup_loadbalancer の renewal 切替(D-49)は staging でも成立する

## 構築手順の setup 呼び出しが ENVX を渡していなかった(2026-07-19)

- 手順5/8/9 が素の `ssh $HOST 'bash -s' <` で、ENVX 依存の setup_webserver / setup_loadbalancer に staging が伝わらず hostname が prod 値(web1/lb1)になるところだった(staging 差し替えの事前点検で発見。prod では偶然無害)
- prerequisites の run() 経由に統一(setup_*.sh の全呼び出し)。run() は「ssh bash -s がごちゃごちゃしすぎ」というオーナー指示由来の仕組みでもある

## D-51: staging ゼロ再構築へ方針変更(2026-07-19)

- in-place 差し替え(D-50)はオーナー指摘で撤回。「いずれ I-STEP3 で必ずやる作業(state 分離・DNS 付替)を先送りしていただけ」が実態だった
- terraform workspace 分離を構築手順 prerequisites に組込(staging=workspace staging / prod=default)。LB_IP は workspace 経由で両環境とも terraform output に統一
- EIP 実測10個(supercom 4 + legacy 6)→ 上限余裕不明のため destroy 先行
- clone_monorepo.sh の旧ディレクトリ退避は新規箱では no-op のため防御として残置

## F16: /js/simplicity アセットは全環境で 404(既存欠陥・カットオーバー非障害)(2026-07-19)

- thinkx のテンプレート(general/NNTM の common.html)が `/js/simplicity/dist/simplicity.js` 等を参照するが、
  **オンプレ本番も旧 staging も新 prod もすべて 404**(実測)。views/js/ に simplicity が存在せず、nginx にも
  マッピングなし。つまり monorepo 移行の退行ではなく従来からの欠陥(パリティは取れている)
- /src/simplicity(B案・53f0639 固定)はサイト配信に未配線。配線するか、テンプレートから参照を外すかは
  simplicity リファクタリング側の計画で判断(このセッションでは触らない)

## 旧 staging の terraform state がこの Mac に存在しない(2026-07-19)

- ~/Sources/infra は 7/12 の clone で tfstate / tfvars とも無し。terraform_destroy.sh は「破壊対象 0 件」で正しく停止(state 喪失の検出にもなった)
- 実測: staging VPC = vpc-0a837c944d5750395(Name=supercom-staging、192.168.0.0/16)。IAM 名 supercom-staging-lb が残っていると monorepo terraform の staging apply が EntityAlreadyExists で失敗するため IAM も撤去対象
- 対応: scripts/destroy_old_staging.sh(一回きり・aws CLI・棚卸し全提示 → yes 必須)。private hosted zone は権限都合で対象外(残置無害・コンソールで任意掃除)

## 旧 staging 撤去完了(2026-07-19)

- destroy_old_staging.sh 実行(オーナー yes)→ SG 1個と VPC のみ DependencyViolation で残존:
  **SG の相互参照**(web-sg のルールが lb-sg を許可元参照)による削除順依存。参照元 web-sg 消滅後に
  lb-sg → VPC を削除して完遂(VPC NotFound 確認済み)。スクリプトは SG 削除を2パス化して反映
- EIP 2個解放・IAM 名 supercom-staging-lb 解放 → 新 staging の terraform apply(workspace staging)が通せる状態
- 注意: staging.<domain> の A レコード5件は解放済み IP(16.76.147.168)を指したまま。手順12 で新 EIP に付け替えるまで staging URL は不通

## terraform ラッパーの統一(2026-07-19・オーナー指摘)

- 指摘: apply_env という名前では中身が分からない。従来の「plan-summary で差分チェック → apply」の2段階が簡単
- 対応: 2段階の形を維持したまま名前を実態に一致させ統一 — plan-summary.sh(名前維持・**workspace 自動選択と引数必須を追加**)/ terraform_apply.sh / terraform_destroy.sh / terraform_output.sh。従来手順との違いは workspace 対応(monorepo で state が同居したため必須)・逆環境ガード・cd 不要のみで、実質同じ流れ

## D-52 移行完了 + 構成図の固定文言が古い(2026-07-19)

- prod state の envs/prod への移動後、plan-summary prod = **変更なし**(移行の完全性を実機比較で証明)
- plan-summary.sh の構成図の固定部分に旧記述が残存: Host tag supercom2/supercom3L(D-46 で廃止)・
  transformism「Sトラック未適用→人間判断」(D-44 で完遂済み)・命名 supercom-prod-web/lb(実タグは
  supercom-web1/lb1)。差分計算とは無関係の表示のみ。次回図を触る際に更新

## 新 staging apply 完了(2026-07-19)

- terraform_apply staging: 19 add / 0 change / 0 destroy 全成功。web 57.182.107.57 / lb 52.68.142.190
- Name タグは最初から D-46 準拠(supercom-web1-stg / lb1-stg)→ hostname.md の staging タグ手順は自動消化
- 発見: outputs.tf の setup_hint が旧世界の構築案内のまま(実害なし)。構築の正は docs/構築手順.md — setup_hint は削除か手順書への誘導に直すべき(次回 .tf を触る際)

## setup_user / setup_webserver に verdict が無かった(2026-07-19・staging 再構築で露出)

- 手順5の出力が gulp --version 表示で終わり成否不明とオーナー確認 → D-36 適用漏れ2本(setup_user.sh / setup_webserver.sh)に verify + 色つき verdict を追加(webserver は hostname が ENVX 期待値かまで判定)
- 実機は正常を別途実測: hostname=web1-stg(run() の ENVX 修正が有効)・kaz あり・/src に monorepo + symlink + libcommon/simplicity 原本(手順6まで完了状態)

## 新 staging 受け入れ green + F13 の環境差症状(2026-07-19)

- **手順4〜11 が「同じ手順の再実行」で素通りし、経路疎通 全ホップ green・受け入れ 62/62 一致(prod と同一結果)**。
  D-32 の完了指標を staging ゼロ再構築で実証。今回の再実行で露出した抜けは D-36 verdict 漏れ2本(setup_user/setup_webserver、修正済み)のみ
- check_request_path [1] が staging で NG になった件: F13 の残骸(default server → 死んだ 192.168.1.7:8009)の症状が
  環境で変わるため(prod=同一サブネットで即 502 / staging=サブネット外ブラックホールでタイムアウト)。
  [1] の意図は「public IP の 443 到達」なので TCP 接続判定に修正(IP 直打ちの HTTP 応答は vhost 方式の仕様外)

## staging ゼロ再構築 完遂(2026-07-19)

- 構築手順 1〜12 をフル実行して完遂: terraform apply(envs/staging)→ setup 群 → 経路疎通 全ホップ green →
  受け入れ 62/62 → staging.<domain> 5件を 52.68.142.190 へ付替 → 実 DNS 経由で 5ドメインとも 401+正証明書を実測
- これで staging / prod が**同一手順書(/Users/K00TSUKA/Sources/thinkx-system/infra/docs/構築手順.md)の産物**になった
  = I-STEP3 の中核(monorepo 前提再構築)を前倒しで消化(D-51)。ROADMAP の I-STEP3 項の扱いは人間判断
- 新 staging は最初から: D-46 命名(タグ・hostname)・証明書自動更新(D-49)・IAM ロール・prod と同一の /src レイアウト

## Codex 並行セッションとの照合(2026-07-19)

- Codex サマリーの「未 push 3コミット」は**既に push 済み**(origin と完全同期を実測)。追加で k00bot2 の merge はオーナーにより revert 済み(719e856)・AGENTS.md 新設・terraform_output.sh の2バグ(eips ディレクトリ判定 / map 出力)は Codex 修正済みで eip_ledger 4件の出力を実測確認
- D-52 / D-53 は DECISIONS に原文つきで記録済み・F16 も記録済みを確認(欠落なし)
- **polyfill.io 除去(5892559)は staging 反映済みだが prod 未反映を実測**(prod の /src/thinkx-system が 1e65aa9 で停止・テンプレートに参照残存)→ prod へ pull + restart_thinkx が必要(DNS 切替前必須)

## setup_claude_code の偽緑と postinstall ブロック(2026-07-19)

- 露出: npm の allowScripts 既定ブロックで Claude Code の postinstall(本体バイナリ取得)が走らず、
  claude コマンドは存在するが起動不能。verdict が `command -v` の存在確認だけだったため**緑を出した(偽緑)**
- 修正: install に `--allow-scripts=@anthropic-ai/claude-code` を明示 + verify を「バージョンが取れること」に変更。
  教訓は D-48 と同型 — **存在や is-active でなく、機能する証拠で判定する**
- 小ノイズ: ubuntu ユーザーの .bashrc に autoenv の残骸(activate.sh 不在エラー)。実害なし・掃除は任意

## サーバー編集ドキュメントの整理(2026-07-19・オーナー裁定)

- 正本は docs/サーバー編集ClaudeCodeセッション.md(オーナー全面書き換え)。ROLES.md と
  旧 infra/docs/サーバー編集のエージェント化計画.md は削除(二重管理の解消)
- 役割別応答の切替は**名乗り方式を撤回**: 会話の流れで相手が「私はエンジニアではない」等と言った時点で
  プロファイルを切り替える(自己申告の名乗りは不要)。権限ゲートが役割と無関係な点は不変
- `claude --rc` は `--remote-control` の短縮として実際に機能する(オーナー実測)
- 旧計画書から引き継ぐ v2 候補(未実施のメモ): サーバー専用 Anthropic アカウント(個人 Max との分離)/
  tmux 接続専用の制限ユーザー(ssh 共有 = sudo 共有の緩和)/ バックアップリポジトリへの push /
  ブランチ分離(staging→本番昇格)/ staging の pull 型自動反映
