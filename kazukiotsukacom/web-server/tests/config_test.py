# web-server/tests/config_test.py
#
# S-0b テスト用 Config(quantz Q-1 と同型)。main.py の import 連鎖
# (init_flask_app / flask_helper / mails.send_mail / submodule libcommon の
#  logger・locale・mail 等)が起動時に check_config / 直接アクセスで要求する
# 全キーを明示列挙する。実値は不要、形式が通ればよい(計画 S-0b)。
#
# 本番の config.py は編集しない。conftest が `sys.modules['config'] = config_test`
# で差し込む(src 変更ゼロ)。catch-all は置かない — optional キー
# (logger.py の LOGGER_FORMAT_* など getattr デフォルトを持つもの)を不在にして
# 正しくデフォルトを効かせる。欠落は MissingKeyError / AttributeError で顕在化し反復で補う。
#
# 注: kazuki の flask_helper.py は対応言語をハードコードしており(Config.AVAILABLE_LANGS 不参照)、
# main.py は discord を import しないため、AVAILABLE_LANGS / DISCORD_* キーは不要。

import os

_LOCALES_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'locales')


class Config:
    ENV = 'test'
    DEFAULT_LANG = 'en'
    LOCALES_ROOT = _LOCALES_ROOT
    HOST_URL = 'http://localhost'
    FLASK_APP_SECRET_KEY = 'test-flask-app-secret-key'

    # メール送信(SES / libcommon.mail)
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
