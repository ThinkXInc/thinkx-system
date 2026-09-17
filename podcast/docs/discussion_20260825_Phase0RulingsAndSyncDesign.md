2026-08-25 Phase 0 裁定と同期設計の詰め（生ログ）

引用（太字）が発案者の発言で、原文のまま。続く地の文が Claude の応答（実際に返した内容。
冗長な部分のみ圧縮）。時系列。確定事項は thinkx-system/docs/PODCAST_TRACK.md（D-52）が正。

> **Phase 0 — 裁定(オーナー決定事項、作業前に確定)**  
> **1. 取り込み ref の承認: 両リポジトリ main HEAD の SHA を実測して提示 → 承認(M-0 と同じ型)**  
>
> **podcast master ブランチが最新の正であることに注意**  
>
> **1. フォルダ名の裁定: podcast/ を推奨(リポ内 conf が全部 /src/podcast 前提のため。nginx-web-root 側の予約行 podcast-pipeline を1行修正する方が安い)**  
>
> **thinkx-system/podcastを想定**  
> **構造は他のthinkx等のサイトと同じように**  
> **つまり**  
> **.env**  
> **web-server/views**  
> **web-server/venv**  
> **web-server/main.py**  
> **など同じ構造に**  
> **念の為kazukiotsukacomなども共通項チェックせよ**  
>
> **1. 「編集UIを開く」の定義: 当面 preview_local.py でよいか(uWSGI 版 app は未実装のため)**  
>
> **常にuwsgiが起動しstagingさえ稼働していれば常にネット上に開いている状態を想定**  
> **ゆえに明示的に.pyで開くということは想定していない**  
> **単にグローバルアドレス(EIP)にアクセスするだけ（ドメインは取得しないため）**  
>
> **1. staging での外部公開方式(推奨は a):**  
> **thinkxinc.comドメインでホストする意味は？TLS？外部公開しなくてもTLSやドメイン必要？**  
> **でないならhttp://{EIP} やhttps://{EIP}でいい**  
> **ドメインがいるなら stating.thinkxinc.com/podcast がトップになるように その場合は上記の通りポート番号でLB->webにルーティングすることになるだろう**  
> **それはあまりやりたくないから単に{EIP}にしたい**

回答の要点:

- ドメインの意味は実質「正規のTLS証明書が取れる」だけ。SGで絞れるなら http://{EIP} で成立
- podcast master は当日（8/25）タイムライン編集UI入りの PR #1 がマージ済みで、
  「枠だけ」ではなくなっていた。master HEAD = 21c9ce7
- thinkx / kazukiotsukacom の共通構造（.env / web-server/{main.py, uwsgi/, nginx/conf.d,
  views, venv, requirements.txt}）を実測し、podcast をこの型に改組する案を提示

> **LBを通さないとして他のサイトと構造が変わるならむしろ共通構造がいい**  
> **変わらないならEIPに直接アクセスでいい**  
> **ただし**  
> **http://{web1-stgのEIP}/podcast**  
> **のように同様の直アクセスサイトを複数増設できる前提に**  
>
> **-> local macでも引き続き使うからその前提で　簡単にlocal起動できるように main.pyだけでいいのか**  
>
> **->これはthinkxinc.comの動画などと同じアセット扱いということか？**  
> **編集履歴などはレポジトリ管理したい**

回答の要点:

- LB 経由の方が既存構造そのもの（LB に Host 名なしの default_server + location /podcast/ →
  web:8010）。URL は http://{lb1-stgのEIP}/podcast/。増設は location 1行ずつ
- Flask 化すれば `python3 web-server/main.py` の1コマンドでローカル起動できる
  （「依存ゼロ」は失われ venv が要る）
- データは分離: 大物バイナリ=アセット扱い（git外）、edit/ の JSON と編集履歴=git 追跡。
  当初サーバーのデータ置き場を /src の外に出す案を提示

> **-> OK**（deploy スクリプトからのシリアル実行）  
> **-> 同意**（手動一発の場面がない）  
> **-> \<host\>はいるのか？staging以外に想定していない**  
> **-> 元wavが必要になる場面がない？そもそもそれなしで編集できる？**  
> **-> もちろん**（edit/ に触れない）  
> **-> OK**（一覧突き合わせ）  
> **基本的にいいが，仮に間違えてデータを消したり移動したりしたときにそれがpushされてしまうことは？**  
> **外部timerがトリガーは正しいのだろうか**  
> **例えば編集したら書き込みが動いているはず**  
> **その時に最後にpushした時刻を見て一定時間経っていたらpushするというのは？**  
> **そうすれば意図した変更だけ確実にpushされないか？**  
>
> **edit_history_jounal.jsonl の方がわかりやすい気がするが合理的な方で**

回答の要点:

- host 引数は Phase 4（本番常設）で同じスクリプトを使うため必要。当面 staging のみ受け付ける
- 編集の再生は preview_audio.m4a を最優先で使う設計が既にあり（D-021）、元WAVなしで編集可能。
  元WAVが要るのは書き出し・ノイズ除去のみ
- push トリガーはオーナー案を採用して補強: 外部 timer の dirty 監視は「事故も正当な保存も
  区別できない」ため廃止。保存処理が書いたファイルパスをキューに記録し、flusher が
  「静止2分 or 最古10分」でそのファイルだけ add/commit/push。手による削除・移動は
  キューに載らないので push されず、dirty で deploy timer が止まって発覚する
- ジャーナル名は segments_history.jsonl（履歴の本体）との衝突を避け edit_save_journal.jsonl を採用

（8/28 の承認・取り込み実施へ続く → discussion_20260828_ApprovalAndImport.md）
