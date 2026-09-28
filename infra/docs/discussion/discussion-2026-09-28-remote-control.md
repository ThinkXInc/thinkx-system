# thinkx-system/infra/docs/discussion/discussion-2026-09-28-remote-control.md

2026-09-28 KOBITO リモコン「セッションを再接続」が無反応 — claude root→user 切替による PATH 断絶の調査(生ログ)

引用(太字)がオーナーの発言で、原文のまま。続く地の文が Claude の応答(冗長な部分のみ圧縮)。時系列。
本セッションは調査のみ(修正は別セッションが担当)。実測の詳細は `infra/findings.md` 2026-09-28。

---

> **KOBITOのClaudeセッション再接続ボタンを押しても接続されていません　セッションを再接続ボタン　が表示されるだけで一向に動かない　Claude認証への遷移が失敗しているだけなのかなんなのかわからない**
>
> **最近claude updateをしたがrootのclaudeだったので問題がありuserのclaudeプロセスに切り替えた経緯も踏まえて調査しろ**

server.py・両 unit・stg.py(check/doctor)・staging 実機(journal・PATH 実験)を突き合わせて原因を特定。

- claude の実体は kaz の `~/.npm-global/bin/claude`(2.1.283・symlink 作成 09:31 UTC)へ移行済みで、
  root 導入分(`/usr/bin/claude`・`/usr/lib/node_modules/@anthropic-ai`)は消滅。
- `~/.npm-global/bin` は kaz の `.profile`/`.bashrc` でしか PATH に乗らず、systemd の既定 PATH には無い
  (env -i の systemd 同等 PATH で `command -v claude` → 見つからないことを実測)。
- そのため (1) boot の claude-session.service が作る tmux 内の `claude --remote-control` が
  command not found で pane 即死 → tmux サーバーごと消滅(unit は Type=forking+RemainAfterExit で
  active のまま・journal 無音)。09:38:44 boot 直後から state=session_missing。
  (2) ボタン(POST /connect/session、09:39 に 3 回)が作る tmux も同じ理由で即死し、
  約 18 秒待って session_missing のまま → 画面はボタンを出し続ける。
- 認証への遷移が失敗しているのではなく、認証画面に到達する前に claude 自体が起動できていない。
  認証情報は無傷(ログインシェルで `claude auth status --json` は loggedIn:true・形式は 2.1.223 と同一)で、
  PATH を通せば再ログイン不要で connected に戻る見込み。

修正案 2 つを提示: (a) 両 unit に `Environment=PATH=/home/kaz/.npm-global/bin:...` を追記(推奨・server.py 無変更)、
(b) ExecStart と server.py の claude を絶対パス化(D-21 流・変更 3 箇所)。あわせて `setup_claude_code.sh` が
`sudo npm install -g`(root 導入)のままで実態と乖離している点を指摘(D-32: user 導入手順の原文をもらって
setup と KOBITO_セットアップ手順へ反映が必要)。findings.md に記録。

---

> **別のセッションで同じ問題を扱っている　ここは閉じる**

クローズ記録(本議事録+findings)を実施して終了。修正の実施は同問題を扱っている別セッションに委ねる。

## 到達点

ボタン無反応の原因は「claude の root→user 切替で、systemd(claude-session.service / claude_connect.service)から
`claude` が PATH 上見えなくなった」こと。画面・server.py のロジック・認証情報は正常。修正(unit への PATH 追記
または絶対パス化+setup_claude_code.sh の実態合わせ)は別セッションが実施する。
