# EC2 から private repo を clone する ─ GitHub 認証方式

決定日: 2026-07-12 / 決定者: 大塚 / status: 確定
対象: `setup/web-setup.sh`, `setup/lb-setup.sh` / repo: thinkx, kazukiotsukacom, loadbalancer

---

## Deploy key(鍵は Mac で生成・保管)

Deploy key は EC2 に対象レポジトリに限り操作権限を与える GitHub の仕組みであり、鍵は以下のコマンドで
local マシンなど任意の場所で生成され `infra/deploykeys/` に格納される。

```bash
# (macbook local) ~/Sources/thinkx-system
REPO=<repo>
ssh-keygen -t ed25519 -N '' -C "supercom:kaz:$REPO" -f "infra/deploykeys/deploy_$REPO"
```

これを terraform で起動した EC2 に転送し `/home/kaz/.ssh/` に配置する。EC2 を再度起動しても
この鍵を転送すれば再度人手で GitHub に登録する必要はない。新たなレポジトリを追加したら以下の手順を実行する。

```bash
# (macbook local) ~/Sources/thinkx-system
REPO=<repo>
ssh-keygen -t ed25519 -N '' -C "supercom:kaz:$REPO" -f "infra/deploykeys/deploy_$REPO"
cat "infra/deploykeys/deploy_$REPO.pub"   # → GitHub の該当 repo > Deploy keys に登録(write は外す)
tar czf /tmp/secrets.tgz -C infra certs deploykeys
scp /tmp/secrets.tgz setup/check_deploykey.py supercom-web:/tmp/
ssh supercom-web 'bash -s' < "setup/setup_$REPO.sh"
```

---

## 問題

EC2 は起動直後、private repo を clone できない。GitHub に自分を認証する SSH 鍵が要る。
問うべきは 2 点 ── **秘密鍵はどこで生まれどこに置かれるか / 乗っ取られた時に何ができるか**。

- 秘密鍵 = 身分証。持つ者が本人として振る舞える。**外に出さない**
- 公開鍵 = 錠前。GitHub に預ける。漏れても害はない

原本(オンプレ)は、各マシンで `ssh-keygen` し公開鍵を GitHub **アカウント**に手動登録する方式。

---

## 3 案

### (a) EC2 で生成 → GitHub アカウントに登録(原本準拠)

```
EC2 ── ssh-keygen ──> 秘密鍵は EC2 から出ない / 公開鍵だけ ──> GitHub アカウント
```
- ○ 秘密鍵が流れない。原本と同じ。鍵 1 つで済む
- ✗ **アカウントの全 repo に read/write**。乗っ取られたら全 repo を書き換えられる

### (b) Mac の秘密鍵を EC2 にコピー

```
Mac ~/.ssh/id_github ──[ scp ]──> EC2   (同じ秘密鍵が 2 箇所に)
```
- ○ 最短
- ✗ **秘密鍵が移動**(経路・スナップショットに残る)。**あなた本人の鍵**なので被害が個人全体に及ぶ。**避ける**

### (c) Deploy key(repo 単位・read-only)★分かりにくい点

GitHub には、アカウント鍵とは別に **repo 1 つにだけ通用する鍵**を登録する仕組みがある。

```
新しい鍵を1つ    ├── 公開鍵 ──> thinkx repo > Deploy keys  [ write access 外す ]
                └── 秘密鍵 ──> EC2 の ~/.ssh/
```
- ○ **被害が最小**。乗っ取られても「その repo を読むだけ」。書けない/他 repo は見えない
- ○ EC2 の役割(取得して流すだけ = `infra/CLAUDE.md`)と一致。write 不要
- ✗ repo ごとに鍵と登録が要る / `~/.ssh/config` のホスト別名を 1 つ覚える

### 被害範囲(核心)

| | 乗っ取られた時にできること |
|---|---|
| (a) アカウント鍵 | 全 repo を読む + **書き換える** |
| (b) Mac 鍵コピー | 同上。しかも「あなた本人」として |
| **(c) Deploy key** | **その repo を読むだけ** |

---

> # 【大塚】c方式がよくわからない。どれがいいのか。a はこれまで同様だが pub → GitHub が自動化できるか

**→ (c) を推奨。** EC2 は露出サーバー。置く鍵は最悪漏れても損害が限定される種類にすべきで、
EC2 は「取得して流すだけ」で write 不要。read-only の Deploy key がこの設計に合致する。
(a) も許容(原本同様・秘密鍵が出ない)。(b) は実益なしで避ける。

**自動化について**: pub → GitHub は API で可能。ただし PAT(Personal Access Token)が要り、
**その PAT を安全に渡す必要が生じる(鶏と卵)**。解くには SSM + IAM ロールが要る。
→ この時点では「自動化する価値は高い(作り直しのたびの手作業が消える)」と回答した。

---

> # 【大塚】自動化できるが複雑化している。サーバー台数が少ないなら手動でブラウザ登録の方がシンプルで早い(最終判断)

**→ この判断が正しい。手動を採用。**

```
手動:  ssh-keygen → cat *.pub → ブラウザで貼る            ... 3回(repo数分) = 約5分
自動:  PAT作成(結局ブラウザ) → SSM登録 → IAMロール(terraform) → instance_profile
       → setup.shでSSM取得 → curlでAPI → jq/aws-cli依存 → PAT期限管理 → destroy時のkey削除
```

自動化は手作業 1 つを消す代わりに**部品を 6 つ増やす**。PAT 作成のブラウザ手作業は結局残る。
台数 2 台・repo 3 つでは割に合わない。しかも手動は**繰り返し作業ではない**
(Deploy key は GitHub に残るため、destroy して作り直しても鍵が EBS に残れば再登録不要)。

**補足**: こちらが「IAM ロールで `.env` 平文問題も同時解決」と述べたのは話を大きくしすぎだった。
それは独立した課題。Deploy key の自動化と混ぜない ── 混ぜたことが複雑さの原因。切り離す。

---

# ★ 完全な手順(採用: (c) Deploy key / 手動)

**I-STEP2(本番載せ替え)の直前に実施。I-STEP1 リハーサルでは鍵不要**
(リハーサルは経路検証が目的。ダミー静的ページで疎通確認 = clone 不要 = 鍵不要)

> **前提**: `user-setup.md` で実行ユーザ(RUN_USER)を確立済みであること。
> 以下のコマンドは全て RUN_USER として(`sudo -u "$RUN_USER" -H` 経由・絶対パス)実行する。
> ここでは RUN_USER=kaz を例に、簡潔さのため素の `ssh-keygen` 表記で示すが、
> **実際は必ず `sudo -u kaz -H` で /home/kaz/.ssh/ に作る**(user-setup.md 参照)。

### 1. EC2 上で鍵を生成(repo ごと)

```bash
# web
ssh ubuntu@<web_ip>
ssh-keygen -t ed25519 -f ~/.ssh/deploy_thinkx       -N "" -C "supercom-web:thinkx"
ssh-keygen -t ed25519 -f ~/.ssh/deploy_kazukiotsuka -N "" -C "supercom-web:kazukiotsuka"
# LB
ssh ubuntu@<lb_ip>
ssh-keygen -t ed25519 -f ~/.ssh/deploy_loadbalancer -N "" -C "supercom-lb:loadbalancer"
```
`-N ""` = パスフレーズなし(自動デプロイで対話が入らないため)。

### 2. 公開鍵を Deploy keys に登録(ブラウザ)

```bash
cat ~/.ssh/deploy_thinkx.pub
```
```
GitHub → ThinkXInc/thinkx → Settings → Deploy keys → Add deploy key
  Title: supercom-web
  Key:   (ssh-ed25519 AAAA... を貼る)
  Allow write access:  ☐ チェックしない   ← ★ここが肝。read-only
```
| repo | 貼る公開鍵 |
|---|---|
| ThinkXInc/thinkx | deploy_thinkx.pub (web) |
| ThinkXInc/kazukiotsukacom | deploy_kazukiotsuka.pub (web) |
| ThinkXInc/loadbalancer | deploy_loadbalancer.pub (LB) |

> Deploy key は同じ鍵を複数 repo に使い回せない(GitHub が拒否)。だから repo ごとに別の鍵。

### 3. SSH config にホスト別名(仕組みの要)

```bash
vim ~/.ssh/config
```
```
Host github-thinkx
    HostName github.com
    User git
    IdentityFile ~/.ssh/deploy_thinkx
    IdentitiesOnly yes

Host github-kazukiotsuka
    HostName github.com
    User git
    IdentityFile ~/.ssh/deploy_kazukiotsuka
    IdentitiesOnly yes
```
(LB は github-loadbalancer を同様に)
```bash
chmod 700 ~/.ssh; chmod 600 ~/.ssh/config ~/.ssh/deploy_*; chmod 644 ~/.ssh/deploy_*.pub
```
> `IdentitiesOnly yes` は必須。無いと SSH が他の鍵を手当たり次第試し、意図しない鍵で認証してしまう。

### 4. clone URL を別名に書き換え

```bash
# 通常            git@github.com:ThinkXInc/thinkx.git
# Deploy key 使用 git@github-thinkx:ThinkXInc/thinkx.git   ← github.com を別名に
git clone git@github-thinkx:ThinkXInc/thinkx.git                /src/thinkx
git clone git@github-kazukiotsuka:ThinkXInc/kazukiotsukacom.git /src/kazukiotsukacom
```

### 5. 接続テスト

```bash
ssh -T git@github-thinkx
# Hi ThinkXInc/thinkx! You've successfully authenticated...
# → アカウント名でなく repo 名が出れば成功(Deploy key の証拠)
```

### 6. setup スクリプトへ反映

```bash
# 変更前  clone_or_update "git@github.com:ThinkXInc/thinkx.git" "thinkx" "playbooks"
# 変更後  clone_or_update "git@github-thinkx:ThinkXInc/thinkx.git" "thinkx" "playbooks"
```
鍵の生成・登録・config は setup を流す前に一度だけ。以降は再利用される。

### 全体像

```
EC2 (web)                                GitHub
~/.ssh/deploy_thinkx        ──pub──────> thinkx > Deploy keys          [read-only]
~/.ssh/deploy_kazukiotsuka  ──pub──────> kazukiotsukacom > Deploy keys [read-only]
~/.ssh/config
   github-thinkx → deploy_thinkx
  git clone git@github-thinkx:ThinkXInc/thinkx.git
                └─ 別名が config を引き、正しい鍵が選ばれる
```
乗っ取られても攻撃者にできるのは thinkx / kazukiotsukacom を**読むだけ**。他 repo は見えない。

### 実施時に確認

```bash
cat /src/thinkx/.gitmodules   # playbooks submodule が別 repo なら Deploy key を追加
```
(libcommon は vendoring 済みで submodule ではない ─ 既決 / transformism を載せるなら 4 つ目)

---

# ■ 結論

- **D-1. 方式 = (c) Deploy key (read-only)**。EC2 は取得して流すだけで write 不要。
  被害が repo 単位・read-only に閉じる。(b) 却下、(a) は許容だが権限過剰で不採用。
- **D-2. 登録 = 手動(ブラウザ)。自動化しない**。部品 6 つ増に見合わない。繰り返し作業でもない。
  `.env` 平文廃止(SSM/IAM)は独立課題として切り離す。
- **D-3. I-STEP1 リハーサルでは鍵不要**。ダミー静的ページで疎通確認。鍵は I-STEP2 直前。

**再検討トリガー**(先回りしない): 台数/repo 増で手動が負担 / 頻繁な作り直しで再生成が発生 /
別件で SSM・IAM を導入し自動化の追加コストが実質ゼロになった ── のいずれかが実測で成立した時。