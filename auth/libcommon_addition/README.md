# libcommon_addition

`auth_client.py` は libcommon への追加モジュール (PLAN_libcommon_simplicity.md A-1)。
auth 自身は使わない — 使うのは各サイト (quantz-web 等) 側。

配置手順: Phase 2 (libcommon 計画) 完了後に libcommon/web/auth_client.py として追加し、
Phase 5 で各サイトへ vendoring される。それまでこのフォルダはドラフト置き場。
