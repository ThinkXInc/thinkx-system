#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# main.py (auth)
#
# 全サービス共通アカウントシステム。apps の一つとして quantz-web/thinkx と同じ形で立つ。
# nginx-root が auth ドメインをこの uWSGI に流す (conf.d/auth_web.conf)。
#
# 構成 (quantz-web/web-server と同型):
#   main.py            <- app 組み立て + healthcheck
#   sso.py             <- コア: /authorize, /v1/token/exchange, /v1/userinfo,
#                         /v1/users/<user_id>, /v1/logout
#   accounts.py        <- 中央ログイン/登録の API
#   protocol.py        <- UserInfo JSON を組み立てる唯一の場所 (PROTOCOL.md の実装)
#   models/data/user.py
#   views/             <- signin.html / signup.html / sso_error.html
#   locales/           <- sso.json, accounts.json

from flask import Flask

import init_mongodb  # noqa: F401  # import 時に MongoDB へ接続する (テストは事前に monkeypatch)

from libcommon.web.session import RedisSessionInterface, Session
from libcommon.web.flask_helpers import configure_flask_helpers

from sso import blueprint_sso
from accounts import blueprint_accounts

# Logger
from libcommon.logger import Logger
from libcommon.color import *
logger = Logger()
logger.setLevel(logger.DEBUG)

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'ENV',
    'SESSION_COOKIE_NAME',
    # L-1 追随: 従来 libcommon が自分で読んでいた config 値を app 起動時に注入する。
    'DEFAULT_LANG',
    'AVAILABLE_LANGS',
    'BASIC_AUTH_USERNAME',
    'BASIC_AUTH_PASSWORD',
    'REDIS_SESSION_HOST',
    'REDIS_SESSION_PORT',
    'REDIS_SESSION_DB_NUMBER',
    'REDIS_SESSION_EXPIRATION_TIME_SEC',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

# L-1 追随 (quantz-web Q-4 と同型): libcommon の新初期化 API へ配線。
# pre-v2.0.0 では flask_helpers.py が `from config import Config` / `from models.data.user import ...`
# でホストへ逆依存していた。v2.0.0 はこれらを注入 API に置き換えた。app 起動時に config 値を注入する。
Session.configure(
    Config.REDIS_SESSION_HOST, Config.REDIS_SESSION_PORT, Config.REDIS_SESSION_DB_NUMBER)
configure_flask_helpers(
    Config.DEFAULT_LANG, Config.AVAILABLE_LANGS,
    Config.BASIC_AUTH_USERNAME, Config.BASIC_AUTH_PASSWORD)


app = Flask(__name__, template_folder='views')
app.config['SESSION_COOKIE_NAME'] = Config.SESSION_COOKIE_NAME  # 'thinkx_auth_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = Config.ENV != 'development'
app.session_interface = RedisSessionInterface(
    Config.REDIS_SESSION_HOST, Config.REDIS_SESSION_PORT,
    Config.REDIS_SESSION_DB_NUMBER, Config.REDIS_SESSION_EXPIRATION_TIME_SEC,
    prefix='auth_session:')

app.register_blueprint(blueprint_sso)
app.register_blueprint(blueprint_accounts)

logger.info(green('auth service initialized.'))


@app.route('/healthcheck')
def healthcheck():
    return 'OK', 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8020, debug=(Config.ENV == 'development'))
