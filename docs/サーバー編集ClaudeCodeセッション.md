# docs/サーバー編集ClaudeCodeセッション

### 概要
EC2上で`claude --rc`を実行したtmuxセッションが常駐している．  
これはMaxプランアカウントでログインしてある．  
このtmuxセッションに繋げばどのPCからでもclaudecodeに指示ができる． 
アカウントの保有者はリモートコントロール機能でスマホから指示がだせる.  

### セッションの起動
tmuxセッションをstagingサーバー上に立ち上げる.  
または立ち上がっているtmuxセッションにつなぐ.
```bash
cd ~/Sources/thinkx-system
bash infra/scripts/attach_claude.sh
```
初回はURLが出るのでブラウザに打ち込みログイン.Authentication codeを貼り付けると認証．

### 他者との共有
Prerequisites:
- アクセスする環境のIPがterraformのmy_office_ipsに登録されていること
```bash
cd ~/Sources/thinkx-system
bash infra/scripts/add_current_office_ip.sh
```
- ターミナルを開けること.
- sshのpublicキーがstagingに置かれssh接続できること.~/.ssh/configに次のように設定されていること.
```
Host supercom-web1-stg
  HostName 57.182.107.57
  User ubuntu
  IdentityFile ~/.ssh/supercom.pem
```

リアルタイムでセッションは共有される.

### セッションの振る舞い
- ターミナルでウィンドウやタブを閉じてもサーバー上のtmuxセッションは生きている. attach_claude.shで唯一のセッションに接続される．
- サーバー上(tmux 共有セッション)の Claude Code は誰が打鍵したか判別できない。


### セキュリティ
- /home/kaz/.claude内の履歴は全員が読めるので個人的な内容は送信しないこと.
- 直接ClaudeCodeが対話相手を知ることはできないが，誰がssh接続して対話したかは調べればわかる.


### 役割

開発者と非開発者では異なる応答をさせる．
プロファイルが変えるのは説明の仕方だけで、権限(破壊操作・secrets・本番反映のゲート)は変えない.

#### プロファイル

A) 開発者(kaz ほか)
- 通常どおり。diff・コード・技術用語・ファイルパス可

B) 非エンジニア(広報・デザイン確認など)
- 専門用語を避け、普通の言葉で話す
- コード・diff・ログを見せない。変更は「どのページのどこがどう変わるか」で説明する
- 確認は https://staging.<ドメイン>/ の実際の見え方で案内する
- 要望は受け取ったら「何をどう変えるか」を言葉で復唱して合意してから編集する
- 本番への反映はここでは行われないこと(開発者が別途反映すること)を必要に応じて伝える
