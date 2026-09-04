# Claude 接続ページ 実装計画書 v1.1（N トラック）

対象: staging web（web1-stg）の Claude Code 常駐セッション（claude-session.service・D-59）／ 作成日: 2026-08-22　改訂: 2026-09-04（製品名を反映）
性質: **既存の運用フローを変えない追加**。claude-session.service・sync_from_origin.sh・デプロイ経路には触れない。
正本はこのファイル1箇所（infra/CLAUDE_CONNECT_PLAN.md）。settings の `Edit(**/*_PLAN.md)` deny が自動で効く。

## 目的

Claude Code セッションが「接続中」でないとき（tmux 消失・プロセス終了・要ログイン）に、
**スマホのブラウザだけで、ssh も PC も使わず、ボタン1つと入力欄1つで接続中に戻せる**ページを
staging に置く。ThinkX 自身の運用と、KOBITO サーバー顧客の導入初日・障害復旧を同一手順にする。

画面は1つ。接続中以外なら最初からボタンと入力欄を出しておく。

```
KOBITOサーバークラウド
● 接続されていません
[ セッションを再接続 ]
認証後に表示されたコードをここに貼る
[ ______________________ ] [ 送信 ]
```

接続中なら「Claude アプリのセッション一覧から開いてください」だけを出す。

---

## 大原則

1. **staging 限定。prod には置かない**（setup_claude_code.sh 1章・D-55 と同じ線）。
2. **認証情報を預からない。** ログイン URL の表示とコードの転送だけを行う。Claude アカウントの
   パスワード・トークンはページにもサーバーログにも出さない。
3. **既存 unit を変えない。** claude-session.service の ExecStart と同じコマンドを同じユーザー（kaz）で
   打ち直すだけ。tmux セッション名 `claude` も踏襲する。
4. **依存を増やさない。** python3 標準ライブラリのみ（http.server / json / subprocess）。pip も npm も使わない。
   画面は HTML 1ファイルに CSS/JS を内包（D-69 と同じ考え）。
5. **分岐・状態・検証のあるものは python、setup は linear bash**（docs/coding_guides/python.md）。
6. 1項目=1コミット+push。ブランチは `monorepo`（root D-60）。発見は **infra/findings.md** へ即記録
   （GUIDELINES「気づいた点は随時 findings に書く」）。
7. **観測した文言を正にする。** Claude Code のログイン時の出力文言・コード入力プロンプトの文言は
   バージョンで変わりうる。推測で書かず N-0 で実測し、findings に貼り、検出はその実測値に合わせて緩く書く。
8. **tmux send-keys に渡す文字列は `-l`（literal）で渡す。** シェル展開・tmux キー名解釈を通さない。

## 前提（N-0 で機械確認）

- staging EC2 が稼働中で、`systemctl is-active claude-session` が `active`。
- `claude --version` が取れる（setup_claude_code.sh の verify と同じ）。
- `/etc/thinkx/discord_webhook` が存在する（push_discord_webhook.sh で配布済み）。
- LB の staging 用 server ブロック（infra/setup/nginx/staging.thinkxinc.com.conf）に Basic 認証が
  掛かっている（この配下に置くことで認証を新設しない）。
- web SG は LB SG からの 8000〜8009 を許可済み（security.tf）。**8008 を使う**（8005 thinkx /
  8006 transformism / 8007 kazukiotsukacom / 8000・8001・8009 quantz 系。8008 は未使用 — N-0 で `ss -ltn` で確認）。
  SG・terraform に変更なし。

## 配置

```
infra/claude_connect/
  server.py                  状態取得と操作の HTTP サーバー（kaz・127.0.0.1 ではなく private IP:8008）
  index.html                 画面（1ファイル・CSS/JS 内包）
  claude_connect.service     systemd unit（User=kaz）
infra/setup/setup_claude_connect.sh     linear bash（unit の symlink・enable・start・verify）
infra/setup/nginx/staging.thinkxinc.com.conf   location /connect/ を追加（LB 側）
infra/runbooks/claude-connect.md        運用（状態の意味・手動での復旧・ゼロから再実装できる要件）
```

## 状態の定義（server.py が返す `state`）

| state | 判定 | 画面 | ボタンの動作 |
|---|---|---|---|
| `connected` | tmux セッション `claude` があり、pane の末尾 N 行にログイン要求文言が無く、pane のコマンドが claude 本体（N-0 で実測した名前） | 「接続中。Claude アプリのセッション一覧から開いてください」 | ボタンを出さない |
| `session_missing` | `tmux has-session -t claude` が失敗 | 「接続されていません」+ボタン+入力欄 | claude-session.service の ExecStart と同じコマンドで tmux を起動 |
| `login_required` | pane の末尾にログイン要求文言（N-0 実測）がある | 同上。ログイン URL が取れていればボタンを URL リンクにする | `/login` を送り、pane から URL を拾って返す |
| `unknown` | 上のどれでもない（claude が落ちて shell に戻っている等） | 「接続されていません」+ボタン+入力欄 | tmux セッションを kill して起動し直す |

URL の抽出は「`http` で始まるトークン」を末尾行から拾う（正規表現で厳密に書かない。大原則7）。
合わせて `disk_free_gb`（`df /` の空き）を返す。画面の隅に出すだけ。

## 作業項目（実行順）

### N-0 前提ゲートと実測

- **変更:** なし（コードは書かない）。
- **やること:** (1) 前提の各項目をコマンドで確認。(2) staging の tmux に attach し
  `/logout` → `/login` を実際に行い、**ログイン要求の文言・URL の出方・コード入力プロンプトの文言・
  成功時の文言**を pane からそのまま findings に貼る（`tmux capture-pane -p -t claude`）。
  (3) `tmux list-panes -t claude -F '#{pane_current_command}'` の値を接続中と shell に戻った時の
  両方で記録。(4) `claude setup-token` を実際に発行して常駐セッションで試し、結果（動作の可否・有効期限の表示）を記録。
- **完了条件:** 前提が全て成立 / findings に (2)(3)(4) の実測値が貼られている / `ss -ltn` に 8008 が無い。
  いずれか不成立なら着手しない。
- **コミット:** `docs(infra): findings — claude login wording and pane command observed`

### N-1 server.py（状態取得と操作）

- **変更:** `infra/claude_connect/server.py` を新設。標準ライブラリのみ。
  - `GET /connect/state` → JSON `{state, url, disk_free_gb, observed_at}`
  - `POST /connect/session` → state に応じて表の動作を行い、動作後の state と url を返す
  - `POST /connect/code`（body: `{code}`）→ `tmux send-keys -t claude -l <code>` の後に `Enter`。
    code は前後空白を落とし、改行を含むものは 400。**code の値をログに出さない**
  - `GET /connect/` → index.html を返す
  - bind は web の private IP（`hostname -I` の先頭）・port 8008。LB 以外から届かないのは SG が保証する
  - 全ての subprocess は `shell=False`・引数リスト。tmux 操作は `sudo -u` を使わない（自分が kaz）
  - 失敗時は 500 と短い理由文字列。例外で落ちない（ハンドラ内で捕捉）
- **完了条件:** staging で `python3 server.py` を kaz で手動起動し、`curl` で
  (a) `/connect/state` が `connected` を返す、(b) `tmux kill-session -t claude` 後に `session_missing` を返す、
  (c) `/connect/session` で `connected` に戻る、(d) `/logout` 後に `login_required` と URL を返す、
  (e) `/connect/code` に実コードを入れて `connected` に戻る。(a)〜(e) の curl 出力を findings に貼る。
- **リスク/戻し方:** ファイル削除のみ（他に触らない）。
- **コミット:** `feat(infra): claude_connect server — state/session/code over tmux`

### N-2 index.html（画面）

- **変更:** `infra/claude_connect/index.html` を新設。1ファイル・外部アセットなし・スマホ幅前提。
  - 5秒ごとに `/connect/state` を取得して描画。接続中以外はボタンと入力欄を**常に**出す
  - ページ見出しは製品名「KOBITOサーバークラウド」、副題「AIコードエージェント型 自社サイト運用システム」
  - ボタン文言は常に「セッションを再接続」。state により中身（session を POST するか、url があれば
    Claude の認証画面を `target=_blank` で開くか）だけが変わる。同じ位置・同じ見た目。入力欄はその直下に固定
  - 送信後は入力欄を空にし、state が `connected` になるまで「確認中」を出す
  - 文言は日本語のみ。ロケール機構・共通 CSS・共通 JS を使わない
- **完了条件:** iPhone Safari と Android Chrome の実機で、N-1 (b)〜(e) の4場面を**ページ操作だけで**
  通せる。別タブで認証して戻ってきたとき入力欄が同じ位置にある。
- **コミット:** `feat(infra): claude_connect page`

### N-3 systemd unit と setup

- **変更:** `infra/claude_connect/claude_connect.service`（User=kaz / WorkingDirectory=/src/thinkx-system/infra/claude_connect /
  ExecStart=/usr/bin/python3 server.py / Restart=always / After=claude-session.service）。
  `infra/setup/setup_claude_connect.sh` を linear bash で新設（symlink → daemon-reload → enable → start →
  verify は `curl -s http://<private ip>:8008/connect/state` の先頭行）。setup_claude_code.sh の末尾から
  呼ばない（1スクリプト1操作）。構築手順.md の該当箇所に1行追記。
  N-0 で setup-token が動いた場合は、その発行・配置手順をここに組み込む。
- **完了条件:** `systemctl is-active claude_connect` が `active` / staging を stop→start して
  両 unit が自動で上がり `/connect/state` が `connected` を返す。
- **戻し方:** `systemctl disable --now claude_connect` と symlink 削除。
- **コミット:** `feat(infra): claude_connect unit and setup`

### N-4 LB の location 追加

- **変更:** `infra/setup/nginx/staging.thinkxinc.com.conf` の 443 server ブロックに
  `location /connect/ { proxy_pass http://$web_backend:8008; 既存と同じ proxy_set_header 4行 }` を追加。
  Basic 認証は server ブロックのものがそのまま掛かる。reload は `nginx -t` が通ったときだけ
  （restart_loadbalancer.sh の既存手順）。
- **完了条件:** `https://staging.thinkxinc.com/connect/` が Basic 認証後に画面を返す /
  `https://staging.thinkxinc.com/` など既存 location の応答が変わらない（LB 経由の route sweep green）。
- **戻し方:** location ブロック削除 → reload。
- **コミット:** `feat(infra): route /connect/ on staging LB to claude_connect`

### N-5 Discord 通知（状態が変わったときだけ）

- **変更:** server.py に、state が前回と変わったときだけ `/etc/thinkx/discord_webhook` へ
  1行 POST する処理を足す（D-65 と同じ「同じ状況が続く間は黙る」）。文面は sync_from_origin.sh と同じ方針
  （内部名を出さない。「Claude の接続が切れました。https://staging.thinkxinc.com/connect/ から接続できます」）。
  定期監視は N-2 のポーリングに頼らず、server.py 内で 60 秒ごとに state を取る。
- **完了条件:** tmux kill → 60 秒以内に Discord に1件 / そのまま 5 分放置しても2件目が来ない /
  session で戻したとき「接続しました」が1件。
- **コミット:** `feat(infra): claude_connect notifies Discord on state change`

### N-6 runbook と記録

- **変更:** `infra/runbooks/claude-connect.md` を新設。内容は (1) 状態の意味と画面の対応表、
  (2) ページが動かないときの手動手順（attach_claude.sh で同じことをする）、(3) **ゼロから再実装できる粒度の要件**
  （GUIDELINES「status.sh をゼロから書こうと思ったらそれを見れば作れるようなもの」）。
  `infra/docs/運用.md` の staging 節に URL を1行。`infra/docs/DECISIONS.md` への追記は人間。
- **完了条件:** 上記ファイルが存在し、N-0 の実測文言が runbook に転記されている。
- **コミット:** `docs(infra): claude-connect runbook`

### N-7 最終検証（スマホのみで）

- staging を AWS コンソールから stop → start し、PC を触らずにスマホだけで
  (a) ページが `connected` を出す、(b) `/logout` 相当（人間が attach して実行）のあと
  ページから URL → 認証 → コード → `connected`、(c) tmux kill のあとボタン1回で `connected`、の3場面を通す。
- 3場面の所要時間を findings に記録（顧客向け説明の「復旧にかかる時間」の根拠にする）。
- **補助金申請用に、この時点で次の画面をスマホで撮る**（画面内に「KOBITOサーバークラウド」が写ること）:
  `/connect/` の画面（状態・ボタン・入力欄が見えるもの）→ `docs/hojokin/screenshots/shot_connect.png`
- ROADMAP のチェックは人間が更新。

## やらないこと

| 禁止事項 | 理由 |
|---|---|
| prod への配置 | 大原則1 |
| claude-session.service の変更 | 大原則3。動いているものを変えない |
| SG・terraform の変更 | 8008 で既存許可範囲に収まる。収まらない事実が出たら停止・findings |
| Claude の認証情報（トークン・cookie）の保存・表示 | 大原則2 |
| thinkx など各サイトの main.py への組み込み（filedrop 方式） | 製品として各サイトから独立させる。サイト側のルート・ゴールデンに触れない |
| 共通 CSS / locale / simplicity の利用 | 1ファイルで閉じる（D-69） |
| 停止中の staging を起動する機能 | ページ自体が staging 上にあるので原理的に不可。起動は AWS コンソール（既存手順） |

## 確定事項（2026-08-22 オーナー裁定／2026-09-04 製品名反映）

- path は `/connect/`、ボタン文言は「セッションを再接続」。顧客向けも同一。ページ見出しは製品名
  「KOBITOサーバークラウド」（旧称「KOBITO サーバー」から変更）。
- `claude setup-token` は N-0 で**実際に試す**（発行→常駐セッションでの動作→ログアウト相当の状況で
  ログイン要求が出るか）。動けば採用して N-3 の setup に組み込む、動かなければ捨てる。人間判断にしない。
