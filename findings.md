# findings — M トラック(monorepo 取り込み)

実行中に気づいた点・逸脱・人間の残作業を記録する台帳。規範は `docs/MONOREPO_PLAN.md`。

## M-F1: cp/rsync の権限を deny → ask に一時変更(2026-07-15・オーナー裁定)

- 経緯: M-2(リポジトリごとの作業ツリーコピー)で `cp`/`rsync` が必要だが、ワークスペース
  `.claude/settings.json` は `Bash(rsync:*)` / `Bash(scp:*)` を deny していたため実行者がコピー
  できなかった(M-1 の制御文書コピーはオーナーが手動 rsync で実施)。
- 裁定: オーナーが `cp`/`rsync` を **deny → ask** に変更。M-2 は各リポジトリのコピー実行時に
  承認プロンプトが出る形で実行者が進める。
- **正とするコピーコマンド: `rsync -a --exclude=.git <src>/ <dest>/`**(無加工・`.git` 除外)。
- **人間の残作業(M 完了後): `cp`/`rsync` を deny に戻す。** → 完了報告に明記する。

## M-F2: monorepo/CLAUDE.md 冒頭が polyrepo 前提のままで monorepo と矛盾

- `CLAUDE.md` 冒頭「ワークスペース自体は git 管理しない。各サブディレクトリが独立した git
  リポジトリ(clone)である」は、単一 git リポジトリである monorepo では事実に反する。
- M-1 の指定範囲は「歴史調査は ARCHIVE.md 経由」の**1行追記のみ**のため、冒頭記述は未修正で残した。
- CLAUDE.md の monorepo 向け全面改訂は M の範囲外(人間判断・後工程)。

## M-F3: コピー欠落の検出と忠実復元(M-3・重要)

- 各リポジトリの `.gitignore`(root monorepo + 各リポジトリ + jquery/remodal 等の nested)を
  git が尊重するため、**origin が `.gitignore` に反して force-add していた追跡ファイルが
  monorepo の初回 `git add` で脱落**した。「元の追跡ファイル一覧 vs monorepo 追跡一覧」の
  突合(`core.quotepath=false`)で検出:
  - `kazukiotsukacom`: 10件(`web-server/views/js/*.js` 7 + `web-server/views/jslibs/jquery/dist/*` 3)
  - `thinkx`: 1件(`web-server/venv/.gitkeep`)
  - `transformism`: 33件(`web-server/views/css/*`・`web-server/views/js/**`・`jslibs/{jquery,remodal}/dist/*`)
- 対処: 計画「コピーは無加工(origin 忠実)」に従い **`git add -f` で忠実復元**。突合再実行で
  実欠落ゼロを確認。`.gitignore` ルール自体は生成物用に残置(最小修正・M-3 方針)。
- 教訓: ファイルコピー方式では per-repo/nested `.gitignore` による force-add 資産の脱落が起きる。
  取り込み後は毎回「origin ls-files vs mono ls-files」で突合すること。

## M-F4: 除去した submodule メタデータ

- `thinkx/.gitmodules`(playbooks・ピン 38bf25a を M-2 で実体焼き込み済み)を除去。
- `transformism/.gitmodules`(`www/playbooks` を宣言するが 2026refactor HEAD のツリーに gitlink
  実体が無い**孤立メタデータ**。焼き込む submodule 無し)を除去。

## M-F5: 相互参照(発見のみ・修正は人間/infra 管轄・monorepo で要改訂)

polyrepo 前提の兄弟リポジトリ参照を検出。monorepo では意味が変わるが M の範囲外(記録のみ):

- `bootstrap.sh` — 兄弟リポジトリを個別 clone する polyrepo ブートストラップ。monorepo では不要/要改訂。
- `infra/setup/setup_quantz.sh` L31–33 — libcommon/llm/simplicity の deploy-key ホストエイリアス
  (`git config url.insteadOf`)。polyrepo の per-repo clone 前提。
- `thinkx/playbooks/README.md` — `git submodule add playbooks` の歴史的記述(無害)。

## M-F6: 【停止】M-4 秘密検査で実秘密を検出(値は記録しない)

M-4(秘密機械検査)で、**追跡ファイルにコミットされた実秘密**を検出。計画「実体は検出したら
即停止・報告」に従い M を停止(M-5/M-6 未着手・push していない)。値は本台帳に書かない(所在のみ)。

**検出(実秘密・要対処):**
- `thinkx/playbooks/roles/vpn/templates/ipsec.secrets_1` / `_2` — VPN の実 PSK(テンプレ変数でなく実値+実 IP)。
- `infra/docs/raw/` の4ドキュメント(quantz local / DB Server Supercom3c / Setup Supercom3a /
  Setup Supercom2)— **AWS フル資格情報(ACCESS_KEY_ID + SECRET_ACCESS_KEY)を .env 貼り付けで含む**。
- `infra/findings.md` — AWS ACCESS_KEY_ID を平文列挙。
- `thinkx/playbooks/api` / `web`(+ `roles/{api,web}/tasks/main.yml`)— ansible inventory に AWS 資格。

**良好(正しく gitignore・未追跡):** `infra/certs/` `infra/deploykeys/` `infra/terraform/terraform.tfstate(.backup)`
`infra/terraform/terraform.tfvars`、各サイトの `.env`(kazukiotsukacom/loadbalancer/thinkx/transformism)。
`push_secrets.sh` は値の埋め込み無し(安全)。`config.py`/`mail.py`/`send_mail.py` の
`AWS_SECRET_ACCESS_KEY`/`PASSWORD` 参照は環境変数経由の可能性が高い(要確認だが直値ではない見込み)。

**重要な前提:** これらは**旧リポジトリ(thinkx / infra)に既にコミットされている既存露出**で、M が
新たに作った漏洩ではない。ただし M-6 で新 GitHub リポジトリへ運ぶことになる上、**AWS 資格情報・
VPN PSK は現用の生き秘密**であり、旧 GitHub に露出済みである以上、monorepo からの除去とは別に
**ローテーション(無効化・再発行)が必要**。

**オーナー裁定(2026-07-15)と対処状況:**
1. `thinkx/playbooks`(VPN PSK + ansible inventory の AWS 資格)→ **不使用のため monorepo から
   丸ごと除外**。`git rm -r thinkx/playbooks` 実施済み。
2. `infra/docs/raw/` の文書群 + `infra/findings.md` → **該当秘密の値のみ redact**(`<REDACTED>`)。
   実施済み(AWS ID/SECRET・FLASK_APP_SECRET_KEY・PASSWORD_ENCRYPT_KEY・STRIPE_SECRET_KEY・
   各 RABBITMQ/MONGO_DB_PASSWORD 等。テンプレ `${...}` と `LLM_MAX_TOKENS` は非対象)。
3. `libcommon/discord.py:21` の Discord webhook URL 直書き(原本+vendored 計5コピー)→
   **オーナー裁定(2026-07-15・改訂): これはデモ用 webhook でありセキュリティ上問題なし。
   そのまま残置・対処不要。** M-4 のブロッカーは解消し M を続行。
   (AWS キー・VPN PSK のローテーションは引き続き別トラックの是正対象。)

**確認済み(誤検出・実秘密でない):** `config.py`(`CHANGE_ME`/env 参照)・`config_test.py`(test 値)・
`mail.py`(AWS 資格は引数/env 経由)・`sendmail.py`(ホスト名)・`flask_helpers.py`
(`BASIC_AUTH_PASSWORD=None`/変数)。他種トークン(sk_live/AIza/ghp_/slack)掃引=discord 以外ゼロ。

## M-F7: 【裁定・訂正1】libcommon / simplicity は monorepo に取り込まない(B案)

- 裁定(2026-07-15・オーナー、根拠 `docs/COMMON_LIB_POLICY.md` の B 案): libcommon / simplicity を
  monorepo にマスターとして置かない。**各サービスが vendored コピー(`*/web-server/libcommon` 等)を
  直接持ち直接編集**し、完了したらコピーのバージョンを上げて原本へ適用する。原本は独立リポジトリ
  (`/src/libcommon/.git`・`/src/simplicity/.git`)として monorepo と並置。
- 実施: `git rm -r libcommon simplicity`(monorepo 直下2フォルダのみ。物理残(gitignore 物)も削除)。
  **各サービス内の vendored コピーは一切触っていない**(thinkx/kazukiotsukacom/auth/transformism の
  `web-server/libcommon` は無傷)。ARCHIVE.md の両行を表から「取り込み対象外(記録)」節へ移動
  (参照 SHA: libcommon `a316494` / simplicity `53f0639`、根拠 COMMON_LIB_POLICY.md)。
- MONOREPO_PLAN の v1.2 改訂(この裁定の計画本文反映)は人間が後で行う。

## M-F8: 【裁定・訂正2】push 前に歴史を1コミットに畳む(秘密の歴史残留の根治)

- 問題: M-2 の import コミットには redact 前の実秘密(AWS 資格・VPN PSK・playbooks)が歴史として
  残っており、M-6 で push すると `git log -p` 全域に運ばれてしまう。方針「歴史は運ばない」に反する
  (出所は ARCHIVE.md が担う)。
- 裁定(2026-07-15・オーナー): orphan で歴史を作り直し 1 コミットに畳む。
- 実施: `git checkout --orphan fresh` → `git add -A` → `git commit -m "initial: import all repos @
  2026refactor (provenance: ARCHIVE.md)"` → `git branch -M fresh master`。
- 検証(実施済み): `git rev-list --count master` = 1。全歴史(`git log -p master`)スキャン結果:
  PRIVATE KEY = 0 / PSK "hex" = 0 / 実 AWS キー = 0 / 追跡 `thinkx/playbooks/*` = 0。
  - 残 AKIA ヒット1件は `transformism/design/v2023Feb/kazukiotsukacom.ai`(Illustrator バイナリの
    偶然一致=**誤検出**。origin 由来の正当なデザイン資産)。
  - `thinkx/playbooks/` 文字列3件は本 `findings.md` 内の**言及テキストのみ**(除去記録)。実ファイルなし。
- 畳み込み後、`git reflog expire --expire=now --all && git gc --prune=now` で redact 前の実秘密を含む
  旧コミット群(M-1〜訂正1 の15コミット)を **dangling ごと完全 purge**(ローカルからも根絶)。

### 畳む前の全コミット記録(保全・15コミット)

畳み込みで破棄する歴史の記録。出所 SHA は本 ARCHIVE.md が正典。

```
ab36339 chore(M-1): monorepo shell — git init, workspace control docs, .gitignore, ARCHIVE.md skeleton
05f8f96 docs(M): findings ledger — cp/rsync deny→ask episode + CLAUDE.md polyrepo contradiction
bd0f6bf import libcommon @ 2026refactor a316494
a97ee58 import simplicity @ 2026refactor 53f0639
5edd822 import auth @ 2026refactor 02e97d1
c99cb97 import infra @ 2026refactor 4ef4726
c12c364 import loadbalancer @ 2026refactor 5ac8ceb
e645de5 import nginx-web-root @ 2026refactor 9214f26
605d380 import kazukiotsukacom @ 2026refactor 0ad3809
50b42f7 import thinkx @ 2026refactor 5a62167
c369dd8 import transformism @ 2026refactor df51b5b
abb7193 M-3: submodule メタデータ除去 + .gitignore 脱落アセットの忠実復元
6b93cea M-4 (partial): 秘密スクラブ — thinkx/playbooks 除外・infra 文書 redact
c687662 M-4 done: discord webhook はデモ判定で残置(オーナー裁定)・秘密検査クリア
4fc5b8e M(訂正1): libcommon/simplicity を monorepo 直下から除外(B案・COMMON_LIB_POLICY.md)
```

## M-F9: M-5 sweep 結果(全 green)

環境: pytest。サイトは `.s-track-venv`(flask 3.1.0)、auth は `auth/.venv`(mongoengine+mongomock)。
いずれも monorepo コピーを対象(conftest が monorepo 配下へ chdir/sys.path 挿入)。

- **3サイト route sweep**(Flask test_client で全 GET ルートの status をゴールデン照合):
  - `thinkx/web-server/tests/test_route_sweep.py` → 1 passed
  - `kazukiotsukacom/web-server/tests/test_route_sweep.py` → 1 passed
  - `transformism/web-server/tests/test_route_sweep.py` → 1 passed
- **auth テストゲート** `auth/tests` → **21 passed**(smoke routes / app imports / protocol / conventions)。
- **libcommon / simplicity**: B案(M-F7)により monorepo 対象外。テストゲートは原本リポジトリの管轄。
- **vendored libcommon VERSION 棚卸し**: 4消費者すべて同一。
  - `auth/web-server/libcommon` = v2.1.0 / `kazukiotsukacom/web-server/libcommon` = v2.1.0 /
    `thinkx/web-server/libcommon` = v2.1.0 / `transformism/web-server/libcommon` = v2.1.0
  - tree_sha256 全一致 `ab534a69ddb3ade5634253bc0d8b0c1bd6ea4e215a856b4320eb9b60b5495b04`
- コピー欠落起因の落ちは無し(M-3 の force-add 復元が効いている)。

## 参考: libcommon の実発見(別台帳)

libcommon リファクタの QA 中に検出した2件(vector_database が特性テスト網の外 / DEFAULT_LANG の
fallback 不整合)は `libcommon/DISCUSSION_2026REFACTOR.md` に記録済み。対応は libcommon Phase 3 の
管轄で、M(コピー)では扱わない。
