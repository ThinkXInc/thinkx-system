# podcast 統合トラック規約(PODCAST_TRACK)

方針(オーナー決定 2026-08-24〜08-28): podcast(切り出しパイプライン + タイムライン編集UI)を
monorepo に取り込み、編集UIを uWSGI で常時稼働させる。まず staging、次いで本番常設
(podcast/docs/DECISIONS.md D-030「他の作業者への提供は既存 EC2」の実装)。
fabula は取り込みのみ後日行い、サイト(fabula-method.com)の設計は別トラックとする。

設計の経緯はこのファイルではなく 2026-08-24〜28 のセッション記録が持つ。ここは確定形だけを書く。

## Phase 1: 取り込み(実施済み 2026-08-28)

- コピー元: `ThinkXInc/podcast` master の 2026-08-25 版
  (`21c9ce71058e2bd463ff2f19c8ef628ba8ae4879`、PR #1 マージコミット)。オーナー承認 2026-08-28
- 方式: `git archive` による無加工コピー(M-2 同型・歴史は運ばない)。秘密検査済み(実物なし。
  README の `sk-...` はプレースホルダ)。`data/` は podcast/.gitignore により非追跡
- ARCHIVE.md への出所行はオーナーが追記する(settings.json が実行者の ARCHIVE.md 書き込みを
  deny しているため。D-21 の代行記録ルールに従いこの文書と findings に記録)

## Phase 2: 構造合わせ + WSGI 化(実施済み 2026-08-28。8c4e262〜8704705)

- 他サイト(thinkx / kazukiotsukacom)共通構造に合わせる:
  `.env`(ルート直下) / `web-server/{main.py, requirements.txt, nginx/conf.d/,
  uwsgi/(uwsgi.ini + uwsgi_podcast.service), views/, tests/, venv/(git外)}`
- `web/preview_local.py` を Flask 化した `web-server/main.py` にする。ローカルは
  `python3 web-server/main.py` の1コマンド起動(Flask 内蔵サーバー)。標準ライブラリのみ
  という旧性質は失われ、ローカルにも venv が必要になる(承認済みのトレード)
- パスプレフィックスは uwsgi の `mount = /podcast=main.py` + `manage-script-name` で吸収する。
  アプリは自分が `/podcast` 配下にいることを知らない(url_for が解決)
- **書き出しはサーバーでも実行する**(オーナー指示 2026-08-28。「edit/ を回収してローカルで
  書き出す」は過去議論での Claude 提案であり、オーナー指示ではなかった — 不採用)。
  `export_audio.py` のエンコーダ `aac_at` は macOS 専用のため、Linux では ffmpeg 標準 AAC に
  フォールバックする。ffmpeg は setup_podcast.sh でサーバーに入れる
- ノイズ除去(MossFormer2)つき最終版書き出し: **サーバーに載せない**(モデル 211MB +
  venv_enhance 1.2GB + 重い CPU 推論)。ただし UI のボタン・入口は残し、除去処理部を
  差し替え可能に分離して、当面は除去なしで書き出す(オーナー指示 2026-08-28
  「処理だけ差し替えるつもりで UI 上は残せ」)
- `save_inbox.jsonl` を `edit_save_journal.jsonl` にリネームする(名前単体で役割が読めること。
  書き手 main.py と読み手 restore_edit.py を追随)

## データの扱い

- ディレクトリ構造はローカル・サーバーで同一: `podcast/data/<ID>/`。サーバー側の別置き
  (/srv 等)はしない(オーナー裁定 2026-08-28)
- git 追跡: `edit/*.json` + `segments_history.jsonl`(編集履歴はコミット履歴として残る)
- git 外: 音源・動画・generated/ の大容量バイナリ、`edit_save_journal.jsonl`(復旧用受信
  ジャーナル。各端末にだけ残る)
- 大物の配布: `infra/scripts/push_assets_podcast.sh <env> [ID...]`
  - env は `staging | prod` の必須引数(ホスト対応は内部で自動決定)
  - **ID を明示したときだけ新規 ID をサーバーへ公開**。引数なし(deploy からの自動呼び出し)は
    「サーバーに既にある ID だけ」を差分同期(未公開 ID を deploy のついでに公開しない)
  - **元WAV(source/)も送る**(サーバー書き出しに必要)。`edit/` には触れない(編集中の正は
    サーバー側)。push_assets.sh と同じ一覧突き合わせで、一致なら何もしない
  - 呼び出しは `deploy_staging.sh` / `deploy_production_from_staging.sh` に
    push_assets.sh の後のシリアル実行として1行ずつ足す(push_assets.sh の中に混ぜない —
    汎用規則とサイト固有例外を分けるオーナー裁定 2026-08-28)

## 編集データの push(保存トリガー同期)

外部 timer による dirty 監視は不採用(手による削除・移動の事故まで push してしまう)。
トリガーは編集アプリに置く:

1. main.py の保存処理が、自分が書いたファイルのパスを pending キュー(git外の小ファイル)に
   追記する。リクエスト内で git を叩かない(応答を遅らせない・push 失敗が編集を壊さない)
2. flusher(systemd 1分 timer)がキューだけを見る。空なら何もしない。
   「最後の保存から2分静止」または「最古の未 push が10分超過」で、**キューに載っている
   明示ファイルのみ** `git add <ファイル列挙>` → commit(`data(podcast): edit保存 <ID>
   @<host>`) → push してキューを消す。ディレクトリ単位の add はしない
3. 手による削除・移動はキューに載らないので push されない。dirty のまま残り、deploy timer が
   止まって通知される = 既存の安全装置がそのまま事故検知器になる
4. push 後は 60 秒以内に deploy timer が追従し、デプロイは自然復帰する

## 公開経路

- staging: **lb1-stg の EIP 直**(Host 名なしアクセス用 default_server ブロックを LB に追加)。
  URL は `http://{lb1-stgのEIP}/podcast/`。TLS なし(http)・Basic 認証あり。
  DNS・証明書・SG・terraform の変更なし
- 増設規則: 同型の直アクセスサイトは LB の同ブロックに `location /<site>/ → web の専用ポート`
  を1行ずつ足す。サイト側は自分のフォルダに nginx conf / uwsgi を持つ(既存サイトの
  増やし方と同一)。podcast は設計済みのポート 8010 / socket `/tmp/uwsgi_podcast_web.sock`
- nginx-web-root の予約 include 行(nginx.conf 81行目)を
  `/src/podcast/web-server/nginx/conf.d/*.conf` に修正して有効化する

## Phase 3: staging 稼働(ゴール = 編集UIがブラウザで開く)

コード・conf・スクリプトは作成済み(2026-08-28)。残りはサーバー上の実行のみ:

1. 手順書 1→2→3 でデプロイ(nginx-web-root include・loadbalancer/conf.d/direct.conf・
   podcast/ 一式が staging に乗る)
2. web1-stg で `bash infra/setup/setup_podcast.sh`(ffmpeg・venv・uwsgi_podcast・flusher)
3. lb1-stg で `bash infra/setup/setup_podcast_lb.sh`(Basic 認証ファイル。最終行が対話)
4. オーナー機で data をローカル `podcast/data/` へ移し、edit/ をコミット。
   `bash infra/scripts/push_assets_podcast.sh staging <ID>` で大物を搬入
5. 確認 URL `http://{lb1-stgのEIP}/podcast/` をオーナーに提示して目視確認

## Phase 4: 本番常設(staging OK 後)

- 同構成を web1 へ。デプロイは本番経路(L2b またはオーナー機 4番)
- **未決**: 本番サーバーの編集データ push は `production` ブランチに積むことになる。
  release 入れ直し運用(戻し方)との整合はこの Phase の冒頭で設計する

## Phase 5: fabula(保留)

- 取り込みは Phase 1 と同型でいつでも可(音声ファイルが git 内にあり重い点だけ留意)
- fabula-method.com は配信物の設計から始める独立作業。ドメイン取得・Route53・証明書を含む
