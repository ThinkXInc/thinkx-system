# transformism 開発規約

thinkx / kazukiotsukacom と同じ層構造の静的サイト。libcommon を vendoring で消費する。
（S2 トラックで submodule → vendoring へ移行。実測は findings.md 参照。）

## libcommon 消費(vendoring)

- 本サイトは libcommon の[凍結]面(logger / color / validator / locale / language /
  レスポンスフォーマット族(web.http_errors / web.http_successes / web.validation_errors)/
  mail 等)のみを消費する。libcommon の flask_helpers / session は使わない。
  - 注: 本サイトの `web-server/flask_helper.py` は**サイト独自ファイル**であり、
    libcommon の凍結面(language / locale / validator / logger / color)のみを利用する。
    libcommon 内の `web/flask_helpers.py` とは別物。混同しないこと。
- `web-server/libcommon` は vendoring された実物コピー(`web-server/libcommon/VERSION` 参照。
  現在 v2.1.0 / tree_sha256 `ab534a69…`。thinkx / kazukiotsukacom と byte 一致)。**編集禁止**。
  修正は libcommon 原本で行い、`libcommon/scripts/bake.sh <tag> transformism/web-server/` で
  焼き直す。焼き直したら必ず検証(下記)を実行する。
- `.gitmodules` に libcommon は無い(submodule から vendoring へ移行済み)。
  `www/playbooks` submodule は別途存在し、**本トラックの対象外・不触**。

## 設定

- `config.py` + `.env` が設定の正。libcommon の各モジュールはホストの `config`(Config)を
  読む(現行仕様)。`ENV`(develop / production)未指定だと `config.EnvironmentNotSpecified`。

## 検証(スモーク + ルートゴールデン)

- ハーネス: `web-server/tests/`(conftest / config_test / golden_utils /
  test_route_sweep / test_app_imports。thinkx と同型)。
  ゴールデン: `web-server/tests/golden/route_sweep.json`。
- **実行前提3点(重要)**:
  1. **cwd=web-server** で実行する(conftest が chdir する)。でないと libcommon は
     名前空間パッケージのため workspace-root の**原本 libcommon を誤ロード**する。
  2. libcommon は `__init__.py` を持たない**名前空間パッケージ**。どの libcommon が
     解決されたかは submodule の `__file__` で判定する(`find_spec().origin` は None)。
  3. libcommon.logger が host `config` を import するため、`ENV` を与える
     conftest / config_test が要る(本番 config.py は編集せず `sys.modules['config']` 注入)。
- 実行コマンド(例):
  `<venv>/bin/python -m pytest web-server/tests/test_app_imports.py web-server/tests/test_route_sweep.py -v`
- **libcommon を焼き直したら必ずこの pytest を実行し、ルートゴールデン不変を確認する。**
  ゴールデン不一致は黙って再生成せず、findings.md に記録して停止(人間判断)。

## ビルド / 起動

- 実行は `web-server/` を cwd に。本番は uwsgi。
- `main.py` の `if __name__ == '__main__'` ブロックは `app.run(secret_key=…,
  max_content_length=…)` と**無効な kwargs** を渡すため、**`python main.py` では直接起動しない**
  (pre-existing WIP。本トラックでは不修正 — 是正は Phase 3 型仕分け)。
  ローカル確認は `app` を import して `app.run(host, port)` する。

## ルート面(重要・誤解防止)

- **現状の能動ルートは `/`(top_handler)のみ。** 加えて errorhandler 400 / 404 / 500 / 502、
  Flask 既定の `/static/<path:filename>`(404)。ルートゴールデンは `/`→200、`/static`→404 の 2 件。
- **`/<lang>/` を含む他のルートハンドラは、本番未投入の WIP として `main.py` 内で
  コメントアウトされている**(F-S2-14。本番 https://transformism.art/ が単一ページ構成で
  あることを実サイト照合済み。ナビはページ内アンカー、外部リンクは store.transformism.art のみ)。
  → **これらのコメントアウト群を「誤って消されたコード」と誤解して勝手に復活させないこと。**
  復活は本番投入の意思決定(人間)を伴う別作業である。
- 多言語(locale 依存)ルートは現状 **0 件**。

## メール(SES)

- `web-server/mails/send_mail.py` は import 時に SES クライアント(libcommon.mail.Mail)を
  構築するが、`TEST_SEND=False` により実送信はしない。
  **実 SES 送信の検証はステージング(インフラ I-STEP2 以降)で行う**。
