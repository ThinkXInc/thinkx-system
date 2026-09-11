# staging 観測ツール 実装計画書 v1.0(O トラック・案)

対象: staging web(web1-stg)の Claude Code 常駐セッションと claude_connect の**観測**を、
Claude Code の承認プロンプト無しで回せるようにする ／ 作成日: 2026-09-05(案。オーナー承認で確定)
性質: **観測のみを道具にする。変更系は道具に持たせない。** claude-session.service・claude_connect・
デプロイ経路・SG・terraform には触れない。
正本はこのファイル1箇所(infra/docs/STG_OBSERVE_PLAN.md)。settings の `Edit(**/*_PLAN.md)` deny が自動で効く。

## 目的

いま毎回承認が挟まっている次の3種のコマンドを、承認なし・レビュー済みの固定コマンド列に置き換える。

1. ヘルスチェック(uptime・unit・tmux・state・外形)
2. state 遷移のウォッチ(ログイン復旧の見守り)
3. claude_connect のログ末尾

`ssh` / `curl` で始まるコマンドは今後も承認対象のまま残す(ワンオフ調査の経路)。
ゼロにするのは「毎回同じ観測」の承認だけであり、「任意の ssh」を無承認にすることではない。

## 調査で確定した前提(2026-09-05 実測・infra/findings.md 同日)

| 項目 | 値 | 根拠 |
|---|---|---|
| claude_connect の稼働ノード | web1-stg 自身(User=kaz) | setup_claude_connect.sh / claude_connect.service |
| bind | 192.168.2.11:8008 のみ。**127.0.0.1 では聞いていない** | `ss -ltn` 実測・curl 127.0.0.1 → 000 |
| ホスト上の state URL | `http://web1:8008/connect/state`(200) | dns.tf(web1.supercom.internal→private_ip)・search domain 配布済み |
| private IP | terraform `local.web_ip` で固定。再構築で不変 | variables.tf |
| ssh 別名 | `supercom-web1-stg`(ログインは ubuntu・`sudo -n` 可) | hostname.md ①層・実測 |
| 公開 IP / URL | EIP 台帳で固定(D-53)。staging.thinkxinc.com は LB EIP 52.68.142.190 | terraform/eips・DNS切替手順 |
| サーバー TZ | Etc/UTC(server.py の observed_at も UTC) | timedatectl 実測 |
| tmux の見え方 | `sudo -n -u kaz tmux ...` | attach_claude.sh・runbook |
| 外形の期待値 | Basic 認証外から `/` `/connect/` `/connect/state` は **401** が正常 | findings 2026-09-05 N-4 |

## 大原則

1. **観測のみ。** send-keys・kill-session・restart・logout は道具に入れない。/logout は人間が attach して行う
   (CLAUDE_CONNECT_PLAN N-7 の定義どおり)。変更系が要るなら別計画。
2. **リモートで実行するコマンド文字列は全てスクリプト内の固定リテラル。** 引数として受け取らない
   (`exec <任意>` を作らない)。値引数は型を検証(整数・ホワイトリスト)して `shlex.quote` で埋める。
3. **python3 標準ライブラリのみ、`infra/scripts/` に置く。** 分岐・ループ・状態を持つので bash にしない
   (infra/docs/GUIDELINES.md「分岐が要るなら python」「新規 bash を scripts/ に足さない」)。
4. **定数は冒頭に集約し、`doctor` で機械検証する。** 再構築後に前提が崩れたら doctor が検出し、
   「定数と findings を更新せよ」と出す。定数を毎回再発見する道具は作らない。
5. **認証情報・ログイン URL を標準出力に出さない**(URL は `url=yes/no`。必要時のみ `--show-url`)。
6. 1項目=1コミット+push。ブランチは `monorepo`。発見は infra/findings.md へ即記録。
7. **settings は人間が適用する**(実行者は `.claude/**` を書けない)。順序は「スクリプト配置 → 人間がレビュー → settings 適用」。

## 配置

```
infra/scripts/stg.py            観測ツール(サブコマンド式・python3 標準ライブラリ)
infra/scripts/README.md         stg.py の要件を追記(ゼロから再実装できる粒度)
infra/runbooks/claude-connect.md 4節「サーバー側の確認」を stg.py check に差し替え(ask 承認)
.claude/settings.json           deny 2行(人間が適用)
```

## stg.py の仕様

呼び出し: `python3 infra/scripts/stg.py <subcommand> [options]`(Mac から。ask の `ssh`/`curl` 前置一致に掛からない)。
ssh は `subprocess.run(["ssh","-o","ConnectTimeout=8","-o","BatchMode=yes",HOST,REMOTE], ...)`。REMOTE は固定文字列。

| subcommand | やること(リモート) | 出力・判定 |
|---|---|---|
| `check` | uptime / `systemctl is-active claude-session claude_connect nginx uwsgi_thinkx` / `sudo -n -u kaz tmux ls` + `list-panes -F #{pane_current_command}` / `curl http://web1:8008/connect/state` / pane 末尾 8 行(空行と `Permission` 行を除く) | ローカルから外形 `https://staging.thinkxinc.com/` `/connect/` `/connect/state` の HTTP code(期待 401)。最終行 `OK: stg check state=<state> ...` / `FAIL: stg check <崩れた項目>` |
| `watch` | `--interval 5` `--max 54` で state をポーリング。変化時だけ `HH:MM:SSZ <state> url=yes/no` を出す。`connected` で終了 | 終了時に `journalctl -u claude_connect -o cat` の末尾 `--log-lines 8`(`GET /connect/state` を除く) |
| `log` | `--unit {claude_connect,claude-session}`(ホワイトリスト) `--since-min 30`(相対。TZ を意識しない) `-n 50` | `sudo -n journalctl -u <unit> --no-pager --since -<N>min -o cat` をそのまま |
| `doctor` | 前提表の機械検証: ssh 到達・`id -un`=ubuntu・`hostname`=web1-stg・`sudo -n true`・`timedatectl`=Etc/UTC・`ss -ltn` に `192.168.2.11:8008`・`getent hosts web1`=192.168.2.11・unit 2つ enabled | 項目ごとに OK/FAIL。1つでも FAIL なら最終行 `FAIL: stg doctor 前提が崩れている — stg.py の定数と infra/findings.md を更新` |

- 戻り値 0/1(`sys.exit(main())`。python.md の preflight パターン)。
- 例外は捕まえて FAIL 1行。ssh 不達は `FAIL: stg <sub> ssh 到達不可(staging 停止中?)` と出す。
- 引数が無ければ使い方を出して 1(bash.md「引数が無ければ何もせず指定を促す」)。

## settings の差分(人間が適用。stg.py を読んでから)

```jsonc
"deny": [
  "Edit(infra/scripts/stg.py)",
  "Write(infra/scripts/stg.py)"
]
```

- allow の追加は不要(素の `Bash` が allow。`python3 infra/scripts/stg.py` は ask のどれにも前置一致しない)。
- ask の追加も不要(変更系サブコマンドを作らないため)。
- **この deny は「標準ツールでの誤編集の防止」であり境界ではない。** 素の Bash が allow の間は `sed -i`・`tee` で
  書き換え可能(既存の `*_PLAN.md` deny と同じ強さ)。境界が要るなら O-4。

## 作業項目(実行順)

### O-1 stg.py

- **変更:** `infra/scripts/stg.py` 新設(check / watch / log / doctor)。
- **完了条件:** Mac から4サブコマンドを実行し、承認プロンプトが出ないこと。`doctor` が全項目 OK。
  `check` の外形が 3 つとも 401。`watch --max 2` が 2 回で抜ける。`log --since-min 5` が journal を返す。
  出力を findings に貼る。
- **戻し方:** ファイル削除。
- **コミット:** `feat(infra): stg.py — staging observation without approval prompts`

### O-2 settings(人間)

- **変更:** オーナーが stg.py を読み、deny 2行を `.claude/settings.json` に追加。
- **完了条件:** 実行者が `Edit` で stg.py を触ろうとすると拒否される(1回試して findings に記録)。
- **コミット:** なし(settings はワークスペース制御文書)。

### O-3 文書

- **変更:** `infra/scripts/README.md` に stg.py の要件(上表)を追記。`infra/runbooks/claude-connect.md` 4節の
  ssh 一行コマンドを `python3 infra/scripts/stg.py check` に差し替え(runbook は ask → 承認1回)。
- **完了条件:** README から stg.py を書き直せる粒度。runbook の旧コマンド(192.168.2.11 直書き)が消えている。
- **コミット:** `docs(infra): stg.py requirements and runbook pointer`

### O-4(任意・境界が欲しい場合)ssh forced command

- **変更:** 観測専用鍵を作り、web1-stg の `/home/ubuntu/.ssh/authorized_keys` に
  `command="/src/thinkx-system/infra/scripts/stg_remote.sh",no-pty,no-port-forwarding` で登録。
  `~/.ssh/config` に `Host supercom-web1-stg-ro` を切り、stg.py の HOST をそれに変える。
  `stg_remote.sh` は linear bash の観測系(`SSH_ORIGINAL_COMMAND` の先頭語で check/watch/log/doctor を選ぶ最小限)。
- **効果:** stg.py が書き換えられても、その鍵経由では固定スクリプト以外を実行できない。
- **判断:** O-1〜O-3 で運用を回した後、オーナーが要否を決める。鍵作成と authorized_keys 登録は人間。

## 運用ルール

- ワンオフ調査(その場で grep 条件を組む等)は素の `ssh` を書いて承認1回。無承認化の対象ではない。
- 同じ形の調査を 3 回やったら stg.py のサブコマンドに昇格させる(計画書改訂 → オーナー承認)。
- 変更系(logout・restart・kill)は人間が attach_claude.sh か runbook の手順で行う。

## やらないこと

| 禁止事項 | 理由 |
|---|---|
| `stg.py exec <任意コマンド>` | 大原則2。deny をすり抜ける ssh そのものになる |
| logout / restart / send-keys サブコマンド | 大原則1。ask ルールは境界にならず、人間の操作と定義済み |
| bash の case 分岐ディスパッチャ | GUIDELINES(分岐は python) |
| `localhost:8008` への curl | bind が private IP のみ(実測 000) |
| `hostname -I` 先頭への依存 | docker bridge が 2 番目に出る。順序保証なし。DNS 名 web1 を使う |
| ask から `Bash(ssh:*)` を外す | 任意 ssh の無承認化は目的でない |
