# web-server — podcast タイムライン編集サイト

音源(ID)ごとに1ページ。文字起こしがそのままタイムラインになり、ブラウザだけで
カット編集（スプリット・トリム・undo/redo・自動保存）から m4a 書き出しまで完結する。
作業方針は `CLAUDE.md`、トラック全体は `thinkx-system/docs/PODCAST_TRACK.md` を参照。

## セットアップ（初回のみ）

```
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt
```

## 起動

ローカル(mac):
```
venv/bin/python main.py
```
→ `http://127.0.0.1:8010/`（data は `../data`。`SITE_DATA_DIR` で上書き可）

本番・staging:
```
sudo systemctl start uwsgi_podcast
```
→ nginx(8010) → LB 経由 `http://{EIP}/podcast/`

## テスト

```
node tests/timeline_logic_test.js
```
