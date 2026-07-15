#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# libcommon/web/auth_client.py  (libcommon への追加モジュール)
#
# 各サイトが auth と話すための薄いクライアント。PROTOCOL.md v1 に対応。
# サイト側はこのモジュール経由でのみ auth と通信する。
#
# 設計上の要点:
# - この層は「通信の約束」だけを持ち、滅多に変えない。libcommon 本体のバージョンが
#   サイトごとにずれても、この部分が同じである限り全サイトが auth と話せる。
#   変更が必要になるのは protocol_version 2 導入時のみ。
# - config の読み方は libcommon 全体の現行規約 (from config import Config) に従う。
#   注入方式への変更は libcommon リファクタ全体の論点であり、このモジュールが単独で
#   先行しない (auth リポジトリの CLAUDE.md 参照)。
#
# 使い方 (サイト側):
#   1) config.py に AUTH_BASE_URL / AUTH_SERVICE_ID / AUTH_SERVICE_SECRET /
#      AUTH_CALLBACK_URL を置く
#   2) ログイン開始:  redirect(AuthClient.authorize_url(lang))
#   3) callback:      userinfo = AuthClient.exchange_auth_code(auth_code)
#                     Session.start(userinfo['user_id'])
#                     redirect(AuthClient.pop_return_to())
#   4) 保護:          @auth_login_required を GET ハンドラに積む
#      (積む位置: @language_wrapper の直後。Session を読み、lang を使うため)

import secrets
from urllib.parse import urlencode
from functools import wraps

import requests
from flask import request, redirect, session

from config import Config, check_config

from libcommon.web.session import Session

# Logger
from libcommon.logger import Logger
from libcommon.color import *
logger = Logger()
logger.setLevel(logger.INFO)

REQUIRED_KEYS_IN_CONFIG = [
    'AUTH_BASE_URL',         # 例: 'https://auth.thinkx.com'
    'AUTH_SERVICE_ID',       # 例: 'quantz'
    'AUTH_SERVICE_SECRET',
    'AUTH_CALLBACK_URL',     # 例: 'https://quantz.example.com/auth/callback'
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

EXPECTED_PROTOCOL_VERSION = 1
STATE_SESSION_KEY = 'auth_state'
RETURN_TO_SESSION_KEY = 'auth_return_to'
SERVICE_ID_HEADER = 'X-Service-Id'
SERVICE_SECRET_HEADER = 'X-Service-Secret'
TIMEOUT_SEC = 5


class AuthClientError(Exception):
    """auth との通信・検証の失敗の基底。"""
    pass

class ProtocolMismatchError(AuthClientError):
    """受信した protocol_version が期待値と異なる。UserInfo を信用してはならない。"""
    pass

class AuthCodeExchangeError(AuthClientError):
    """auth_code -> UserInfo の交換に失敗 (期限切れ・使用済み・secret 不一致等)。"""
    pass


class AuthClient:

    # ------------------------------------------------------------------
    @classmethod
    def authorize_url(cls, lang=None, return_to=None):
        """ログイン開始 URL を作る。state を生成してサイトの session に保存する。

        return_to: ログイン完了後に戻したい自サイト内のパス。callback 側で
        pop_return_to() で取り出す。
        """
        state = secrets.token_urlsafe(16)
        session[STATE_SESSION_KEY] = state
        if return_to:
            session[RETURN_TO_SESSION_KEY] = return_to
        query = urlencode({
            'service_id': Config.AUTH_SERVICE_ID,
            'redirect_uri': Config.AUTH_CALLBACK_URL,
            'state': state,
        })
        base = Config.AUTH_BASE_URL.rstrip('/')
        path = f'/{lang}/authorize' if lang else '/authorize'
        return f'{base}{path}?{query}'

    # ------------------------------------------------------------------
    @classmethod
    def verify_state(cls):
        """callback 到着時の state 照合 (CSRF 防止)。一致したら消費する。"""
        expected = session.pop(STATE_SESSION_KEY, None)
        received = request.args.get('state')
        ok = bool(expected) and secrets.compare_digest(expected, received or '')
        if not ok:
            logger.info(yellow('auth callback: state mismatch.'))
        return ok

    # ------------------------------------------------------------------
    @classmethod
    def pop_return_to(cls, default='/'):
        """ログイン完了後の戻り先 (自サイト内パスのみ) を取り出す。"""
        return_to = session.pop(RETURN_TO_SESSION_KEY, None)
        # 自サイト内の絶対パスのみ許可 (外部 URL への横流しを防ぐ)
        if not return_to or not return_to.startswith('/') or return_to.startswith('//'):
            return default
        return return_to

    # ------------------------------------------------------------------
    @classmethod
    def exchange_auth_code(cls, auth_code):
        """auth_code -> UserInfo (PROTOCOL.md §2 手順4〜5)。

        Returns: UserInfo dict (user_id, email, email_verified, services, access_token, ...)
        Raises: AuthCodeExchangeError, ProtocolMismatchError
        """
        url = Config.AUTH_BASE_URL.rstrip('/') + '/v1/token/exchange'
        try:
            res = requests.post(url, json={
                'auth_code': auth_code,
                'service_id': Config.AUTH_SERVICE_ID,
                'service_secret': Config.AUTH_SERVICE_SECRET,
            }, timeout=TIMEOUT_SEC)
        except requests.RequestException as e:
            logger.error(red(f'auth exchange: request failed: {e}'))
            raise AuthCodeExchangeError(str(e))

        body = res.json()
        if res.status_code != 200:
            logger.info(yellow(f'auth exchange: {res.status_code} {body.get("reason")}'))
            raise AuthCodeExchangeError(body.get('reason', 'exchange_failed'))

        cls._check_protocol(body)
        return body

    # ------------------------------------------------------------------
    @classmethod
    def get_userinfo(cls, access_token):
        """access_token -> 最新 UserInfo (PROTOCOL.md §4)。token の TTL 内のみ。"""
        url = Config.AUTH_BASE_URL.rstrip('/') + '/v1/userinfo'
        try:
            res = requests.get(url, headers={
                'Authorization': f'Bearer {access_token}',
            }, timeout=TIMEOUT_SEC)
        except requests.RequestException as e:
            raise AuthClientError(str(e))

        body = res.json()
        if res.status_code != 200:
            raise AuthClientError(body.get('reason', 'userinfo_failed'))

        cls._check_protocol(body)
        return body

    # ------------------------------------------------------------------
    @classmethod
    def get_user_by_id(cls, user_id):
        """user_id -> 最新 UserInfo (サーバ間の再照会基本ルート。PROTOCOL.md §2 手順7)。

        決済直後の課金状態の取り直し等に使う。通常のページ表示ごとには呼ばない。
        """
        url = Config.AUTH_BASE_URL.rstrip('/') + f'/v1/users/{user_id}'
        try:
            res = requests.get(url, headers={
                SERVICE_ID_HEADER: Config.AUTH_SERVICE_ID,
                SERVICE_SECRET_HEADER: Config.AUTH_SERVICE_SECRET,
            }, timeout=TIMEOUT_SEC)
        except requests.RequestException as e:
            raise AuthClientError(str(e))

        body = res.json()
        if res.status_code != 200:
            raise AuthClientError(body.get('reason', 'users_get_failed'))

        cls._check_protocol(body)
        return body

    # ------------------------------------------------------------------
    @classmethod
    def _check_protocol(cls, body):
        if body.get('protocol_version') != EXPECTED_PROTOCOL_VERSION:
            logger.error(red(
                f'auth protocol mismatch: expected {EXPECTED_PROTOCOL_VERSION}, '
                f'got {body.get("protocol_version")}'))
            raise ProtocolMismatchError(str(body.get('protocol_version')))


# ----------------------------------------------------------------------
# ページ保護デコレータ
# ----------------------------------------------------------------------
def auth_login_required(f):
    """未ログインなら auth の /authorize へ redirect する (ページ GET 用)。

    積む位置: @language_wrapper の直後 (lang を受け取って authorize_url に渡すため)。

        @blueprint.route('/mypage')
        @blueprint.route('/<lang>/mypage')
        @language_wrapper
        @auth_login_required
        def mypage(lang, lang_name): ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not Session.user_id():
            lang = kwargs.get('lang')
            logger.info(cyan(f'not signed in -> redirect to auth: {request.path}'))
            return redirect(AuthClient.authorize_url(lang=lang, return_to=request.path))
        return f(*args, **kwargs)
    return decorated
