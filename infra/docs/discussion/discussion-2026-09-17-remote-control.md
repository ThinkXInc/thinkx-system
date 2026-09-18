# thinkx-system/infra/docs/discussion/discussion-2026-09-17-remote-control.md

2026-09-17 KOBITO リモコン本番入口(/remote_control/)の実装 — staging 電源、GitHub ルールセット、本番 .env 事故と復旧(生ログ)

引用(太字)がオーナーの発言で、原文のまま。続く地の文が Claude の応答(冗長な部分のみ圧縮)。時系列。
成果物は `infra/terraform/{iam.tf,instances.tf}`、`thinkx/web-server/main.py`(/remote_control/)、`infra/claude_connect/{index.html,server.py}`、
`loadbalancer/conf.d/staging.thinkxinc.com.conf`、`infra/etc/push_remote_auth.sh`、`infra/docs/KOBITO_セットアップ手順.md`。
前回分は `discussion-2026-09-06-remote-control.md`。

---

**「今どういう状況？　リモートコントロールは使える？ステージングをオンオフ試したいのだが どこまでやって何が残ってるかまとめて」**

使えるもの(staging の /connect/ 4 機能)と未着手(ページからの起動・停止)を整理。stop/start は当面 Mac のコマンド。

**「まだ無いもの: ページからの staging の起動・停止 これを進めよう 今のページは staging 上にあるので、staging を止めるとページも消えます。->どういうこと？消える？止めるとは単に停止するだけでしょ？データは消えないでしょ？停止したからといって中の編集が消えるのはあり得ないからそういう仕様なら見直せ 前回の 4 点…これじゃ内容を思い出せない」**

「消える」は「停止中はページを開けない」の意味でデータは EBS に残ると訂正。4 点(ロールは本番だけ / staging LB は本番 IP を satisfy any で通す /
本番 .env に staging 認証を置かない / `/remote_control/`)を言い直し、下書きに反映。P-0 前提ゲート成立(boto3・requests あり、IMDSv1 有効、
staging 2 台のみ、全体 plan No changes)。

**「４点をチェックしたがその仕様は問題ない」**

P-1(index.html を相対パス化+電源カード)、P-1b(staging LB の satisfy any)、P-2(iam.tf/instances.tf: prod のみロール・IMDSv2、plan 3 to add 1 to change)、
P-3(main.py に /remote_control/・power/*・中継、ゴールデン 3 行)を実装。P-1 の変更は別セッションのコミット 1ffe5eb に巻き込まれた(記録)。

**「RuntimeError: git push --quiet origin …:production が失敗: Locking support detected on remote…」**

本当の理由は `GH013: Changes must be made through a pull request`(ルールセット production protection・2026-08-07・bypass 空)。
9/6 の「保護なし」判断は旧 API を見た誤り。選択肢 3 つを提示し、Deploy keys のバイパス追加を推奨。server.py は stderr を返し release を使い回すように修正。

**「ルールセットのバイパスに「Deploy keys」を加える（推奨）… この手順はKOBITOユーザー全てが行うので繰り返し行うのに迷わないようセットアップマニュアルの一部に記録して 今後同様にこの仕組みを使うのに必要な設定がでてきたら追記する」**

`infra/docs/KOBITO_セットアップ手順.md` を新設(書き込み鍵・ルールセットとバイパス・IAM ロール・.env・LB・動作確認)。GUIDELINES とメモリに記録。

**「バイパスを追加した btwで確認した内容を手順書に簡潔にまとめて記録できるか https://share.evernote.com/note/… この下線を特に」「3, 4とは？ここに出さないとわからない　Evernoteの説明はわかりやすいのでなるべくそのまま書いたか確認しろ」**

API で bypass(DeployKey/always)を確認。Evernote の本文を Chrome で読み、当初は要点に圧縮したが、指摘を受けて原文どおり(下線込み)に置き換え。
3(terraform apply)・4(.env)のコマンドをその場に提示。

**「(apply は差分なし・ロール名が出た)」「(read/ssh の貼り付けが折り返されて分割実行)」「それはできた ボタンを押したが最後に Unexpected token '<', "<html> <h"... is not valid JSON」**

本番反映は成功(production 進行・/remote_control/ 401)。画面のエラーは staging LB の 60 秒 timeout → `proxy_read_timeout 300s`。
.env の宛先を `/src/thinkx/web-server/.env` と誤っていた(本物は `/src/thinkx/.env`)ため `push_remote_auth.sh` を新設。

**「(push_remote_auth.sh 初版の出力: Permission denied ×2 / FAIL 500)」**

**事故**: 初版が fs.protected_regular=2 の /tmp で書けず、空ファイルで /src/thinkx/.env を上書き → 本番全ルート 500(08:43〜08:53)。
Mac の thinkx/.env を push_env.sh で配り直して復旧。スクリプトを「root の python が原子的に差し替え・空なら止まる」に書き直し、staging のコピーで試験。

**「(修正版で OK: 認証あり=200 / なし=401 / トップ=200)」「ボタンを押したが内容を確認0秒から動かない」**

本番 Flask の中継が 110 秒応答を待つ間、本番 LB が 60 秒で切断し、uwsgi(processes=1 threads=1)で本番サイト全体が待ち。
「本番に反映」を非同期(202 で受け付け、state.deploy で完了)に変更。uwsgi の並列数はオーナー判断として記録。

**「今押したら本番と同じだから反映するものがないという テストしたいから適当に変更して サイトを変えないなにか」「Claudeを開くボタンが出なくなった　なぜ」「ボタンを押すと Claude のチャット画面が開きます この表示いらないだろ」**

再起動でメモリの URL を忘れていた。`~/.claude/sessions/<pid>.json` の `bridgeSessionId` から URL を組むように修正。案内文を削除。

**「undefined を本番に出しました。本番の応答: 確認できません(undefined)。」「もう一度テストするから適当な変更出して」「> ❯ ボタンを押すと Claude のチャット画面が開きます さっき消したこの部分ちゃんと間を詰めろよ」「もう一回テストするから適当な変更出して」**

古い版の画面が 202 を完了と誤解した表示で、実際は release/2026-09-17-4 が反映済み。空の案内文・エラー行を消して間を詰めた。
文書だけの差分を 2 回用意して本番入口からの反映を試験(2 回目は押下待ちで終了)。

**「OK このセッションは一度閉じるのでCLAUDE GENERALに従い記録して」**

本ファイル群・DECISIONS・GUIDELINES・findings・メモリを記録。残作業: P-4(本番入口からの staging 停止→起動→Claude を開く の通し)、
P-5(SECURITY.md の web ロールの行と運用.md の URL・オーナー)、別件(本番 thinkx の uwsgi 1 プロセス、未使用 Deploy key thinkx-system-rw の削除)。
