# Claude Code への作業指示書（web-server = タイムライン編集サイト）

podcast の編集UIを配信するサイト。音源(ID)ごとに1ページで、文字起こしがそのまま
タイムラインになり、ブラウザだけでカット編集から書き出しまで完結する。
thinkx / kazukiotsukacom と同じサイト構造（web-server/ + main.py + uwsgi + nginx conf.d）。
トラック全体の確定事項は `thinkx-system/docs/PODCAST_TRACK.md`（D-52）が正。

## 構成

- `main.py` … Flask アプリ本体（描画・保存・書き出し起動のすべて）
- `requirements.txt` … 専用 venv 用（本体 venv とは別。1コンポーネント1venv の例外）
- `uwsgi/uwsgi.ini` + `uwsgi/uwsgi_podcast.service` … 本番・staging の常駐起動
- `nginx/conf.d/podcast.conf` … nginx-web-root が絶対パスで include する
  （ポート 8010・socket `/tmp/uwsgi_podcast.sock`。他サイトと衝突しない値）
- `tests/timeline_logic_test.js` … タイムライン区間ロジックの検証（node で実行）

## 起動

- **ローカル(mac)**: `venv/bin/python main.py` → `http://127.0.0.1:8010/`。
  nginx / uwsgi は不要（Flask 内蔵サーバー。音源の Range 配信も main.py が行う）
- **サーバー**: `systemctl start uwsgi_podcast`。公開 URL は `/podcast/` 配下
  （プレフィックスは uwsgi の mount + manage-script-name が剥がすので、
  main.py はプレフィックスを知らない。リンクは url_for / request.script_root で作る）

## データ

- data の場所は既定で `../data`（= `podcast/data/`）。ローカルもサーバーも同一構造
  （D-52。サーバー別置きはしない）。`SITE_DATA_DIR` で上書き可
- 生成物（音源・動画）は本番では nginx が `/podcast/media/` として data/ を直接配信。
  ローカルは main.py の /media ルートが同じパスで配信する
- 編集の保存先は `data/<ID>/edit/`（git 追跡）。保存のたびに、書いたファイルのパスを
  `data/.pending_sync.jsonl` に追記する（サーバー側の flusher が git commit/push する
  ためのキュー。D-52「保存トリガー同期」）
- `edit/edit_save_journal.jsonl` … 受信した保存内容の完全ジャーナル（git 外・復旧用。
  読み手は `scripts/restore_edit.py`。旧名 save_inbox.jsonl も読める）

## 方針

- data を唯一の正とし、コピー・複製しない。DB やビルド工程は持たない
- 書き出し（export_audio.py）はサーバーでも実行する。ノイズ除去（MossFormer2）だけは
  サーバーに置かない — UI のチェックボックスは残し、環境が無ければ明示エラーにする
  （処理部は将来差し替える。D-52）
