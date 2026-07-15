# kazukiotsukacom findings(S トラック / Phase 2.5)

規範: `thinkx/refactor_plan.md`(静的サイト群 vendoring カットオーバー計画 v1.1・正本は thinkx 側1箇所)。
本ファイルは kazukiotsukacom リポジトリ直下(計画 大原則3)。Security exception は即停止・報告(D-22)。

---

## S-0a 前提ゲート(2026-07-07・確認のみ・詳細は thinkx/findings.md と共通)

- libcommon `v2.0.0` タグ存在 / `bake.sh` 存在 / tree_sha256 再算出一致
  (`3359309a30a392a75a97b3fad594569487cb07068f770877202de3096fb57cf0`)/ ruff・pyright green。
- settings.json スコープ切替は人間が適用済み。
- F-S1(別トラック記録): libcommon の bare `pytest` に旧世代テスト由来の collection error 3件
  (nose/torch 欠落)。v2.0.0 デリバラブルとは無関係。詳細は thinkx/findings.md 参照。

---

## S-0b スモークハーネス(2026-07-07)

### 消費面の実測(計画 大原則2 の裏取り)
- kazuki main.py / flask_helper.py / mails/send_mail.py が消費する libcommon:
  `language`・`locale`・`logger`・`color`・`validator`・`web.validation_errors`・
  `web.http_errors`・`web.http_successes`・`mail`。thinkx と異なり **discord は不使用**。
  flask_helper.py は対応言語をハードコード(`Config.AVAILABLE_LANGS` 不参照)。
- ピン submodule commit `ee96d6d…` は上記モジュールを v2.0.0 と同一に保持。

### import 時の外部依存(注入で遮断)
- `libcommon.locale` はホスト config を読む → conftest が `sys.modules['config']=config_test` を注入。
- `libcommon.mail.Mail()` が import 時に boto3 SES クライアント生成 → conftest で boto3 を MagicMock 化。
- mongo / redis / session は import 時に接続しない(config 注入 + boto3 mock のみで十分)。

### 環境
- S トラック共有 venv `<workspace>/.s-track-venv`(git 管理外)。版は thinkx/findings.md と同一
  (Flask 3.1.0 / Jinja2 3.1.6 / Werkzeug 3.1.8 / pydantic 2.10.4 / boto3 1.34.122 /
  requests 2.32.5 / python-dotenv 1.0.1 / pytest 8.3.4)。
- submodule はローカル libcommon clone からオフライン初期化
  (`protocol.file.allow=always` + `submodule.web-server/libcommon.url=<local>`)。

### ゴールデン
- `from main import app` 成功(test_app_imports)。
- GET ルート sweep 4件(`/`, `/<lang>`, `/<lang>/`, `/static/<path:filename>`)を
  `tests/golden/route_sweep.json` に凍結(test_route_sweep)。static は 404 を現状として記録。
- 実行(cwd 非依存・autoenv 回避のためワークスペース直下から):
  `.s-track-venv/bin/python -m pytest kazukiotsukacom/web-server/tests/test_app_imports.py \
   kazukiotsukacom/web-server/tests/test_route_sweep.py`

---

## S-3 kazukiotsukacom カットオーバー(2026-07-07・S-1+S-2 同型)

- `git submodule deinit -f web-server/libcommon` → `git rm -f web-server/libcommon` → `.gitmodules`
  は libcommon が唯一の submodule だったため空になり `git rm -f .gitmodules` で削除。
- `bash libcommon/scripts/bake.sh v2.0.0 kazukiotsukacom/web-server/` → 実物コピー + VERSION。
- VERSION tree_sha256 = `3359309a…cf0` = S-0a パラメータと一致(bake 出力 + `bash -c` 独立再算出の
  両方で MATCH。thinkx と同一 v2.0.0 ソースのためバイト同一)。
- `.gitignore` の無視は `__pycache__/*.pyc` のみ(bake hash 除外対象と一致)。実ソース129ファイル tracked、pyc 混入なし。
- 検証: `from main import app` green / ルートゴールデン(4件)不変 / 想定外差分なし
  ({D .gitmodules, D gitlink, A 129 実ファイル})。

### S-2 相当 デプロイ経路の submodule 依存検査
- `log.sh`(journalctl)/ `restart.sh`・`web-server/restart.sh`(systemctl restart uwsgi)のみ。
- `git grep -E 'submodule|recurse-submodules'`(libcommon・tests・findings 除外)= **0件**。
- CI 設定ファイル・playbooks・deploy.sh は**存在しない**。→ デプロイ経路の変更不要。

### 環境メモ(CLAUDE.md にも反映済み)
- `cd` はワークスペースの `.autoenv` により対話プロンプトで stdin をブロックし無人進行を止める。
  検証・hash 再算出は `git -C`、または cd を含む場合は `bash -c '...'`(zsh の autoenv フック回避)で行う。
