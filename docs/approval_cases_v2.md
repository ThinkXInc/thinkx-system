# thinkx-system/docs/approval_cases_v2.md

# 承認ケース集(コーパス) v2 — 運用中に出た承認事例

v1(`docs/archive/approval_cases/v1.md`・事例 A〜M・凍結 2026-09-17)の構築物が稼働してから、
**なお承認プロンプトが出たコマンド**を生のまま貯める場所。v1 と同じく材料であって規範ではない。

- **enforce の正**: `.claude/settings.json`(deny / ask / allow)。ここを複製しない。
- **判定基準**: `docs/DEPLOY_APPROVAL_LEVELS.md`「承認削減の判定基準」「安全モデル」。
- **層の割り当て(D-53)**: settings / hook 判定 / 固定 wrapper の 3 層。割り当て表は下に転記(v1 から引き継ぎ・現行の規則)。
- **稼働中の構築物(v1)**: `hooks/check_git_command.py`(git add / commit / push 非 force を無承認)、`infra/scripts/stg.py`(staging 観測)。

## 追記のしかた(v1 と同じ)

承認が出たコマンドに当たったら 1 ケース足す。想像で先に書かない(実例のみ)。フィールドは 5 つ:

- **生コマンド(要点)**
- **承認の引き金**(どの ask/deny 語・どの構文にマッチしたか)
- **クラス**: 観測 / 編集 / 資産 / 変更 / 一度きり
- **正しい形**: 畳んだ形 or 使うべき専用ツール、または「承認を残す」
- **残るゲート**

昇格の入口: 同型を **3 回** 書いたら固定スクリプトのサブコマンド化(`DEPLOY_APPROVAL_LEVELS.md` の規則)。

## 判定方式の割り当て(D-53・2026-09-06 確定・v1 から引き継ぎ)

新しい事例は次の 3 問で層を決める:
1. settings の前置一致で書けるか。
2. 実行時にコマンドを安全に分類できるか(文法が綺麗で、危険な形を数え上げられるか)。
3. 頻度が高く習慣的か(高いと、毎回 wrapper を使わせる規律が崩れて生コマンドが漏れる)。

| 対象 | settings で書ける | 分類が安全 | 頻度 | 割り当て |
|---|---|---|---|---|
| git add | 可 | — | 高 | **settings** |
| WebFetch ドメイン | 可(`domain:*.host`) | — | — | **settings** |
| git commit(複数行・トレーラ) | 不可 | 安全 | 最高 | **hook 判定**(稼働中) |
| git push(非破壊) | 不可 | 安全 | 高 | **hook 判定**(稼働中) |
| curl(localhost) | 不可 | 危険(localhost 偽装) | — | **固定 wrapper** |
| ssh(観測) | 不可 | 不能(引数の中身が不透明) | — | **固定 wrapper / forced-command** |
| terraform apply/destroy | — | — | 低 | ゲート維持(自動承認しない) |
| 編集 | — | — | — | Edit / build script(Bash でない) |
| browser localhost | — | — | — | Chrome 拡張(別系統) |

deny の床(force push・rm・sudo・鍵/tfstate 等)は全層で維持。hook も wrapper もその上で承認を足すだけ。
ask と deny のルールは hook の allow に勝つ。

---

## 事例(v2・2026-09-17 開始)

事例番号は v1 の M の続き(N から)。

### N. lb1-stg から web1 のポートへの疎通確認(+ security.tf の grep)
- **生**: `grep -n "8005\|8006\|8007\|8010\|from_port\|to_port" infra/terraform/security.tf | head -20; echo ---; ssh -o ConnectTimeout=8 supercom-lb1-stg 'curl -s -o /dev/null -w "%{http_code}" -m 5 http://web1.supercom.internal:8010/podcast/ || echo ...'`
- **引き金**: `ssh`(ask)。grep / head / echo は止まらない。
- **クラス**: 観測(SG の設定値を読み、LB から web のポートに届くかを見る。書き込みなし)。
- **正しい形**: 固定 wrapper。既存の `stg.py` は web1-stg の中を見る道具で「lb1-stg から web1 の指定ポートへ GET」は持たない。
  `check_request_path.sh` も ssh を生で書く前提。「LB → web:<port> の http code」を返すサブコマンドを 1 つ足す。
  ホストは lb1-stg / web1 に固定、ポートは固定リテラルの候補(8005〜8010)に限定し、任意 URL・任意ホストを受けない。
- **残るゲート**: なし。
- **同型カウント**: 1 回目(2026-09-17)。

### O. release が production に取り込まれたかの検証(事例 F/G と同型・3 回目)
- **生**: `git fetch -q origin; echo "--- production の先端"; git log --oneline -1 origin/production; echo "--- release/2026-09-17 と production の tree 一致?"; [ "$(git rev-parse origin/release/2026-09-17^{tree})" = "$(git rev-parse origin/production^{tree})" ] && echo "一致(取り込み済み)" || echo "不一致"; echo "--- 本番 /re…`(末尾は本番 URL への curl)
- **引き金**: 3 つ重なる。(1) `$(git rev-parse ...)` のコマンド置換(settings も hook も委ねる)、(2) `git rev-parse` が allow に無い、(3) 末尾の本番 URL への `curl`(ask)。
- **クラス**: 観測(fetch して先端と tree を比べ、本番 URL の http code を見る。書き込みなし)。
- **正しい形**: v1 事例 F/G(デプロイ着地の検証)と同型で **3 回目 → 昇格条件に達した**。
  `verify_deploy.py <release>` を新設し、production の先端・release との tree 一致・本番 URL の http code を
  まとめて **OK / MISMATCH** で出す(hex や SHA を人間に目視させない)。curl は python の urllib で畳み、対象 URL は
  固定リテラル(thinkxinc.com 配下)に限定する。
- **残るゲート**: なし。
- **同型カウント**: 3 回目(F・G・本件)。次の一手は wrapper 新設。

### P. `printf 'yes\n' | bash terraform_apply.sh staging` + ssh 疎通確認(変更系の反例・事例 K の再発形)
- **生**: `printf 'yes\n' | bash infra/scripts/terraform_apply.sh staging 2>&1 | tail -2 && ssh -o ConnectTimeout=8 supercom-lb1-stg 'curl -s -o /dev/null -w "LB -> web:8010 = %{http_code}\n" -m 8 http://web1.supercom.internal:8010/podcast/'`
- **引き金**: `terraform_apply.sh` は allow に無い(bash スクリプト実行)+ `ssh`(ask)。**ここで承認が出るのは正しい。削減しない。**
- **クラス**: 変更(terraform apply)+ 観測が 1 行に混ざっている。
- **問題は承認の有無ではなくコマンドの形**: `terraform_apply.sh` は「plan の全差分を人間に見せ、人間が `yes` と打ってから apply する」
  wrapper(`read -r ans; [ "$ans" = yes ]`)。`printf 'yes\n' |` で標準入力に yes を流すのは、**その yes を実行者(Claude)が
  代打ちしている** = wrapper の存在意義を消している。v1 事例 K(`-auto-approve` で prod/staging 全 4 台破壊)と同じ構造。
  plan に無関係な差分(AMI 追従の ForceNew 等)が同乗しても止まらない。
- **正しい形**: 2 つに分ける。(1) apply は wrapper を素で実行し、**yes はオーナーが plan を見て打つ**(承認プロンプトの
  承認とは別物。plan の内容を見た上での yes)。実行者は yes を流さない。(2) その後の疎通確認は事例 N の観測 wrapper で行う。
  1 行に混ぜない。
- **残るゲート**: apply の承認(人間・plan を見た yes)。削減対象ではない。
- **記録**: findings.md 2026-09-17 に「実行者が yes を代打ちした」事実を記録。
- **同型カウント**: 変更系につきカウント対象外(何回出ても削減しない)。

### Q. 本番サイトの http code + 本番 web1 の `.env` 設置検証(push_env.sh の結果確認)
- **生**: `echo "--- 本番サイト"; for p in / /about /remote_control/; do printf '%-18s %s\n' "$p" "$(curl -s -o /dev/null -m 10 -w '%{http_code}' https://thinkxinc.com$p)"; done; ssh -o ConnectTimeout=8 -o BatchMode=yes supercom-web1 'ls -l /src/thinkx/.env; sudo -n wc -l < /src/thinkx/.env; sudo -n grep -o "^[A-Z_]*=" /src/thinkx/.env | tr "\n" " "; ls -l /tmp/remote_auth.env*; sysctl fs.protected_regular; sudo -n journalctl -u uwsgi_thinkx --no-pager -n 8 -o cat | cut -c1-160' 2>&1; sed -n 18,40p infra/etc/push_env.sh; ls -l thinkx/.env | awk '{print $1, $5, ...}'`
- **引き金**: `curl`(ask・本番 URL)+ `ssh`(ask・本番 web1)+ `$(curl ...)` のコマンド置換。sed / ls / awk / printf は止まらない。
  ssh の中の `sudo -n` はローカルの `Bash(sudo:*)` deny に前置一致しない(deny は可視コマンドの先頭語しか見ない。v1 判定基準の注記どおり settings は機械的境界でない)。
- **クラス**: 観測。ただし **相手が本番で、`.env` に触る**点が N・O と違う。読んでいるのは所有者・権限・行数・変数名(`grep -o "^[A-Z_]*="`)だけで **値は出していない**。
  ローカル側の `.env` は `Read(**/.env)` deny だが `ls -l` はメタデータのみで内容を読まない。
- **中身は 4 つの別作業**:
  1. 本番 URL の http code(固定パス 3 つ・GET のみ)= 事例 O の末尾と同じ断片。**この断片は F/G/O/Q で 4 回目**。
  2. 本番サーバーの `.env` 設置検証(所有者・権限・行数・変数名)= `push_env.sh` が配布した結果の確認。
  3. `/tmp` の残骸と `sysctl fs.protected_regular` = push_env.sh の設計確認(一度きり。答えが出たら意味が尽きる)。
  4. ローカルの push_env.sh の該当行と元ファイルのメタデータ = 止まらない。
- **正しい形**:
  - 1 → `verify_deploy.py`(事例 O の次の一手)に本番 URL の http code を含める。URL は固定リテラル(thinkxinc.com 配下)。urllib で畳む。
  - 2 → **配布スクリプト自身に結果検証を畳む**(`push_env.sh` の末尾か `verify` サブコマンド)。出すのは所有者・権限・行数・変数名まで、**値は絶対に出さない**(スクリプト側で固定・引数で変えられない)。
    配布と検証を別コマンドで書くから ssh が 2 回出る。配布した直後に同じスクリプトが検証すれば承認は配布の 1 回で済む。
  - 3 → 一度きり。生の ssh で承認 1 回、答えは findings/手順書に定数として記録して二度と打たない(v1 事例 B と同じ扱い)。
  - 本番 web1 への ssh 観測 wrapper は staging 用 `stg.py` とは別に持つか、環境を必須引数にする(D-xx「環境は必須引数」・黄色注意)。本番は読み取り専用コマンドを固定リテラルで持ち、`sudo -n` の対象ファイルもリテラル固定。
- **残るゲート**: なし(全て読み取り)。ただし本番への ssh は wrapper 化しても「本番に入る」事実は変わらないので、wrapper の固定コマンド集合は staging より狭く保つ。
- **同型カウント**: 本番 URL http code は 4 回目(昇格済み扱い・`verify_deploy.py` に含める)。`.env` 設置検証は 1 回目(push_env.sh 側に畳む候補)。

### R. push_remote_auth.sh の埋め込み python をローカルで単体テスト
- **生**: `T=$(mktemp -d); awk "/<<'PY'/{f=1;next} /^PY\$/{f=0} f" infra/etc/push_remote_auth.sh > "$T/w.py"; wc -l < "$T/w.py"; printf 'A=1\nB=2\nREMOTE_BASIC_AUTH_USER=old\n...' > "$T/.env"; chmod 640 "$T/.env"; echo "--- 通常"; printf 'kobito\nsecret1\n' | python3 "$T/w.py" "$T/.env" ...`
- **引き金**: `$(mktemp -d)` のコマンド置換(settings の allow でも hook でも通らない)+ `>` リダイレクト。awk / python3 / chmod / printf は止まらない。
- **クラス**: テスト(一度きり・ローカル)。書き込みは mktemp 配下だけで可逆。
- **根本**: python が bash スクリプトの heredoc に埋まっているため、awk で切り出さないと単体テストできない。テストのために
  ワンライナーで抽出・仮 `.env` 作成・実行を 1 行に詰めたのが承認の原因。
- **正しい形**:
  - 埋め込み python を独立ファイル(例 `infra/etc/lib/write_remote_auth.py`)に出し、bash からはそれを呼ぶ。テストは
    そのファイルを直接対象にできる。
  - テストは固定スクリプト(例 `infra/etc/tests/test_push_remote_auth.sh` か python の unittest)に置き、仮 `.env` の作成と
    後片付けをスクリプト内に持つ。作業ディレクトリはセッションの scratchpad か `$T` をスクリプト内で作る(可視コマンドに `$(...)` を出さない)。
  - settings の allow に `Bash(python3 scripts/*)` があるので、python のテストをその形で置けば無承認で走る。
- **残るゲート**: なし。
- **同型カウント**: 1 回目。「bash の heredoc に埋めた python を切り出してテスト」はこれが初出。次に出たら独立ファイル化を実施。

### S. staging の podcast データを NFD→NFC にリネーム(ssh + sudo + python heredoc・変更系)
- **生**: `ssh -o ConnectTimeout=8 supercom-web1-stg 'sudo -u kaz python3 - <<"PY" ... os.listdir("/src/podcast/data") ... unicodedata.normalize("NFC") ... shutil.move / shutil.rmtree(p) / os.rename(p, tgt) ... PY'`
- **引き金**: `ssh`(ask)。中の `sudo -u kaz` はローカルの deny に前置一致しない。
- **クラス**: **変更**(サーバー上のデータの移動・ディレクトリ削除・リネーム)。**承認が出るのは正しく、削減対象ではない。**
- **問題は承認の有無でなく中身と形**:
  1. **データ消失の穴**: 既存 NFC 側に同名ファイルがあると `skip(既存)` して比較せず、その後 `shutil.rmtree(p)` で NFD 側を丸ごと消す。
     両側に同名で中身が違うファイルがあれば NFD 側が黙って失われる。削除前にハッシュ一致を確認するか、不一致があれば止めるべき。
  2. **不可視**: ssh の heredoc に書いた一度きりの python は diff に残らず、レビューも再現もできない(v1 事例 C/M と同じ構造)。
  3. podcast データは 2026-09-17 に monorepo へ完全移行済み(全ハッシュ照合済)で、サーバー側はデプロイ連動の完全コピー先。
     サーバー側だけを直接いじるとローカル(正)との差が生じ、次のデプロイで再び NFD が来るか、逆に消える。正はローカル側の名前。
- **正しい形**: 一度きりの移行でも、変更系はレポジトリ内の固定スクリプト(例 `podcast/scripts/normalize_nfc.py`)にする。
  dry-run(何を動かし何を消すかの一覧)→ ハッシュ比較 → 不一致なら停止 → 承認 → 実行、の順。ローカルの data/ を先に直し、
  サーバーはデプロイの同期で追従させる(サーバー直叩きは最後の手段)。ssh で流す場合もスクリプトをファイルとして送って実行し、
  heredoc に書かない。
- **残るゲート**: 実行の承認(人間)。削減対象ではない。
- **同型カウント**: 変更系につきカウント対象外。

---

## 状態と次の一手(2026-09-17)

- v1 構築物は稼働中(複数行 commit の dry-run が無承認で通ることを 2026-09-17 に実測)。
- N・O・Q は観測 wrapper の材料。O は 3 回目、「本番 URL の http code」断片は Q で 4 回目 → `verify_deploy.py` 新設が次の一手
  (release の着地 + 本番 URL の http code を 1 本で)。N は 1 回目、同じ形が続くなら同じスクリプトか `stg.py` のサブコマンドに畳む。
- Q の `.env` 設置検証は配布スクリプト `push_env.sh` 自身に畳む候補(値は出さない)。本番 web1 への観測 wrapper は staging 用と分けるか
  環境を必須引数にする。
- P は削減しない。「wrapper の yes を実行者が流さない」を実行者の規律として守る(findings に記録)。
- R は「heredoc 埋め込み python を切り出してテスト」の初出。次に出たら python を独立ファイルにしてテストをスクリプト化。
- S は削減しない(変更系)。中身に削除前のハッシュ比較が無い穴があり、形も heredoc で不可視。変更系は固定スクリプト + dry-run + 承認。
- 収録済みの承認引き金(v2 時点): ssh(N/P/Q/S)・curl 本番(O/Q)・`$(...)` コマンド置換(O/Q/R)・変更系 wrapper への yes 流し込み(P)。
- 未着手(v1 から持ち越し): WebFetch ドメイン allow の恒久化、`make_favicons.sh`(事例 E)、curl localhost wrapper。
- `.claude/settings.json` の hooks 登録(オーナー編集)は 2026-09-17 時点で未コミット。
