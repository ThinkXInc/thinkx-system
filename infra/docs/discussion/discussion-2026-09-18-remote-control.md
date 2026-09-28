# thinkx-system/infra/docs/discussion/discussion-2026-09-18-remote-control.md

2026-09-18 KOBITO リモコン「Claude を開く」が archive 済みセッションを開く問題の調査と修正(生ログ)

引用(太字)がオーナーの発言で、原文のまま。続く地の文が Claude の応答(冗長な部分のみ圧縮)。時系列。
成果物は `infra/claude_connect/{server.py,index.html}`(commit f9ae176・d33bafc、本番 release/2026-09-18-5・-6)。
経緯の詳細は `infra/findings.md` 2026-09-18、前回分は `discussion-2026-09-17-remote-control.md`。

---

> **今stagingをKOBITO remote_controlで起動し Claude を開くボタンを押すと session already archivedになる　正しいセッションのurlが取得できていないか起動していないようだからチェックしろ**
>
> **直近のKOBITOリモコン関連の議事録も読んだほうがいいだろう**

server.py・index.html・9/17 議事録・staging 実機(journal)を突き合わせて原因を特定。
(1) server.py の記憶ファイル `~/.claude_connect_remembered.json` は EBS に残るため、staging の停止→起動を跨いで前回の(停止時に archive 済みの)セッション URL を持ち越す。消すのは server.py 自身の start_session() だけで、boot 時の claude-session.service 経由では消えない。boot 後 claude が `~/.claude/sessions/<pid>.json` を書くまでの十数秒(実測 08:24:57 起動→08:25:07 書き込み)、/connect/state は connected + 古い URL を返す。
(2) 画面は同日採用の案 A で state が一度取れるとポーリングを止めるため、この窓で取った古い URL が「Claude を開く」の href に固定され、リロードするまで直らない。
journal 実測: 新 boot 後の state 取得は 08:25:06〜08 でちょうど書き込み前後の窓。サーバー自体は sessions ファイル書き込み後に自己修復しており、pane の表示と一致する正しい URL を返していた。findings に記録し、恒久対処 (a) 記憶に pid を添えて無効化 / (b) URL が出るまで追う、の 2 案を提示。

---

> **今リモコンで停止　再起動したが　claudeはarchiveが開かれる**
>
> **いやしばらくしてまたClaudeを開くを押したらセッションが開かれた**
>
> **もう一度試してみる　待ち時間が発生するということだろうか**
>
> **時間というより再起動後にリロードが必要らしい**

2 回目の停止→起動(boot 08:52:31→URL 確定 08:52:43)でも同型を再現。「しばらくして開けた」「リロードで直る」はいずれも診断と整合(画面が古い URL を固定しているだけで、サーバーは自己修復済み)。恒久対処 (a)(b) を両方実装:
- server.py: 記憶に pane の pid を添えて保存し、pid が違えば返さない(server.py 再起動を跨ぐ 9/17 の本来の目的は維持・旧形式は無効扱い)。モック tmux の機能テスト 9 件 PASS。
- index.html: connected でも session_url が無い間だけ POLL_GIVEUP 回を上限に追い、URL が出たら止める。
commit f9ae176 → develop → deploy_staging.sh(途中、停止中で 2 回失敗→起動待ちで完走)→ claude_connect.service 手動再起動(デプロイの自動再起動対象に claude_connect が無いことを findings に記録)。本番反映コマンドを提示。

---

> **リロードするまでClaudeを開くボタンがでなくなったが**
> **リロードしなくてもボタンが最初から出ていて新しいリンクで開けないのか？時間がかかるならボタンは新しいリンクが準備できるまでdisableにするか リロードしないとリンクを差し替えできないなら（できるだろう）仕方ないが**
>
> **stagingのサイトは使ってない　本番でチェックするからそのつもりでいろ**

「ボタンが出なくなった」のは修正配布前の古い JS を積んだタブでの現象(画面 JS はページ内蔵のため、画面修正後の初回だけリロードが要る)。リンク差し替え自体はリロード不要でできるので、指示どおり「ボタンは最初から表示・URL 準備中は disable・準備できたら有効化」に変更。再接続・コード送信の直後に connected で URL 未取得の場合も追いかけを再開するようにした。確認は常に本番入口 /remote_control/ で行う前提(画面 HTML は本番 web の checkout から配られる)を踏まえ、以後は本番反映までを段取りに含めることにした。

---

> **disable中はなぜ押せないかわかるようになっているか確認を**
>
> **/connectでなくremote_controlでチェックしているという意味**

disable 中はボタン直上に「セッションの URL を準備しています。準備ができるとこのボタンが押せるようになります(十数秒)」と理由を表示するよう文言を追加。ローカルのモック state(2 回 null→3 回目 URL)+Chrome 実測で、disable 表示 → リロードなしで有効化+href 差し替えを確認し、スクリーンショットを送付。commit d33bafc → develop → 本番反映コマンドを提示し、オーナーが本番へ反映(release/2026-09-18-6 に含まれることを確認)。

---

> **OK**
> **このセッションは終わる**

終了時記録(本議事録・DECISIONS・GUIDELINES・findings・メモリ)を実施。

## 到達点

archive 済みセッションが開く原因は「EBS に残る記憶ファイル+起動直後の URL 未確定の窓+一度取れたら止まる画面ポーリング」の合わせ技で、サーバー側(記憶を pane の pid で無効化)と画面側(URL が出るまで追う・ボタンは disable で常時表示・理由を注記)の両方を修正し本番まで反映済み。以後は停止→起動してもリロード不要で「Claude を開く」が disable→有効化の動きになる。オーナーの動作確認は常に本番入口 /remote_control/ で行う。
