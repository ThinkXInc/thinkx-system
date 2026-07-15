# kazukiotsukacom 開発規約

- 本サイトは libcommon の[凍結]面(logger/color/validator/locale/language/
  レスポンスフォーマット族/mail 等)のみを消費する。flask_helpers / session は使わない。
- web-server/libcommon は vendoring された実物コピー(VERSION 参照)。**編集禁止**。
  修正は libcommon 原本で行い、bake.sh で焼き直す。
- 検証: pytest(スモーク+ルートゴールデン)。libcommon を焼き直したら必ず実行する。
- config.py + .env が設定の正。libcommon の各モジュールはホストの config を読む(現行仕様)。
