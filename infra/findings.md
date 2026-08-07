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

## filedrop はサイト内ハンドラーに変更(2026-07-19・オーナー裁定)

- infra の別サービス(8008 常駐)案を撤回し、thinkx の Flask に `/filedrop` を実装
  (「ドメインが thinkxinc.com なんだから ThinkX の配下にあるべき。サイトの1ページとして実装すればいい」)
- production では 404(Config.ENV 判定)。入口は staging.thinkxinc.com/filedrop(LB の basic auth 配下)のみ
- LB staging vhost に client_max_body_size 75m(web 側 nginx の既存値と一致)。着地は /src/thinkx-system/Downloads

## filedrop ガードと LB verify の2バグ(2026-07-19・実測で露出)

- staging の thinkx も Config.ENV=production で動いている実測 → /filedrop のガードを ENV 判定から
  **ホスト名判定(-stg 接尾辞・D-46 準拠)**へ変更(ENV では prod/staging を区別できない)
- restart_loadbalancer.sh の verify が `curl https://localhost/` で F13 のブラックホール(名前なし直打ち)に
  自爆し、active なのに FAIL(偽赤)。Host つき(--resolve staging.thinkxinc.com→127.0.0.1)に修正

## インスタンスサイズ実測と最適化の判断材料(2026-07-20)

測定(staging web t3.small・Claude Code 起動中・ビルドなし):
- 2GB 中 1245MB 使用・空き 459MB・**スワップ 0**(OOM 即死のリスク)
- claude 517MB / node 系(VS Code Remote 等)~320MB / uwsgi×3 ~230MB
- **docker + containerd が active(~150-200MB 無駄)** — staging web に docker 不要(quantz 用)
- prod web(t3.medium)は 464MB / prod lb(t3.small)は 265MB 使用 = 大きく余っている

判断:
- ボトルネックはメモリのみ(CPU は load 0.00・2vCPU は全サイズ共通)
- **設計反転**: 配信専用の prod は縮小可(web medium→small / lb small→micro・月約$30減)、
  開発する staging web はむしろ余裕が要る
- staging web 案1=t3.medium 化 + stop_staging でこまめ停止 / 案2=t3.small のまま swap 2-4GB + docker 停止
- terraform をサイズの env 独立指定に変更が必要(現状は is_prod 連動で反転不可)。
  instance_type 変更は stop→modify→start の短時間停止・EIP は台帳で維持・prod は承認/タイミング要

## Mac ローカルブランチの別トラック混在と復旧(2026-07-20)

- 受賞企業ページ4社(truetechjapan)は staging に8コミットで存在・未 push だった → staging で origin にリベースし push(6b32e0c)。競合なし・成果は無事
- 事故: 私が claude-session 変更を Mac でコミットしたら Mac HEAD が auth 線(29c4f78)で、infra コミットが auth に乗り push 拒否 → reset --soft → mixed reset で Mac を無傷復帰(citywalk 未コミット作業も保持)。教訓は D-58(デプロイ/push は staging 経由・Mac 非依存)
- tmux/claude はインスタンス停止で消える(全プロセス死)。ただし /home/kaz/.claude(認証)は EBS 上で永続 → 再ログイン不要。起動時自動復帰は claude-session.service(D-59)

## 次の infra セッションへの是正事項(worktree 方針 D-58・2026-07-20)

CLAUDE.md「worktree と deploy checkout の分離」を明文化したので、既存実装を次セッション(専用 worktree 用意後)で是正する:
- **claude-session.service の WorkingDirectory が deploy checkout(/src/thinkx-system)を指す** → CLAUDE.md 違反。専用の編集 worktree+branch を指すよう変更。attach_claude.sh / setup_claude_code.sh も編集 worktree 起点へ。
- **deploy.sh が origin/monorepo の暗黙 HEAD を pull** → 明示 DEPLOY_REF に変更(staging 受け入れ済みの ref を prod へ同一適用)。
- **本セッションの infra 編集は staging deploy checkout 上で直接行い staging から push した = Mac 汚染事故の障害復旧(例外)**。通常は専用 worktree で編集し worktree から push する。
- 対応方針: 専用 infra worktree を用意した次セッションで上記を実装。本セッションは方針に従いクローズ。

## 3トラック混在履歴の組み直し(2026-07-20・交通整理)

分岐点 a663f6c から、ローカルの1本の線に3トラックが積み上がっていた:
fe82157(citywalk)→ cf14a9b/d797020/23dd576/29c4f78/2e0e1f4(auth 5件)→ 890e087(citywalk)。
work/auth も work/citywalk もこの混在線を祖先に持つため、両方を origin/monorepo 上へ組み直す。

競合の実態(機械確認済み):
- origin 側 12 コミットが触ったのは docs/GUIDELINES.md・infra/**・thinkx/**・docs/WORKTREES.md・.codex/GUIDELINES.md
- citywalk 2件は citywalk/** と ARCHIVE.md のみ → **origin と重なりゼロ・競合しない**
- auth 5件は auth/** + docs/{DECISIONS,GUIDELINES,ROADMAP}.md。うち origin と重なるのは
  **docs/GUIDELINES.md の末尾追記のみ**(origin=「重要な決定・指示はその場で記録する」/
  auth=「結論だけを先置きせず理由を続ける」)。解決は両ブロックを残すだけ
- 順序: auth → citywalk → infra(D-58 行)。origin/monorepo が共有トランクなので push は直列化する

infra が保留している root docs/DECISIONS.md の D-58 行(auth の d797020 と追記位置が競合するため、
auth の組み直し完了後に追記する。原文は Codex 記述):

| D-58 | **monorepo の並行作業を track 別 Git worktree に分離する。** 1 セッション = 1 計画 = 1 専用 worktree = 1 writer とし、共有 worktree への複数 writer を禁止する。デプロイはローカル HEAD から行わず、origin 上の明示的な不変 `DEPLOY_REF` を staging と production へ同一参照で適用する。サーバーの deploy checkout と自動起動する Claude/Codex の編集 worktree も分離する。 | 同一 worktree を複数セッションが操作し、別トラックの HEAD・index・未コミット変更へ干渉した実事故を再発防止するため。ローカル Mac の作業状態と緊急デプロイを独立させるため。|`CLAUDE.md`、`CLAUDE_GENERAL.md`、`docs/WORKTREES.md`、`infra/CLAUDE.md`、`infra/runbooks/deploy-site.md` |

なお D-58 が参照する `infra/runbooks/deploy-site.md` はまだ存在しない。deploy.sh の DEPLOY_REF 化と
同時に新設する(未着手)。

### 訂正(同日): 上の組み直し計画は実行しなかった

上節の「順序: auth → citywalk → infra」「トラック別 clean branch へ cherry-pick」は**採用しなかった**。
worktree 分離そのものが撤回された(D-49 / D-60)ため、混在チェーン7件を origin/monorepo へ
**1回 rebase して push しただけ**で解消した(bce5d83)。競合は予告どおり docs/GUIDELINES.md の
末尾追記1箇所のみで、origin 側「重要な決定・指示はその場で記録する」と auth 側「結論だけを
先置きしない」を両方残して解決。2649 ファイル・トラック外への波及なしを確認済み。

保留していた root docs/DECISIONS.md の D-58 行も追記しなかった。決定内容が変わったため、
root は **D-49**(単一ディレクトリ運用の規則6項)として書き直し、infra 側は **D-60**(D-58 の
撤回範囲)を追加した。root と infra の採番空間は独立しており、Codex が root に書こうとした
D-58 は infra の D-58 と番号衝突していた。

Mac 側の worktree はすべて解体済み(本体 + k00bot2 のみ)。work/citywalk・work/auth・work/infra・
work/merge は削除。

### 未修正: infra/CLAUDE.md が D-60 と矛盾している

infra/CLAUDE.md 末尾の「worktree と deploy checkout の分離(D-58)」節のうち、Mac 側の worktree
分離を指示している2行が D-60 と矛盾する。infra/CLAUDE.md は infra の禁止事項で書き換えが
禁じられているため未修正のまま残した。削るべきは次の2行:

- 「infra の編集は専用 worktree で行い、他トラックまたは deploy checkout と共有しない。」
- 「サーバー起動時に Claude/Codex セッションを自動起動する場合、専用の編集 worktree と branch を
  `WorkingDirectory` に指定する。deploy checkout 上で起動してはならない。」

deploy checkout を clean に保つ・DEPLOY_REF・Mac の現 branch を暗黙のデプロイ元にしない・
wrapper と承認ゲート・staging からの push は DR 例外、の残り6行は**維持する**(サーバー側の
分離は撤回対象外)。オーナー判断待ち。

## deploy 議論の論点(a): 編集する場所と配信元の分離(2026-07-20・未裁定)

前提: clone_monorepo.sh がサイトの実体を /src/thinkx → /src/thinkx-system/thinkx の
シンボリックリンクで作っているため、**deploy checkout がそのまま配信元**になっている。
一方 staging の Claude Code セッションの存在意義は、スマホやブラウザからサイトを直接いじって
その場で staging.thinkxinc.com で確認することにある。現状の構成ではこの2つが両立しない。

- **案1: 編集用 checkout を配信元にする** — staging だけシンボリックリンクを編集用へ向ける。
  編集が即座に見える。欠点: staging が「prod に出す確定 ref をリハーサルする場所」でなくなる。
- **案2: deploy checkout のみを配信する** — 編集 → commit → push → DEPLOY_REF で反映、で初めて
  見える。正しいが、1行直すたびにこのループを回すのはスマホ運用として重い。
- **案3: staging に2面持つ** — staging.thinkxinc.com = deploy checkout(確定 ref のリハーサル)/
  edit.staging.thinkxinc.com = 編集用 checkout(即時プレビュー)。役割の違うものを1つの箱に
  押し込めているのが混乱の根本なので設計としては一番素直。欠点: vhost と uwsgi がもう1組増えて
  メモリを食う。staging web は t3.small で空き 459MB・スワップ 0 の実測なので、D-57 の
  medium 化とセットでないと成立しない。

前セッションの推薦は案3。**オーナー裁定は未了**。deploy.sh の DEPLOY_REF 化はこの結論に従属する。

論点(b): 「デプロイは Mac 非依存」をどこまで取るか。deploy.sh は Mac から ssh する Mac 起点の
スクリプト。D-58 の趣旨を「Mac のローカル**リポジトリの状態**に依存してデプロイ内容が決まるのを
やめる」と読むなら、DEPLOY_REF を明示した時点で目的は達せられ、Mac 起点のままでよい。
staging から prod へ ssh させる案は staging に prod の鍵を置くことになり攻撃面が広がる。未裁定。

## デプロイ手順書の新設と、D-58 参照先の変更(2026-07-21)

- `infra/runbooks/deploy-site.md` は「まだ存在しない」と 07-20 に記録したが**誤り**。実在したが中身が
  monorepo 以前(`cd /src/thinkx` を git リポジトリとして扱う・`2026refactor → v2.1.0` 前提)で陳腐化して
  いた。**無いより悪い**(手順書として読めてしまう)
- 全面書き換えの上、オーナー裁定により `infra/docs/デプロイ手順書.md` へ改名・移動。
  「構築手順.md / DNS切替手順.md / 運用.md」と同じ**オーナーが実行する手順書の系列**に置く
- **D-58 の規範文書欄が指す `infra/runbooks/deploy-site.md` は現存しない。** D-58 は Mac 側部分が
  D-60 で撤回済みのため行そのものの扱いが未確定。参照先の是正は人間の判断待ち(DECISIONS は人間のみ変更)
- 手順書の設計方針: サーバーへ ssh しない / `git checkout` で branch を切り替えない(単一ディレクトリを
  複数セッションが共有しているため、branch 切替は他セッションの作業ツリーを壊す)。
  release branch は `git branch <名前> origin/develop` で作る — checkout を伴わないので安全
- 未実装: `develop` / `production` branch(未作成)、`gh` 認証(未実施)、pull 型 timer(本体未着手)。
  それまでのつなぎとして手順書に「手動デプロイ」節を残している

## デプロイ方式の実地投入で露出した3点(2026-07-21)

- **貼り付け用コマンドは折り返す長さにしない。** `ssh host 'a && b'` を渡したところ、
  ターミナル幅で折り返されて `git -C` の引数が次行に落ち、「fetch は成功したが checkout は失敗」
  という半端な状態になった。原因が分かりにくい。1コマンド1ブロックに分割する
  (zsh のインラインコメント禁止と同種の、手渡し用ブロックの制約)
- **`git branch <名> origin/monorepo` は上流も origin/monorepo にする。** develop / production を
  作った直後、両方が origin/monorepo を追跡していた。`git branch -u` で直す必要がある。
  放置すると `git status` / `git pull` が別ブランチと比較して混乱する
- **サーバー側 checkout は先に fetch が要る。** `checkout -B develop origin/develop` は
  remote-tracking ref がローカルに無いと `'origin/develop' is not a commit` で落ちる。
  staging web は事前の診断で fetch 済みだったため通り、lb だけ落ちて差が出た

投入結果(2026-07-21):
- staging web / lb = develop・dirty 0(get-pip.py は .gitignore で除外)
- prod web / lb = production(40e5e96 = prod の従前の配信内容)。4サイト 200 で無影響
- prod web は dirty 3(get-pip.py)。prod はまだ .gitignore 更新を受け取っていないため正常。
  ただし**この状態で deploy.sh prod を叩くと DIRTY で止まる**。初回本番デプロイの前に
  prod の get-pip.py を消しておく
- `production` は当初 origin/monorepo から作ってしまい、prod を 7/19 から今日の先端へ
  50コミット飛ばすところだった。prod の現在地(40e5e96)へ `git branch -f` で戻してから
  checkout した。**新しい branch を作って既存サーバーに載せるときは、branch の起点を
  サーバーの現在地に合わせる**(でないと checkout が無検証の一括デプロイになる)

既知の粗さ(未修正):
- `deploy_tick.sh` のサービス判定が host を見ていない。`loadbalancer/` の変更で web 側でも
  nginx を再起動し、`nginx-web-root/` の変更で lb 側でも再起動する。動作は壊れないが無関係な
  再起動が起きる。staging で挙動を観察してから直す

## 配信物のビルドがデプロイ経路に無かった(2026-07-21・本番で露出)

受賞企業ページの本番反映で、テンプレートと LESS は届いたのに **css が古いまま**で表示が崩れた。
`views/css` と `views/js` は `.gitignore` の生成物であり、ソースを配っただけでは配信に出ない。
`setup_*.sh` には front build があるが、**`deploy.sh` / `restart_*.sh` には無かった**(設計漏れ)。

実測:
- `award_company.less` 12519B(Jul 21 06:03・デプロイ済み)/ `main.css` 117017B(Jul 18 04:31・古い)
- repo の npm タスクは `--watch` 常駐用のみ。ワンショットは
  `npx babel src/js --out-dir js` と `npx lessc src/less/main.less css/main.css` を直接叩く

対応: `infra/run/build_thinkx.sh` を新設し、`deploy.sh` と `deploy_tick.sh` の restart 前に実行。
**条件分岐で「変わったときだけ」にしない**(判定を誤ると古い配信物を出し続ける)。冪等なので毎回実行する。

**サイトごとに事情が違う(未解決・要調査)**:

| サイト | views/src | css 追跡 | js 追跡 | ビルド配線 |
|---|---|---|---|---|
| thinkx | あり | 0 | 0 | **配線済み**(両方とも生成物) |
| kazukiotsukacom | あり | 0 | 7 | 未配線 |
| transformism | あり | 4 | 22 | 未配線 |

`transformism` と `kazukiotsukacom` は js/css の一部が **git 追跡されている**。babel/lessc は同じパスへ
書き出すため、生成物が commit 済みの内容と1バイトでも違えば **ビルドのたびに repo が dirty になり、
以後のデプロイが恒久的に止まる**。現状 3サイトとも dirty=0 なので一致しているようだが確証がない。
確認してから配線する。確認方法: 該当サイトでビルドを流し `git status --porcelain` が空のままか見る。

## ディスク実測(2026-07-21)

```
prod web    49G 中 8.9G (19%)  空き 40G   repo 3.0G / .git 935M
prod lb     20G 中 5.9G (31%)  空き 14G
staging web 20G 中  12G (58%)  空き 8.2G  ← 一番きつい
staging lb  20G 中 6.0G (32%)  空き 14G
```

Mac のローカルが 5GB 超なのは node_modules・venv・LFS 動画など git 管理外を含むため。
サーバーの clone は 3.0G。当面足りるが、**staging web は citywalk legacy 取り込みで 58% に上がった**。
citywalk を本格的に載せると効く。D-57(t3.medium 化)はメモリの話でディスクとは独立。

## 検証が旧サーバーを見ていた(2026-07-21・重大)

本番反映後の確認を素のドメイン(`https://truetechjapan.com` 等)で行っていたが、**これらは
DNS 未切替でオンプレ(123.226.234.127)を指している**。AWS のデプロイが成功しようが失敗しようが
200 が返るため、**検証として成立していなかった**。

```
thinkxinc.com / truetechjapan.com / transformism.art / kazukiotsuka.com  -> 123.226.234.127(オンプレ)
staging.*                                                                -> 52.68.142.190(AWS)
```

`deploy_production_from_staging.sh` の確認ブロックと手順書の確認 URL を、web へ直接当てる形
(`ssh supercom-web1` から `curl -H "Host: ..." localhost:800X`)に変更した。公開ドメインでの
確認は DNS 切替後に意味を持つ。

派生して判明したこと:
- 受賞企業ページの URL は `/truetechjapan/award/<company_key>`(`/award_companies/<key>` ではない)
- AWS 本番は4社とも 200・css も新ビルド(129944B)で、**デプロイ自体は完全に成功していた**
- LB の vhost は `prod.*` と `staging.*` のみで素のドメインを持たない。切替時に追加が要る

## deploy.sh の多バイト文字による unbound variable(2026-07-21)

`"...(origin/$br・再起動: ...)"` で `$br` の直後に多バイト文字 `・` が続き、`set -u` 下で
`br?: unbound variable` になった。**変数展開の直後が非 ASCII なら `${br}` と括る。**
全処理が終わった後の最終行だったため実害は無かったが、ラッパーが非ゼロ終了を見て
「FAIL: 反映が止まりました」と誤報した。

## 静的資産に Cache-Control が無い(2026-07-21・再発する)

受賞企業ページの本番反映後、`prod.truetechjapan.com` で表示が崩れて見えた。原因は**ブラウザキャッシュ**。
プライベートウィンドウでは正常に表示された(オーナー確認)。

切り分けの根拠 — staging と prod は**サーバー側で完全に同一**だった:

```
staging css : f49755422a5a515c17f2b81d9cfced5c  129944B
prod    css : f49755422a5a515c17f2b81d9cfced5c  129944B   (md5 一致)
staging page: 17543B / prod page: 17543B                  (一致)
```

`/css/main.css` のヘッダに `Cache-Control` が無く、`Last-Modified` と `ETag` のみ。
この場合ブラウザはヒューリスティックキャッシュを使い、`Last-Modified` からの経過時間の
約10%を勝手に「新鮮」と見なす。古い css を一度読むと数時間そのまま使われる。

**これは毎回のデプロイで再発する。** ファイル名が固定(`main.css`)なので、内容が変わっても
URL が変わらない。「本番に出したのに古いものが見える」は切り分けが難しく、今日は
「デプロイが失敗した」と誤認する原因になった。エンドユーザー側でも、変更前に訪れた人は
しばらく古い css を見る。

対応案(未着手・人間判断):
- ファイル名にハッシュを付ける(`main.<hash>.css`)。最も確実だがテンプレート側の参照を変える必要がある
- クエリで busting する(`main.css?v=<build>`)。軽いが CDN によっては効かない
- nginx で `Cache-Control` を明示する。即効性はあるが、短くすると毎回取りに行く

## 初回の本番デプロイが新フローで完走(2026-07-21)

`deploy_production_from_staging.sh` -> release/2026-07-21 の凍結 -> production への取り込み ->
サーバー反映 -> 受賞企業ページ4社が AWS 本番で 200。DNS は意図的に未切替(正しいデプロイの
確認後に切り替える方針・オーナー)。

途中で露出して修正した実バグ:
1. 配信物のビルドがデプロイ経路に無かった(css が古いまま)
2. 検証が素のドメイン = オンプレを見ていた(AWS の成否と無関係に 200 が返っていた)
3. `$br・` の多バイト文字で `unbound variable`(全処理後の最終行・実害なし・誤って FAIL 報告)
4. kaz が sudoers に居ないため timer が User=kaz では動かない(staging で露出)

## スクリプトの整理(2026-07-21・オーナー指示)

オーナー指摘3点をまとめて反映:

1. **`【分類: 変更系】` の表示をやめる。** `docs/coding_guides/bash.md` は「分類を冒頭コメントで
   宣言する」を規範として求めているが、オーナーは表示を不要と判断した。**規約と食い違うため記録する**
   (CLAUDE.md「上位と下位が食い違ったら上位に従い、食い違いを findings に記録する」)。
   bash.md を変えるかどうかは人間の判断。
2. **`sync_servers_from_origin.sh` を廃止。** 「これがいつ・何の場面で必要なのか分からない」が正しい。
   timer が全台に入れば Mac から同期を叩く場面は存在しない。デプロイの入口は
   `deploy_production_from_staging.sh` 1本だけにし、ssh の呼び出しはその中へ畳んだ。
   途中で止まった場合は**同じコマンドをもう一度実行する**(production に取り込み済みなら
   release を切り直さず反映だけやり直す)。覚えることが1つで済む。
3. **`build_thinkx.sh` を廃止し `build_and_restart.sh <service>` に統合。** サービスごとに
   ファイルを増やすのが誤り。あわせて `sync_from_origin.sh` が別に持っていた restart と
   verify のロジックもここへ集約した(また二重化していた)。

結果、この経路のスクリプトは3本:
- `infra/scripts/deploy_production_from_staging.sh` — 唯一のデプロイの入口
- `infra/run/sync_from_origin.sh` — この箱を origin に合わせる(timer と手動が共有する唯一の実装)
- `infra/run/build_and_restart.sh <service>` — 1サービスを作り直して再起動し応答を確かめる

## 箱ごとの担当判定(2026-07-21・実測)

web と lb は同じリポジトリを持つため、変更パスからサービスを判定すると「LB の設定変更で web を
巻き戻す」「lb で thinkx を起動する」が起きうる。実測で判別方法を確定した。

```
web : nginx active -> /src/thinkx-system/nginx-web-root/nginx.service   uwsgi_thinkx active
lb  : nginx active -> /src/thinkx-system/loadbalancer/nginx.service     uwsgi_thinkx inactive(ユニットは存在する)
web の nginx は 80 ではなく 8005/8006/8007 で listen(各 uwsgi の前段)
```

判定は2段:
1. **`systemctl is-active` で「この箱で現に動いているか」**。ユニットの有無では判別できない
   (lb にも uwsgi_thinkx のユニットが inactive で存在する。有無で判定すると lb で thinkx が起動する)
2. **nginx はどちらの箱でも動いているので、`/etc/systemd/system/nginx.service` の実体が
   どのディレクトリを指すか**で web(nginx-web-root)と lb(loadbalancer)を見分ける

誤り訂正: 一度「web は nginx を動かしていない(80 が応答しない)」と判断したが誤り。
web の nginx は 8005/8006/8007 で listen している。`curl localhost:80` の結果だけで
役割を推論したのが浅かった(オーナー指摘)。

## デプロイ経路の残件つぶし(2026-07-21・実測)

### staging の timer は「動くが自分の更新で必ずコケる」状態だった

`/usr/local/bin/deploy_tick.sh` は前日インストールされたコピーがそのまま動いていた。git 側で
`sync_from_origin.sh` に改名してもインストール済みのコピーは消えないため、timer は古い実装を
実行し続けていた。その古い実装は最後に「自分自身を git 上の `deploy_tick.sh` から入れ直す」ため、
存在しないファイルを参照して失敗し、異常終了の通知を出していた。

`:page_facing_up:`(成功)が混ざっていたのは、再起動が不要な回は入れ直しの手前で return して
いたため。**timer の入れ直しで解消する。**

### 自己更新が実行中のスクリプトを truncate していた(修正済み)

```bash
install -m 0755 "$REPO/infra/run/sync_from_origin.sh" "$SELF_INSTALLED"
```

`$SELF_INSTALLED` は実行中のファイルそのもの。`install` は同じ inode を truncate して書き直すので、
bash が読み進めている途中で中身が入れ替わる。冒頭コメントで「git が実行中のスクリプトを書き換えると
壊れるから複製側を動かす」と書いておきながら、その複製を自分で書き換えていた。**発火するのは
「このスクリプト自身が変わったデプロイのとき」だけ**なので、平時のテストでは出ない。

別名に置いてから `mv`(rename)に変更した。rename なら実行中の側は古い実体を読み続ける。

### 配信が非圧縮だった(修正済み)

```
Content-Length: 129944      ← main.css が非圧縮
Last-Modified: Mon, 20 Jul 2026 00:59:44 GMT
ETag: "6a5d7300-1fb98"
                            ← Content-Encoding なし
                            ← Cache-Control なし
```

`nginx.conf` に `gzip on;` はあったが **`gzip_types` が無い**。nginx の既定は `text/html` のみなので、
css・js・svg・json がすべて非圧縮で流れていた。`main.css` は 130KB → gzip で 20KB 程度になる。

`Cache-Control` の欠落(2026-07-21 の「本番が古く見える」の原因)と同じ場所なので、まとめて修正した。

### サーバー自体は遅くない(切り分けの記録)

```
staging web (localhost:8005, Host: truetechjapan.com)
  /ja/award/augmented-communications   ttfb 0.004s  17543B  200
  /css/main.css                        ttfb 0.001s 129944B  200
staging lb  (https 経由・TLS 込み)
  /ja/award/augmented-communications   ttfb 0.010s  17543B  200
```

アプリの生成は 4ms、LB 込みでも 10ms。「サイトが遅い」の原因はサーバー側の処理時間ではない。
(サイト側の診断は担当セッションの持ち場。ここは配信基盤の事実のみ記録する)

### 3サイトのコンパイル配線を確定(解決済み・懸案だった項目)

`transformism` と `kazukiotsukacom` は `views/js` `views/css` に git 追跡されたファイルが
残っており、「コンパイルが同じパスへ書き出して repo が恒久的に dirty になる」ことを懸念して
配線を見送っていた。実測で解消した。

```
                tracked css   tracked js   babel/lessc の出力先との衝突
thinkx              0             0        なし
transformism        4            22        なし(追跡物は common.css / lib/jQuery.js 等の実ソース)
kazukiotsukacom     0             7        js/main.js のみ重なるが、babel の出力とバイト単位で一致
```

staging 上で `npx babel src/js --out-dir /tmp/...` して `cmp` した結果、両サイトとも
`main.js` は追跡済みファイルと**一致**。`main.css` はどちらのサイトでも追跡されていない。
**dirty にはならないので、3サイトとも同じ形で配線した。** site 側のファイル構成は変更していない。

### 残件

- **ファイル名にハッシュを入れる**(`main.<hash>.css`)。`no-cache` は毎回の再検証で回避しているが、
  根本策ではない。テンプレート側の参照を書き換える必要があるためサイト側の仕事
- **`bash.md` との食い違い**(冒頭の分類宣言)。規約を変えるかは人間の判断(既出)

## スクリプトから呼ぶ git がページャを開いて止まった(2026-07-21)

`deploy_production_from_staging.sh` が本番に出す内容を表示したところ、`git log` が
ページャ(less)を開いて `(END)` で待ち、オーナーがそこから進めなくなった。

```
(END)  ← ここで止まる。q を押すまで先に進まない
```

`git log` は出力先が端末のとき既定でページャを開く。コマンド置換 `$(git log ...)` の
中では端末でないので開かず、**画面に直接出す1行だけが該当する**ため、開発中は気づきにくい。

対処: 端末へ直接出す git は `git --no-pager log ...` にした(4本すべて)。

一般則としては「スクリプトから呼ぶ git は必ずページャを切る」。`docs/coding_guides/bash.md`
に NG/OK として入れる価値があるが、規約の変更は人間の判断なのでここに記録する。

## 確認一覧が staging と本番で揃っていなかった(2026-07-21・修正済み)

本番デプロイの最後に当てる確認が3ドメインで、`truetechjapan.com` が入っていなかった。
**今日まさに変更したドメインが確認対象から漏れていた。** staging 側には入れたのに
本番側へ揃えるのを忘れたもの。両方を同じ4ドメインにした。

```
thinkxinc.com:8005  truetechjapan.com:8005  transformism.art:8006  kazukiotsuka.com:8007
```

同種の漏れは今日2件目(1件目は検証が素のドメイン=オンプレを見ていた件)。**確認の対象は
配信しているものから機械的に導くべきで、手で並べる限り漏れる。** nginx conf の
`server_name` から起こす案があるが、`nntm.thinkxinc.com` `nntmapp.com` など確認の
要否が分かれるものもあるため、実装は要検討として残す。

## 同期が途中で死ぬと、その回の再起動は二度と拾われない(2026-07-21・構造上の穴・未修正)

`sync_from_origin.sh` は「前回の HEAD と今回の HEAD の差分」から再起動するサービスを決める。
そのため **merge が済んだあとに再起動の手前で落ちると、次回以降の差分にはもう現れない**。
設定はサーバーに届いているのに、それを読み込むプロセスが永久に再起動されない状態になる。

実際に起きた。staging web で古い `deploy_tick.sh` が merge だけして自己更新で落ちており、
`nginx.conf` の gzip / Cache-Control が届いていたのに nginx が古い設定のまま動き続けていた。

```
staging web の checkout : d34cdec(最新)
staging web の配信ヘッダ : Content-Length のみ(gzip も Cache-Control も無い)
本番 web の配信ヘッダ   : Content-Encoding: gzip / Cache-Control: no-cache
```

**本番のほうが staging より新しい設定で動く、という逆転が起きた。** staging で確認してから
本番に出す、という前提が崩れる種類の不整合である。

直すなら「再起動まで終わって初めて反映済みとする」形(HEAD とは別に反映済みマーカーを持ち、
マーカーと HEAD が食い違っていたら再起動からやり直す)。設計変更になるため今日は入れていない。

暫定の対処は手で再起動する:

```
ssh supercom-web1-stg 'sudo bash /src/thinkx-system/infra/run/build_and_restart.sh nginx-web-root'
```

## 2回目の本番デプロイが新フローで完走(2026-07-21)

`deploy_production_from_staging.sh` → release/2026-07-21-2 の凍結 → production 取り込み →
4台反映 → 確認。**今日書き換えた経路がすべて実地で通った。**

```
HEAD    3b886dc Merge pull request #10 from ThinkXInc/release/2026-07-21-2
dirty   0
Cache-Control: no-cache          新規に効いた
Content-Encoding: gzip           新規に効いた(Content-Length が消える = チャンク転送)
受賞企業ページ  200 / 17543B
/usr/local/bin/sync_from_origin.sh  09:09 に配置(初回ブートストラップが動いた証拠)
```

初回ブートストラップ(`git show origin/production:infra/run/sync_from_origin.sh | ssh ... 'sudo bash -s prod'`)
はこの回がはじめての実行だった。本番 web にはこのファイルが無かったので、これが無ければ
ここで止まっていた。

箱ごとの担当判定も実地で正しく働いた。lb1 では `skip: この箱(lb1)の nginx は nginx-web-root の
設定で動いていない` `skip: thinkx はこの箱(lb1)で動いていない` が出て、lb で thinkx を
起動する事故は起きなかった。

## 一度も発火していない経路(2026-07-21 時点)

**戻し(rollback)。** `build_and_restart.sh` が非ゼロを返したときに `reset --hard` で直前へ戻し、
再度ビルドして通知する経路が、実装以来まだ一度も動いていない。意図的に staging を壊して
確認する必要がある。ここが今いちばん検証されていない。

## git 管理外の実アセット(動画)を本番へ運ぶ経路が実質欠けていた(2026-07-21・修正済み)

staging に置いた動画が本番へ運べない、として露出した。調べると経路そのものは D-40 で
決まっており `infra/etc/push_assets.sh` が存在したが、**送るだけで展開しない**作りだった。

```
push_assets.sh  ->  host:/tmp/<site>-video.tgz  で終わり
展開は setup_<site>.sh の役目(D-40)
```

新規構築ではこれで成立するが、**既に動いている箱に対しては「送ったのに反映されない」で
終わる**。動画を差し替えるたびに setup を流し直すのは現実的でない。展開と chown まで
push_assets.sh が行うようにした。`/tmp` の tgz は setup_<site>.sh が期待する形なので残す。

危険なのは順序である。動画は `.gitignore` の対象なので git では運ばれない。**HTML の
参照だけが先に本番へ行くと、存在しないファイルを指して 404 になり背景動画が消える。**
動画を差し替えたときは、デプロイの前に push_assets.sh を実行する。

改善余地: 転送量が views/video 全体になる(thinkx で 347MB)。mp4 は圧縮が効かないので
実サイズがそのまま流れる。差分だけ送る形(rsync)にできる。

## 編集した箱では、その変更が「差分」に現れない(2026-07-21・構造上の性質)

staging web の上で編集して commit した場合、その箱の HEAD には既にその変更が入っている。
次の同期では `prev..new` の差分に現れないため、**編集した箱だけがコンパイルと再起動を
行わない**。他の箱は差分に現れるので正しく処理される。

実際に `deploy_staging.sh` の出力で、web1-stg は何も出ず、lb1-stg だけが
`skip: thinkx はこの箱で動いていない` を出す、という非対称が観測された。

今回は担当セッションが手で再起動していたため実害は出ていない。「同期が途中で死ぬと
再起動が二度と拾われない」と同じ根(差分を反応の起点にしていること)であり、
反映済みマーカーを持つ設計に変えれば両方が同時に解ける。

## アセット配布をデプロイに組み込んだ(2026-07-21・オーナー指示)

**原文**: 「このETCプッシュアセットというものはかなり忘れそうなので、デプロイの手順と
一体化されているべきだと思うが。つまり、ローカルで何かアセットが変更されていたら、
それを検出して、このプッシュアセットをデプロイのプロセスのどこかで実行するという」

`deploy_staging.sh` と `deploy_production_from_staging.sh` の**サーバー同期の手前**で
`push_assets.sh` を呼ぶようにした。手前に置くのが要点で、HTML の参照だけが先に行くと
存在しないファイルを指して 404 になる。

置き場所も `infra/etc/` から `infra/scripts/` へ移した。`etc/` の他の中身
(`push_env` `push_secrets` `push_rw_key` `push_discord_webhook` `push_ref`)は
**セットアップ時に一度配れば済む秘密や鍵**だが、アセットは**デプロイのたびに走る**。
性質が違うので線を引いた。

### 順序の等価性で嵌った(実測)

一致判定を「ファイル名とサイズの一覧の突き合わせ」で作ったところ、**中身が同じなのに
毎回 347MB を送り直す**状態になった。macOS と Linux で `sort` の照合順序が違い、
並びだけがずれていた。

```
箱のみ   ./VNMachineCloudIntro1.1.mp4 148026838
手元のみ ./VNMachineCloudIntro1.1.mp4 148026838   ← 同じものが両側に出る
```

`LC_ALL=C sort` で両側を同じ規則に揃えて解決。**突き合わせに使う一覧は、必ず両側で
同じ規則で並べる。** 修正後は一致判定が 0.5 秒で返るようになった。

一般則として、環境をまたいで比較するものは照合順序・タイムゾーン・改行コードを
明示的に固定する。ここは macOS(Mac)と Linux(EC2)をまたぐので特に効く。

## 3回目の本番デプロイ — アセット配布込みで完走(2026-07-21)

動画を差し替えた回。アセット配布をデプロイに組み込んだ直後の実走で、**組み込みが
無ければ HTML だけが本番へ行って 404 になっていた**ケースそのものだった。

```
アセット(views/video)を確かめる
  thinkx: アセットが supercom-web1 と違うので配ります
  thinkx-video.tgz  100%  343MB  46.6MB/s  00:07
  OK: thinkx の video を supercom-web1 へ配って展開した

supercom-web1 -> production に合わせる
  skip: この箱(web)の nginx は loadbalancer の設定で動いていない
  == compile thinkx ==  Successfully compiled 3 files with Babel (374ms)
  == restart thinkx (uwsgi_thinkx) ==  OK: thinkx -> 200

supercom-lb1 -> production に合わせる
  == restart loadbalancer (nginx) ==  OK: loadbalancer -> 200
  skip: thinkx はこの箱(lb1)で動いていない
```

反映後の実測:

```
/src/thinkx/web-server/views/video/
  Sitetop2025_7_13noaudio.mp4       13M  kaz:serveradmins
  VNMachineCloudIntro1.1_21MB.mp4   20M  kaz:serveradmins
配信 206 / 206
HTML が指す先と実ファイルが一致(404 なし)
```

箱ごとの担当判定が本番の両方で正しく働いた。web は loadbalancer を飛ばし、lb は
thinkx を飛ばし、それぞれ自分の担当だけを再起動している。

### 通知文の読みにくさが1つ残った

`skip: この箱(web)の nginx は loadbalancer の設定で動いていない` は**正しい判定**だが、
「web の nginx が壊れている」と読めてしまう。意味は「今チェックしているのは loadbalancer
というサービスで、この箱の nginx はその設定では動いていないので担当外」である。
`skip: loadbalancer はこの箱(web)の担当ではない(nginx は nginx-web-root の設定で動作中)`
のように、主語を揃えたほうがよい。次のセッションで直す。

## 本番の3サイト構成(2026-07-21 時点・実測)

```
supercom-web1  nginx = nginx-web-root の設定    uwsgi_thinkx active
supercom-lb1   nginx = loadbalancer の設定      uwsgi_thinkx inactive(ユニットのみ存在)
```

## 2026-07-22 develop→monorepo 戻しをリモートPR方式へ(D-68)+ bash.md の陳腐化参照

- 共有チェックアウトでローカル `git merge origin/develop` を実行したところ、並行 citywalk
  セッションが `git add` していた WIP を merge commit(42a11bf)が丸ごと拾った(オーナー裁定で
  そのまま維持・未 push)。対策として develop→monorepo をリモート PR + ローカル ff に変更(D-68)。
- 実装: `pr_develop_and_merge_to_monorepo.sh` を新設、旧 `merge_develop_into.sh` を廃止。
- **規範への影響(自分では直せない)**: `docs/coding_guides/bash.md:118-119` が使い方メッセージの
  例として旧 `merge_develop_into.sh` を引いている。coding_guides は規範=人間のみ改変可のため
  未変更。人間が例を `pr_develop_and_merge_to_monorepo.sh` 等へ差し替えるか判断されたい。

## 2026-07-22 DNS切替 step1: acceptance の /filedrop が本番で偽 NG

- `acceptance-sweep.sh 52.197.179.70`(本番 LB 直)で `NG expect=200 got=404 /filedrop`(thinkx 1/59)。
- 原因: filedrop は `thinkx/web-server/main.py:787` で **hostname が `-stg` のときだけ有効**な
  staging 専用機能。本番(supercom-web1・-stg なし)では 404 が正。golden が staging 専用ルートを
  200 期待に含んでいる。**本番の障害ではない。**
- 他は全 green(check_request_path 全ホップ・3ドメイン end-to-end https 200・kazuki 4/4・transformism 2/2)。
- 対応方針(TODO): 本番向け acceptance golden から /filedrop を除外するか、環境で期待値を分ける
  (staging=200 / prod=404)。DNS 切替のブロッカーにはしない。

## 2026-07-22 DNS切替の確認対象漏れ: truetechjapan / nntmapp / jessicas.online

- DNS切替手順.md と acceptance-sweep.sh はいずれも **3ドメイン(thinkxinc / kazukiotsuka /
  transformism)決め打ち**。LB の server_name には他に **truetechjapan.com・nntmapp.com・
  jessicas.online(いずれも +www)・nntm.thinkxinc.com・quantz.thinkxinc.com** がある。
  「確認対象を手で並べると漏れる」の再発(handoff 未解決事項)。オーナーが切替時に気づいた。
- 根治方針(TODO): acceptance-sweep / DNS確認の対象ドメインを **loadbalancer の server_name から
  自動生成**する(bare apex + www を抽出、staging.*/prod.*/internal を除外)。決め打ちリストを廃す。
- 切替そのものはオーナーが全 A を差し替え済み。要・全ドメイン実地確認(dig + https)。

## 2026-07-22 DNS本番切替 完了(apex 5 + nntm)/ quantz は据え置き / www 見送り

- 切替完了(全て 52.197.179.70・https 200): thinkxinc.com / truetechjapan.com / nntmapp.com /
  transformism.art / kazukiotsuka.com / nntm.thinkxinc.com。オンプレ(123.226.234.127)から AWS LB へ。
- **quantz.thinkxinc.com = AWS で 500。ただし切替前もオンプレで 500(回帰ではない)。**
  原因: AWS 本番は uwsgi 3つ(thinkx/kazukiotsukacom/transformism)のみで quantz app 未搭載なのに
  LB が quantz.thinkxinc.com を quantz upstream へ流している。判断(別トラック): quantz を載せる /
  server_name を外して畳む / 放置(元から 500 でユーザー影響不変)。
- **www.*(thinkxinc/truetechjapan/nntmapp)= A レコード無し。据え置き(オーナー判断 2026-07-22)。**
  apex 専用で索引がきれい。必要時に A(52.197.179.70)追加 + www→apex 301 確認で対応。
- 戻し口: Route53 で各 A を 123.226.234.127 に戻す(オンプレ温存・DNS切替手順 §5)。

## 2026-07-22 filedrop 偽NG 解消(acceptance-sweep 側で対象外に)

- 原因の正確な所在: acceptance-sweep は Host を常に公開名(thinkxinc.com)で当てるが、filedrop は
  main.py:787 で hostname が -stg のときだけ有効。よって env に関係なく sweep では常に 404。
- 対応(実施): golden(サイト単体テストが正)は触らず、acceptance-sweep.sh で `thinkx:/filedrop` を
  受け入れ対象外にし skip 行を出す(黙って落とさない)。実測: thinkx 58/58・ACCEPTANCE 全 green。
- 波及ルールが増えたら acceptance-sweep.sh の case に足す。

## 2026-08-06 start_staging.sh の待ち時間が表示(最大120秒)より長い

- 事象: staging 起動時、Discord の起動通知が来ているのにスクリプトは
  「ssh 到達と主要サービスを確認中(最大 120 秒)...」のまま待ち続けた。
- 原因1(表示と実態の乖離): ループが ssh ConnectTimeout=5 + sleep 5 × 24周で、
  ssh が沈黙する間は1周最大10秒 → 実際は最大約4分待ち得た。
- 原因2(観測対象の違い): Discord 通知はブート初期(ネットワーク up)に飛ぶが、
  スクリプトの OK 条件は「ssh 到達 + nginx と uwsgi_thinkx が active」。
  サービス起動完了はブート通知より数十秒遅れるため、体感差が出る。
- 対応(実施): ConnectTimeout=3 + sleep 2(1周≦5秒 × 24 = ちょうど120秒)に短縮。
  検知遅延は最大10秒→5秒に。次回の staging 起動が実流し検証を兼ねる。

## 2026-08-06 push_assets: ssh 不達だと「箱が空」に見える / .DS_Store 混入

- 事象: staging デプロイで assets 確認の diff が「箱のみ」空・「手元のみ」11本
  (計約384MB)と出た直後、scp が `port 22: Operation timed out` で FAIL。
  真因は SG の接続元 IP 許可リスト(手元 IP の変化)で、箱側一覧の取得(ssh)も
  同じ理由で失敗して空扱いになっていた。**「箱が空」と「ssh 不達」が同じ見た目**
  になるのは誤診を誘う — push_assets.sh は一覧取得の ssh 失敗を transfer 失敗と
  区別して報告すべき(未実施・要修正)。
- 手元のみ一覧に `.DS_Store`(6148B)が含まれ配布対象になる。実害は小さいが
  ゴミの同期は不要。除外(-name .DS_Store の類)を足すべき(未実施・要修正)。
- 対処ルーチン: `add_current_office_ip.sh` で現 IP を許可 → deploy_staging.sh 再実行。

## 2026-08-06 【事故】add_current_office_ip.sh の auto-approve apply が prod/staging 全4台を破壊再作成

- 経緯: SSH 締め出し(手元 IP 変化)の解消に add_current_office_ip.sh を実行。
  同スクリプトは terraform apply を **-auto-approve** で prod/staging の両 env に
  実行する実装だった(ヘッダーコメントは「承認プロンプトで yes」と記載しており
  実装と乖離)。apply には IP 追加と無関係の **AMI 追従差分**(data.aws_ami
  most_recent が新 Ubuntu AMI を検出 → ami 変更は ForceNew)が同乗しており、
  **web/lb × prod/staging の4台が破壊→新規作成**された。EIP は台帳(D-53)により
  保持=IP・DNS 不変。旧ルート EBS はインスタンスと共に削除。
- 症状: 全公開サイト connection refused(新品 Ubuntu に nginx 無し)。ssh は
  「REMOTE HOST IDENTIFICATION HAS CHANGED」(同一 IP に別マシン=入替の証拠)。
  Discord への異常通知は無し(外形監視が存在しない)。
- 復旧: 構築手順.md により prod → staging の順で再構築(箱=terraform は事故 apply
  で新規作成済みのため手順4以降)。known_hosts は ssh-keygen -R で旧鍵を掃除。
- 恒久対処(実施済み・本コミット):
  1) add_current_office_ip.sh: -auto-approve を廃止し、apply を
     -target=aws_security_group.{web,lb} に限定。IP 追加が SG 以外の差分を
     巻き込む経路を構造的に遮断。
  2) instances.tf: aws_instance {lb,web} に lifecycle ignore_changes = [ami]。
     新 AMI 公開のたびに「要再作成」差分が潜伏する地雷を除去(新 AMI は意図した
     建て直しのときだけ拾う)。terraform fmt/validate 済み。apply は次回の
     承認付き実行で反映(コード変更のみでは挙動に影響しない)。
- 教訓: 「スクリプトのヘッダー記述」と「実装」の乖離は致命傷になる。terraform apply
  を含むスクリプトは (a) 承認プロンプト必須 (b) 目的リソースへの -target 限定
  (c) 事前 plan の要約提示、を規約化すべき(規範化は人間判断・要 D-xx 起票)。

## 2026-08-06 TODO: 外形監視+Discord 通知が無い(本番ダウンに気づけない)

- 今回の全損時、Discord には何の通知も出なかった(ダウン検知の仕組み自体が無い)。
- 最小構成案: 常時稼働の k00bot2 EC2 の cron で5分毎に全サイト
  (thinkxinc/truetechjapan/transformism/kazukiotsuka/nntm/staging)へ curl し、
  非 200 が続いたら Discord webhook へ通知。復旧通知も出す。
- オーナー指示(2026-08-06 原文):「ダウンしたら知らせる仕組みがないので、
  これはTODOにしておかなければいけない」

## 2026-08-06 復旧進捗メモ(全損事故からの再構築・prod)

- 完了: web 基盤(setup_user/setup_webserver: python3.9/node/nginx/mongod 揃い)、
  deploy key 検証(3鍵)、monorepo clone(web/LB とも・checkout は monorepo)、
  .env 配布(thinkx/kazukiotsukacom/transformism/loadbalancer)、
  動画アセット11本配布、setup_nginx-web-root(8005 応答)、
  setup_thinkx(8005->200)、setup_kazukiotsukacom(8007->200)、
  setup_loadbalancer(exit 0・詳細ログ未精査)。
- 未了: setup_transformism(実行直前にオーナー中断→再開時にネット断で不達)、
  LB ログ精査、check_request_path、acceptance-sweep、
  本番 checkout の production ブランチ同期(sync_from_origin prod)、staging 再構築一式。
- 備考: 2度の setup_webserver FAIL の原因は (1)二重実行の apt ロック衝突
  (2)新品初回ブートの unattended-upgrades のロック。3回目は単独実行+ロック解放
  待ちで成功。setup 冒頭に apt ロック解放待ちを入れる改修を提案(要承認)。

### F-I(2026-08-07): staging の箱は空(中身が未構築)。push_assets はそれを「中身が違う」と誤表示する

- 事象: `deploy_staging.sh` が `tar: /src/thinkx/web-server/views: Cannot open: No such file or directory`
  で FAIL。その手前で毎回「アセットが supercom-web1-stg と違うので配ります」が出て
  343MB を送っていた。
- 実測(読み取りのみ): supercom-web1-stg / supercom-lb1-stg とも uptime 約20時間、
  `/src` が存在しない、`kaz` ユーザーなし(home は ubuntu のみ)、nginx inactive、node 未導入。
  箱(EC2)は在るが**中身(setup 一式)が未構築**。prod (supercom-web1) は `/src/thinkx-system` あり。
- 原因: 全損事故後に prod を再構築した一方、staging の中身は再構築していない
  (infra/CLAUDE.md D-32-2 は「staging 再構築はカットオーバー後」)。空箱に対して
  デプロイ経路だけが従来どおり動こうとした。
- ツール側の欠陥(別件として残る):
  1. `push_assets.sh` は remote の一覧取得を `2>/dev/null` で握りつぶすため、
     「箱に views/video が無い」と「中身が違う」を区別できず、前者を後者として表示する
     (2026-07-24 の「箱が空 = ssh 不達の誤表示」と同型の再発)。
  2. 転送先の存在確認より先に 343MB を scp するので、失敗が最後まで分からない。
     宛先の存在確認(安価)を先に行い、無ければ「箱が未構築」と言って即座に止めるべき。
  3. ローカル `views/video/.DS_Store` が一覧にもアーカイブにも入る(既知)。
- 対処の選択肢: (a) staging の中身を prod と同一手順で再構築する(I-STEP3 前倒し・人間判断)
  (b) staging を使わず production へ出す(受け入れの後退なので非推奨)
  (c) ツール側の誤表示と fail fast だけ先に直す(箱が空である事実は変わらない)

### F-I(2026-08-07): 手順書が実在しないパスを指していた(`infra/etc/push_assets.sh`)

- `push_assets.sh` は `infra/etc/` から `infra/scripts/` へ移した(GUIDELINES「etc/ と scripts/ の線引き」
  2026-07-21)が、実行用の手順書3本が旧パスのまま残っていた:
  `docs/構築手順.md`(7章)・`docs/運用.md`・`docs/DNS切替手順.md`。貼れば
  `No such file or directory` で止まる。staging 再構築の最中に踏む位置にあった。
- 対処: 3本を `infra/scripts/push_assets.sh` に修正。DECISIONS / GUIDELINES / 引き継ぎ・
  discussion の記述は当時の記録なので変更しない(履歴であって手順ではない)。
- 再発防止として、手順書に出てくる `*.sh` / `*.py` のパスが実在するかを機械的に照合した
  (構築手順・運用・DNS切替・デプロイ手順書の4本。現在 MISSING なし):
  `grep -rhoE "(infra|thinkx)/[A-Za-z0-9_./-]+\.(sh|py)" <docs> | sort -u | while read -r p; do [ -e "$p" ] || echo "MISSING: $p"; done`
  この照合をスクリプト化して CI 的に回すかは人間の判断(提案)。

## 2026-08-07 全損事故からの復旧完了(prod/staging とも受け入れ green)

- prod: 基盤(python3.9/node/nginx/mongod)→ clone → .env/assets → 3サイト(8005/8006/8007
  すべて 200)→ LB(TLS renewal 全件 dns-route53)→ sync_from_origin prod(9b4aacb =
  release/2026-08-06 merge)→ check_request_path 全ホップ green → acceptance 全サイト green。
  公開 URL 全 200(イベントページ /event/philsemi2609.html 含む)。
- staging: 同一手順で再構築 → pr_and_merge_to_develop で develop を先端化 →
  deploy_staging.sh で同期 → acceptance 全サイト green。Basic 認証(401)は維持。
- 途中の躓きと対処:
  1) 携帯回線(docomo CGNAT 1.73.x)から ssh 不達。checkip の出口 IP を /32 許可しても
     不達で、**CGNAT はフローごとに出口 IP が変わり得る**と判断。復旧作業の間だけ
     1.73.0.0/16 の 22 番を4SGに一時許可し、完了後に /16・/32 とも削除済み
     (SG は terraform 管理の3件のみに復元済み・実測確認)。
  2) 新品初回ブートは unattended-upgrades が apt ロックを保持し setup が失敗し得る
     (prod で2回失敗)。ロック解放を確認してから流すと成功。setup 冒頭への
     ロック待ち組み込みを提案(要承認)。
- 残課題: 外形監視+Discord 通知(TODO 起票済み)/ add_current_office_ip.sh の
  非対話モード(Claude 代行時に terraform の対話承認ができない)/
  setup 冒頭の apt ロック待ち(要承認)。

### F-I(2026-08-07): 手順書に `<...>` のプレースホルダを残さない(オーナー指摘)

- 指摘: `git add <出すファイル>` / `git commit -m "<何を変えたか>"` のような穴あきブロックは
  「上から貼れば完走」を満たさない。貼る側が毎回考える手順は手順ではない。
- 対処: `docs/デプロイ手順書.md` から `<...>` を全廃した。
  - commit は編集ディレクトリ単位に固定(`git add thinkx/` / `git add infra/`)。
    `git add -A` 禁止(D-68)と両立し、かつ貼れる形。message は既定文言を置き、
    必要なら `git commit --amend -m` で直す。
  - `acceptance-sweep.sh <LB_IP>` は `"$(terraform_output.sh prod lb_public_ip)"` に置換して
    値の手写しを無くした。
  - rollback の日付だけは値の選択が必要なので、`BACK_TO=release/2026-08-06` の
    1行ブロックに隔離し、以降のブロックは `"$BACK_TO"` を参照するだけにした。
- 規則: 値の選択が要る箇所は、コマンド中に穴を空けず「変数を1行で置くブロック」に隔離する。

## 2026-08-07 deploy timer が staging にも prod にも入っていない(全損復旧で欠落)

- 事象: release/2026-08-07-2 を production へ merge(PR #33)しても、3分間・12回の
  curl 実測で本番 `https://thinkxinc.com/event/philsemi2609` が旧内容のまま
  (`.hero-date { font-size: 10px; ... }`)。`origin/production` には新内容が入っている
  ことを `git show origin/production:...` で確認済みなので、サーバーが追従していない。
- 原因: **`deploy-timer@<env>.timer` が存在しない。** staging(web1-stg)で実測すると
  `systemctl list-unit-files | grep -i deploy` が空、`list-timers` も空。
  `/usr/local/bin/sync_from_origin.sh` は 02:52 に配置されているのにユニットが無い。
  2026-08-06 の全損事故でインスタンスが破壊再作成された際、`setup_deploy_timer.sh` が
  再実行されなかったためと考えられる。復旧記録(本ファイル「2026-08-07 全損事故からの
  復旧完了」)の手順にも timer の再導入は列挙されておらず、prod は
  `sync_from_origin prod` を人手で1回叩いて同期させている。
- 影響: **merge しても本番に出ない。** 誰かが手で sync を叩かない限り反映されない。
  D-50 で定めた L2b の経路(「マージ → timer が 60 秒以内に反映」)が成立しない。
- 対処(オーナー機から。staging から prod へは名前解決できない):
  `ssh supercom-web1 'ENVX=prod bash /src/thinkx-system/infra/setup/setup_deploy_timer.sh'`
  同スクリプトは unit の登録・enable に加えて `systemctl start deploy-timer@prod.service`
  まで行うので、導入と同時に今回の release が反映される。staging も同様に ENVX=staging で。
- 再発防止: 復旧手順(構築手順.md)の完了条件に「`systemctl list-timers deploy-timer@<env>.timer`
  が active」を入れる。箱を作り直すと消える設定は、受け入れ試験の項目に入っていないと
  必ず落ちる(今回は「全サイト 200」が green だったため欠落に気づけなかった)。

## 2026-08-07 squash merge が deploy_production_from_staging.sh の冪等判定を壊す

- 事象: PR #33 を **squash** で merge したため、`origin/production` は
  `ff762ca Release/2026 08 07 2 (#33)` という単一コミットになり、元の6コミットは
  祖先に含まれない。内容は同一。
- 影響: `deploy_production_from_staging.sh:31` の
  `git merge-base --is-ancestor "$sha" origin/production` が常に false になり、
  「production は既に staging の内容を含んでいます」の分岐に入らない。
  同じ内容でもう一度 release を切って PR を作りにいく(空 PR で失敗しうる)。
- 対処案(未実施・要判断): (a) merge 方法を Merge commit に統一する
  (ruleset の Allowed merge methods を Merge のみにすれば強制できる) /
  (b) 判定を sha の祖先関係でなく tree の一致(`git rev-parse origin/develop^{tree}` と
  `origin/production^{tree}` の比較)に変える。(b) の方が merge 方法に依存しない。
