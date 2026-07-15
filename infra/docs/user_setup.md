# 前処理: 実行ユーザの確立(run-as-user)

決定日: 2026-07-12 / 決定者: 大塚 / status: 確定
種別: **アタッチメント** ─ 正規手順(`setup/*.sh` / Deploy key 登録 等)の**前**に一度実行する共通前処理
対象: すべての EC2(web / LB)

---

## これは何か

AMI 既定ユーザ(`ubuntu`)以外の任意のユーザで、以降の手順を走らせるための前処理。
`setup/*.sh`・Deploy key 登録・cron 設置など、後続の手順は
「実行ユーザは既に正しく確立されている」ことを前提にしてよい。

```
RUN_USER = 以降の手順を実行するユーザ(パラメータ)
   例: kaz   … サービス実行者・原本準拠(既定)
       alice … 開発者。そのユーザ権限で Claude Code を動かす場合
```

**この文書は特定ユーザ(kaz)の話ではない。** 「ubuntu ではない実行ユーザを確立する」
という一般手順であり、kaz はその筆頭の例にすぎない。

---

## 問題

オンプレは全て **kaz** で一貫していた。

```
systemd    User=kaz                      (uwsgi_thinkx.service 等)
/src       kaz:serveradmins が所有
git        kaz が clone / pull
~/.ssh     /home/kaz/.ssh に鍵と config
```

一方 **AWS の Ubuntu AMI の既定ユーザは `ubuntu`**。目的の RUN_USER は**最初は存在しない**。

「EC2 では誰として動くか」を決めないと、**所有権と鍵の置き場が食い違い**、
`sudo -u <RUN_USER> git clone` が `/home/ubuntu/.ssh/` の鍵を見つけられず失敗する
── といった事故が起きる。これは SSH 鍵に限らず、**後続の全手作業に効く上位の設計問題**。

---

## 2 案(どのユーザで動くか)

### (A) RUN_USER(ubuntu 以外)で統一

EC2 上で RUN_USER を作り、`/src`・git・systemd・鍵を全て RUN_USER に揃える。

- ○ 原本(kaz)や、開発者ごとの権限分離と一致。service ファイル・所有権をそのまま持ち込める
- ○ 用途ごとにユーザを分け、権限を分離できる(開発者 A の Claude Code は A の権限で動く 等)
- ✗ EC2 に RUN_USER を**明示的に作る**必要がある(AMI に居ない)
- ✗ ssh で入るのは `ubuntu` なので、**手作業は `sudo -u <RUN_USER>` 経由**になる

### (B) ubuntu のまま使う

`User=` を ubuntu に書き換え、所有権も ubuntu に寄せる。

- ○ ssh で入った本人がそのまま作業できる(`sudo -u` が不要)
- ✗ **service ファイル・所有権・原本手順を全て書き換える**必要がある
- ✗ 原本との差分が増え二重管理。用途ごとの権限分離もできない

---

> # 【大塚】今 kaz で動いているなら無理に変える必要はない。kaz でいい。
> # さらに ─ これは kaz に限らない。他の開発者ユーザを作り、そのユーザが Claude Code を動かすケースに一般化できる。正規手順の前に user をスイッチするアタッチメントとして扱うべき。

**→ (A) を採用し、RUN_USER としてパラメータ化する。** ubuntu 以外の実行ユーザを立てる
という一般手順にし、この文書を後続手順の**前段アタッチメント**として独立させる。
kaz は既定の RUN_USER の例。(B) は書き換え範囲が広く権限分離もできず、不採用。

**ただし ubuntu 以外で動かすには AWS 特有の落とし穴が 2 つある。** 潰さないと必ず踏む。

---

## 落とし穴 1: RUN_USER は最初から居ない ── 順序の罠

```
ssh ubuntu@<host> で入る                    → あなたは ubuntu
RUN_USER として鍵を作るには sudo -u 経由    → RUN_USER が作られた後でないと不可
```

**手作業(鍵生成・config 配置)は、RUN_USER を作った後に、RUN_USER として行う**必要がある。
順序を間違えて普通に `ssh-keygen` すると `/home/ubuntu/.ssh/` に作られ、
clone(`sudo -u <RUN_USER>`)からは見えず認証に失敗する。

## 落とし穴 2: /home/<RUN_USER>/.ssh のパーミッション

`sudo -u <RUN_USER>` で鍵を使うには、`/home/<RUN_USER>/.ssh/` が **RUN_USER 所有**かつ
パーミッションが厳密(700 / 600)でないと SSH が鍵を拒否する。`sudo` 経由で作ると
**root 所有になりがち**で、ここでハマる。

---

# ★ 完全な手順(RUN_USER をパラメータとして)

**原則: EC2 上の手作業は全て `sudo -u "$RUN_USER" -H` で、絶対パスで行う**

```bash
# 実行ユーザを決める(例)
RUN_USER=kaz          # サービス実行者・原本準拠
# RUN_USER=alice      # 開発者。そのユーザで Claude Code を動かす場合

HOME_DIR="/home/${RUN_USER}"
```

### 0. RUN_USER の存在を確認(無ければ作る)

```bash
ssh ubuntu@<host>

id "$RUN_USER" || sudo useradd -m -s /bin/bash -G serveradmins "$RUN_USER"
# setup.sh が既に作っている場合もある。未作成ならここで作る
```

### 1. 鍵を RUN_USER として生成(repo ごと ─ Deploy key 方式)

```bash
sudo -u "$RUN_USER" -H ssh-keygen -t ed25519 \
  -f "${HOME_DIR}/.ssh/deploy_thinkx"       -N "" -C "supercom:${RUN_USER}:thinkx"
sudo -u "$RUN_USER" -H ssh-keygen -t ed25519 \
  -f "${HOME_DIR}/.ssh/deploy_kazukiotsuka" -N "" -C "supercom:${RUN_USER}:kazukiotsuka"
```

### 2. 公開鍵を表示(ブラウザで Deploy keys に貼る)

```bash
sudo -u "$RUN_USER" cat "${HOME_DIR}/.ssh/deploy_thinkx.pub"
```
> 登録手順の詳細は `DECISION-github-auth.md` を参照。

### 3. config を RUN_USER のホームに作成

```bash
sudo -u "$RUN_USER" -H bash -c "cat >> ${HOME_DIR}/.ssh/config << EOF
Host github-thinkx
    HostName github.com
    User git
    IdentityFile ${HOME_DIR}/.ssh/deploy_thinkx
    IdentitiesOnly yes

Host github-kazukiotsuka
    HostName github.com
    User git
    IdentityFile ${HOME_DIR}/.ssh/deploy_kazukiotsuka
    IdentitiesOnly yes
EOF"
```

### 4. パーミッション(RUN_USER 所有・厳密に)

```bash
sudo -u "$RUN_USER" chmod 700 "${HOME_DIR}/.ssh"
sudo -u "$RUN_USER" chmod 600 "${HOME_DIR}/.ssh/config" "${HOME_DIR}/.ssh/deploy_"*
sudo -u "$RUN_USER" chmod 644 "${HOME_DIR}/.ssh/deploy_"*.pub
```

### 5. 接続テストも RUN_USER で

```bash
sudo -u "$RUN_USER" ssh -T git@github-thinkx
# Hi ThinkXInc/thinkx! You've successfully authenticated...
```
> **ubuntu でテストが通っても意味がない**。clone は RUN_USER で走るため、そのユーザで確認する。

### 3 つの鉄則

| | 理由 |
|---|---|
| **`sudo -u "$RUN_USER" -H`**(`-H` 必須) | `-H` が無いとホームが `/root` や `/home/ubuntu` を指す |
| **絶対パス `/home/$RUN_USER/.ssh/...`** | `~` は sudo 環境でどのホームを指すか曖昧 |
| **テストも RUN_USER で** | ubuntu で通っても clone(RUN_USER)は失敗しうる |

---

## 後続手順との接続

この前処理を済ませてから `setup/*.sh` と Deploy key 手順を実行する。
それらは「実行ユーザは既に確立済み」を前提にしてよい。

`setup/web-setup.sh` は既に `APP_USER=kaz`(= RUN_USER)で `sudo -u kaz git clone`・
`/src` を `kaz:serveradmins` 所有に設定している。追加すべきは **clone 前のガード**:

```bash
# clone の前に RUN_USER の鍵と config が存在するか確認して、無ければ止める
if [ ! -f "/home/${APP_USER}/.ssh/config" ] || \
   [ ! -f "/home/${APP_USER}/.ssh/deploy_thinkx" ]; then
  echo "ERROR: ${APP_USER} の SSH 鍵/config がありません。"
  echo "  user-setup.md の手順 0-4 を先に実行してください。"
  exit 1
fi
```

これで「順序を間違えて `/home/ubuntu/.ssh/` に作った」事故が、
**失敗ではなく明示的な停止**になる。

---

## RUN_USER 統一で問題になるケースはあるか

洗い出した結果、**実質ない**。

- **SSM Session Manager を使う場合**: SSM で入ると `ssm-user` になる。
  → 今回は ssh で入る方針なので無関係
- **certbot 等 root が要る操作**: 元々 `sudo` でやるので RUN_USER でも ubuntu でも変わらない

デメリットは「EC2 で RUN_USER を作る + 手作業を `sudo -u` で行う」という**一手間だけ**。
原本との一貫性・用途ごとの権限分離のための正当なコスト。

---

# ■ 結論

- **D-1. EC2 の実行ユーザは ubuntu 以外(RUN_USER)で統一**。既定は kaz(原本準拠)。
  開発者ごとにユーザを分け、そのユーザで Claude Code を動かす運用にも同じ手順で対応できる。
  ubuntu のまま使う(B 案)は変更範囲が広く権限分離もできないため不採用。
- **D-2. EC2 上の手作業は全て `sudo -u "$RUN_USER" -H` + 絶対パス**で行う。
  ssh で入るのは ubuntu だが、**作るものは全て RUN_USER のホームに置く**。
- **D-3. この文書はアタッチメント**。正規手順(`setup/*.sh`・Deploy key 登録)の**前**に
  一度実行し、user をスイッチする。後続手順はこれを前提にしてよい。
- **D-4. setup スクリプトに clone 前ガードを入れる**。RUN_USER の鍵/config が無ければ
  失敗ではなく明示的に停止し、本文書を案内する。

**適用範囲**: この決定は SSH 鍵に限らず、EC2 上の全手作業(鍵・config・`/src` 配下の操作・
cron 設置 等)に及ぶ。GitHub 認証方式(`DECISION-github-auth.md`)は、この前処理を
済ませた後に実行される**下位の一手順**。