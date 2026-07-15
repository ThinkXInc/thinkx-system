# thinkx findings(S トラック / Phase 2.5)

規範: `thinkx/refactor_plan.md`(静的サイト群 vendoring カットオーバー計画 v1.1)。
本ファイルは thinkx リポジトリ直下(計画 大原則3)。Security exception は即停止・報告(D-22)。

---

## S-0a 前提ゲート(2026-07-07 実測・確認のみ)

- `git -C libcommon tag -l v2.0.0` → `v2.0.0`(存在)。
- `libcommon/scripts/bake.sh` 存在。
- tree_sha256 再算出一致: `bash bake.sh v2.0.0 <tmp>` → `3359309a30a392a75a97b3fad594569487cb07068f770877202de3096fb57cf0`
  = 計画パラメータ(Q-6 実測値)と完全一致。
- libcommon ゲート: `ruff check .` = All checks passed / `pyright` = 0 errors(5 warnings: TypeVar 用法・新版通知のみ)。
- settings.json スコープ切替: 人間が適用済み(deny を各サイト `web-server/libcommon/**` のみへ限定)。

### F-S1(記録・別トラック): libcommon の bare `pytest` は緑でない
- `.venv/bin/pytest`(引数なし)で collection error 3件:
  - `tests/modelbase_test.py` / `tests/mongobase_test.py` → `ModuleNotFoundError: No module named 'nose'`
  - `vector_database/test_vector_database.py` → `ModuleNotFoundError: No module named 'torch'`
- いずれもリファクタ対象外の旧世代テストモジュール(消えた optional 依存 nose/torch を import)。
  libcommon 計画の setup が入れる依存は `pytest fakeredis flask pydantic …` のみで nose/torch を含まない。
- 判断: v2.0.0 デリバラブルの健全性は tag + tree_sha256 一致で機械証明済み。サイトが消費する
  [凍結]面(logger/color/validator/locale/language/web.http_errors・http_successes・
  validation_errors/mail/discord)とも無関係。**別トラック(libcommon)の遺物テスト債務**であり
  Phase 2.5 の前提充足を妨げないと判断して S-0b へ進行。libcommon 側で解消すべき事項として記録。

---

## S-0b スモークハーネス(2026-07-07)

### 消費面の実測(計画 大原則2 の裏取り)
- thinkx main.py / flask_helper.py / mails/send_mail.py が消費する libcommon:
  `discord`(send_discord)・`language`・`locale`・`logger`・`color`・`validator`・
  `web.validation_errors`・`web.http_errors`・`web.http_successes`・`mail`。
  flask_helpers / session は不使用(計画通り [凍結]面のみ)。
- ピン submodule commit `7b15ee6…`(thinkx)は上記モジュールを v2.0.0 と同一に保持
  (pinned には削除予定の deprecated: `web/[DEPRECATE]api_errors.py` `web/api_response_v1.py`
  `web/errors_v1.py` が余分に在るが、サイトは import しない)。→ S-1 カットオーバーでゴールデン
  不変になるはず。

### import 時の外部依存(注入で遮断)
- `libcommon.locale` は `from config import Config`(ホスト config を読む現行仕様)→
  conftest が `sys.modules['config'] = config_test` を main import 前に注入して解決。
- `libcommon.mail.Mail()` は mails/send_mail.py の import 時に生成され `boto3.client('ses')` を
  呼ぶ → conftest で boto3.client/resource を MagicMock 化(実 AWS I/O 遮断)。
- 本サイトは mongo / redis / session を import 時に接続しない(quantz Q-1 の mongomock/fakeredis
  差し込みは不要)。→ conftest は config 注入 + boto3 mock のみ。

### 環境(計画に venv 項目が無いため実行者が決定・記録)
- S トラック専用 venv: `<workspace>/.s-track-venv`(ワークスペース直下=git 管理外)。
- 版は libcommon v2.0.0 の検証環境 `.venv` に合わせる: Flask 3.1.0 / Jinja2 3.1.6 /
  Werkzeug 3.1.8 / pydantic 2.10.4。加えて boto3 1.34.122(mail)/ requests 2.32.5(discord)/
  python-dotenv 1.0.1 / pytest 8.3.4。
  - 注: サイト requirements.txt は Flask 0.12.2 の旧ピンだが py3.10 で導入困難かつ本計画は
    「同一 env で S-0b 取得・S-1 検証」すればスワップ回帰オラクルとして妥当なため、v2.0.0 検証環境に
    揃えた。本番デプロイ版の整合は Phase 2.5 の範囲外(サイト無変更)。
- submodule はローカル libcommon clone からオフライン初期化:
  `git -C thinkx -c protocol.file.allow=always -c submodule.web-server/libcommon.url=<local> \
   submodule update --init web-server/libcommon`(ネット/ssh 不要)。playbooks submodule は触らない。

### ゴールデン
- `from main import app` 成功(test_app_imports)。
- GET ルート sweep 56件を `tests/golden/route_sweep.json` に凍結(test_route_sweep)。
  200/302/404/500 を現状のまま記録(500 は test env でのロケール/動的コンテンツ欠落による現行挙動。
  回帰オラクルとして凍結、S-1 で不変を要求)。truetechjapan / nntm アセットサイトのルートを含む。
- 実行: `.s-track-venv/bin/python -m pytest tests/test_app_imports.py tests/test_route_sweep.py`

---

## S-1 thinkx カットオーバー(2026-07-07)

- `git submodule deinit -f web-server/libcommon` → `git rm -f web-server/libcommon`
  (gitlink 除去 + .gitmodules から libcommon 節削除。**playbooks 節は残存**)。
- `bash libcommon/scripts/bake.sh v2.0.0 thinkx/web-server/` → 実物コピー + VERSION 生成。
- VERSION tree_sha256 = `3359309a…cf0` = S-0a パラメータと一致(bake 出力 + 独立再算出
  `find -not __pycache__ -not *.pyc -not VERSION | sort | xargs shasum | shasum` の両方で MATCH)。
- 焼き込んだ `libcommon/.gitignore` が無視するのは `__pycache__/*.pyc`(pytest が生成した一時物)のみ
  = bake の hash 除外対象と一致。実ソース129ファイルは全て tracked(pyc 混入なし)。
- 検証: `from main import app` green / ルートゴールデン(56件)不変 / git status は
  {M .gitmodules, D gitlink, A 129 実ファイル} のみで想定外差分なし。

## S-2 thinkx デプロイ経路の submodule 依存検査(2026-07-07)

- 検査対象: `deploy.sh` / thinkx 直下スクリプト / CI 設定 / 追跡ファイル全体
  (`git grep -E 'submodule|recurse-submodules'`、web-server/libcommon と本計画 docs は除外)。
- 結果: **libcommon 由来の `git submodule update` / `--recurse-submodules` は0件**。
  - `deploy.sh` は `ansible-playbook -i playbooks/thinkx playbooks/thinkx.yml` のみ(submodule 取得なし)。
  - CI 設定ファイルは未追跡(`.github/` 等なし)。
  - `.gitmodules` に残るのは playbooks 節のみ(意図通り)。libcommon 分は S-1 で除去済みのため
    将来の `submodule update` でも libcommon は取得されない。
- **人間確認事項(F-S2)**: `playbooks` submodule(commit `38bf25a…`・別リポ・本計画対象外)は
  未初期化 + ネットワーク遮断のためオフライン検査不可。playbooks 内に旧 `web-server/libcommon`
  submodule パスへの参照や `git submodule update --recurse` があれば、その libcommon 取得ステップは
  不要になっている(playbooks 自体の取得は残す)。playbooks 原本での確認は人間判断。
- deploy 経路コードの変更は無し(計画 S-2「変更があった場合のみコミット」に該当せず。本記録のみ)。
