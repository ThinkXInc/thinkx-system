# Runbook: Claude 接続ページ(/connect/・staging のみ)

staging の web に常駐する Claude Code セッション(tmux `claude`・`claude --remote-control`)が
「接続中」でなくなったとき、スマホのブラウザだけで戻すためのページ。
URL: https://staging.thinkxinc.com/connect/ (Basic 認証は staging と同じ)。
計画書: `infra/docs/CLAUDE_CONNECT_PLAN.md`。実測の記録: `infra/findings.md` 2026-09-04〜05。

## 1. 顧客・運用者がやること(3 行)

1. https://staging.thinkxinc.com/connect/ を開く。緑の「接続中」なら何もしない(Claude アプリのセッション一覧から開く)。
2. 「接続されていません」なら「セッションを再接続」を押す。認証画面が開いたら Claude アカウントで認証する。
3. 認証後に出たコードをボタン直下の欄に貼って「送信」。「接続中」になったら Claude アプリを開く。

## 2. 状態の意味と画面の対応

| state | 判定(server.py) | 画面 | ボタンの動作 |
|---|---|---|---|
| `connected` | tmux `claude` あり・pane のコマンドが `claude`・`claude auth status` の `loggedIn` が true | 緑「接続中」+「Claude アプリのセッション一覧から開いてください」。ボタンなし | — |
| `session_missing` | `tmux has-session -t claude` が失敗 | 橙「接続されていません」+ボタン+入力欄 | unit と同じ `tmux new-session -d -s claude -c /src/thinkx-system "claude --remote-control"` |
| `login_required` | `loggedIn` が false(claude が居ない場合も含む)、または pane にログイン画面(URL / `Paste code here` / 初回対話) | 同上。URL が取れていれば「ボタンを押すと認証画面が開きます」 | claude が居なければ tmux を作り直し、初回対話(`Choose the text style` → `Select login method` → URL)を Enter で進めて URL を返す。URL があればそれを別タブで開く |
| `unknown` | 上のどれでもない(ログイン済みなのに pane が shell に戻っている等) | 橙「接続されていません」+ボタン+入力欄 | tmux を kill して作り直す |

コード送信(`POST /connect/code`)は pane が `Paste code here` を出しているときだけ受け付け、
`tmux send-keys -l <code>` → Enter → `Security notes` の `Press Enter to continue` を Enter で抜けて、
`/remote-control is active` が出るまで待つ。コードはログに出さない。

画面の隅に `df /` の空き(GB)と観測時刻(UTC)を出す。

## 3. 実測した文言(Claude Code 2.1.223・2026-09-04)

- `/logout` は claude 本体を終了させる(pane は shell に戻る)。
  ```
  Successfully logged out from your Anthropic account.
  Resume this session with:
  claude --resume <session id>
  ```
- 未ログインで `claude --remote-control` を起動したときの順: `Choose the text style that looks best with your terminal`
  → `Select login method:`(1. Claude account with subscription)→
  ```
   Browser didn't open? Use the url below to sign in (c to copy)
  https://claude.com/cai/oauth/authorize?code=true&client_id=...&state=...
   Paste code here if prompted >
  ```
  → コード貼付 → `Security notes:` … `Press Enter to continue…` → 通常画面
  ```
  /remote-control is active · Continue here, on your phone, or at
  https://claude.ai/code/session_...
  ```
- URL は pane 幅で複数行に折れて描かれる(ハード改行。`capture-pane -J` でも戻らない)。行頭が `http` の行から、
  `Paste code here` / 空行 / 行頭空白の手前までを連結する。
- `claude auth status`(既定 `--json`)は `{"loggedIn": true|false, "authMethod": ..., ...}` を返す。
- `tmux list-panes -t claude -F '#{pane_current_command}'` は接続中 `claude`、claude 終了後 `bash`。

## 4. ページが動かないときの手動手順(PC から)

```bash
cd ~/Sources/thinkx-system
bash infra/scripts/attach_claude.sh
```
attach 先で状況に応じて:
- shell に戻っている → `claude --remote-control` を打つ。ログイン画面が出たら URL を開いて認証し、コードを貼る。
- 何も無い(tmux が無い)→ attach_claude.sh が新規に作るので同上。
- claude が固まっている → Ctrl-C で抜けてから同上。
- デタッチは Ctrl-b d。**`exit` で shell を抜けると tmux サーバーごと消える**(ページの「セッションを再接続」で戻る)。

サーバー側の確認:
```bash
ssh supercom-web1-stg 'systemctl is-active claude_connect claude-session; sudo -u kaz tmux ls; sudo -u kaz claude auth status; curl -s http://192.168.2.11:8008/connect/state'
```
`claude_connect` が落ちていれば `sudo systemctl restart claude_connect`、ログは `journalctl -u claude_connect`。

## 5. ゼロから再実装できる要件

- 配置: `infra/claude_connect/{server.py,index.html,claude_connect.service}` / `infra/setup/setup_claude_connect.sh` /
  LB: `loadbalancer/conf.d/staging.thinkxinc.com.conf` の `location /connect/`(web:8008 へ proxy)。
- server.py: python3 標準ライブラリのみ(http.server / json / subprocess / shutil)。kaz で動き、
  `hostname -I` 先頭の private IP:8008 に bind。`GET /connect/`(index.html)/ `GET /connect/state` /
  `POST /connect/session` / `POST /connect/code`。subprocess は全て引数リスト・shell なし。tmux への文字列は `send-keys -l`。
  コードは `[A-Za-z0-9#_-]{1,512}` で先頭 `-` 不可。例外はハンドラ内で捕捉して 500 と短い理由。
- index.html: 1 ファイル・外部アセットなし・日本語のみ。ロゴは `infra/assets/KOBITO/logo/KOBITOhT.png` を 720px に縮小し
  data URI で内包。5 秒ごとに state を取り、接続中以外は常に「セッションを再接続」(#070707)と入力欄を同じ位置に出す。
  ボタンはタップ内で空タブを開き、`/connect/session` の応答の URL をそのタブに流し込む(Safari の制限を避ける)。
- unit: `User=kaz` / `WorkingDirectory=/src/thinkx-system/infra/claude_connect` / `ExecStart=/usr/bin/python3 server.py` /
  `Restart=always` / `After=claude-session.service`。setup は symlink → daemon-reload → enable → restart → verify。
- 大原則: staging 限定 / 認証情報を預からない / claude-session.service を変えない / 依存を増やさない /
  観測した文言を正にする(推測で判定を書かない)。
- やらないこと: prod 配置・SG/terraform 変更・トークン保存・各サイト main.py への組み込み・停止中 staging の起動。
