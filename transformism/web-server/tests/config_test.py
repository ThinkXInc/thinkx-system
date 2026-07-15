# web-server/tests/config_test.py
#
# S2-3 テスト用 Config(thinkx S-0b と同型)。main.py の import 連鎖
# (init_flask_app / flask_helper / mails.send_mail / vendored libcommon の
#  logger・locale・mail 等)が起動時に check_config / 直接アクセスで要求する
# 全キーを明示列挙する。実値は不要、形式が通ればよい。
#
# 本番の config.py は編集しない。conftest が `sys.modules['config'] = config_test`
# で差し込む(src 変更ゼロ)。
#
# thinkx config_test との差分(F-S2-13):
#   - Discord webhook キーは不要(transformism の import 連鎖は Discord を参照しない)。
#   - AVAILABLE_LANGS は不要(flask_helper は Language.lang_label_map(only=[...]) の
#     ハードコード list を使い、Config.AVAILABLE_LANGS を読まない)。
#   - LOCALES_ROOT は本番同様サイトの web-server/locales を指す(main.py:38 と
#     send_mail が error_pages.json / page_metadata.json / emails.json を import 時に読む)。

import os

_LOCALES_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'locales')


class Config:
    # 起動時 check_config が要求(main / flask_helper / init_flask_app / send_mail)
    ENV = 'test'
    DEFAULT_LANG = 'en'
    FLASK_APP_SECRET_KEY = 'test-flask-app-secret-key'
    HOST_URL = 'http://localhost'
    LOCALES_ROOT = _LOCALES_ROOT

    # メール送信(SES / libcommon.mail)。send_mail の check_config が要求。
    MAIL_SENDER = 'ThinkX Inc. <noreply@example.com>'
    MAIL_REPLY_TO = 'support@example.com'
    AWS_ACCESS_KEY_ID = 'test-access-key-id'
    AWS_SECRET_ACCESS_KEY = 'test-secret-access-key'
    AWS_DEFAULT_REGION = 'us-east-1'


class MissingKeyError(Exception):
    """本番 config.check_config と同契約。"""
    pass


def check_config(config, required_keys):
    """欠落 or None のキーがあれば MissingKeyError。config_test では全て通る想定。"""
    missing_or_none_keys = [
        key for key in required_keys
        if not hasattr(config, key) or getattr(config, key) is None
    ]
    if missing_or_none_keys:
        raise MissingKeyError(
            f"Missing or None configuration keys: {', '.join(missing_or_none_keys)}"
        )
