#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# sso.py (auth のコア blueprint)
#
# PROTOCOL.md v1 の実装。エンドポイント:
#   GET  /authorize           : 中央ログイン。既ログインなら即 auth_code 発行して redirect
#   POST /v1/token/exchange   : auth_code -> UserInfo + access_token (サーバ間)
#   GET  /v1/userinfo         : access_token -> UserInfo (サーバ間)
#   GET  /v1/users/<user_id>  : service 資格情報 -> UserInfo (サーバ間の再照会基本ルート)
#   GET  /v1/logout           : 中央セッション破棄
#
# 設計:
# - フロントチャネルに流すのは一回限りの auth_code だけ。UserInfo と access_token は
#   service_secret で認証されたバックチャネルだけで返す (PROTOCOL.md §1)。
# - auth_code は Redis で 60 秒 TTL・一回限り (GETDEL で原子的に消費)。
# - service (サイト) は Config.SSO_SERVICES に静的登録。redirect_uri は完全一致のみ許可。
# - JWT / refresh_token は protocol_version 2 の引き金 (PROTOCOL.md §7) 成立まで実装しない。

import secrets
import json
from urllib.parse import urlencode

from flask import Blueprint, request, redirect, render_template
from redis import StrictRedis
from redis.exceptions import ResponseError

# libcommon: 契約層 (レスポンス3型・セッション・デコレータ)
from libcommon.web.session import Session
from libcommon.web.flask_helpers import (
    language_wrapper, content_type_check_json, required_fields_check,
    validate_request,
)
from libcommon.web.http_response_formatter import SuccessFormat, SuccessCode
from libcommon.web.http_errors import (
    UnauthorizedAPIErrorFormat, ForbiddenAPIErrorFormat,
    BadRequestAPIErrorFormat, UnexpectedAPIErrorFormat,
)

from models.data.user import User, UserNotFoundError
from protocol import (
    PROTOCOL_VERSION, build_userinfo, with_exchange_token, with_protocol_version,
)

# Logger
from libcommon.logger import Logger
from libcommon.color import *
logger = Logger()
logger.setLevel(logger.DEBUG)

# Locale
from libcommon.locale import Locale
locale = Locale('sso.json')

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'DEFAULT_LANG',
    'SSO_SERVICES',            # { service_id: {'service_secret', 'redirect_uris', 'logout_uris'} }
    'REDIS_SESSION_HOST',
    'REDIS_SESSION_PORT',
    'SSO_REDIS_DB_NUMBER',     # auth_code / access_token 置き場 (セッション DB と分ける)
    'SSO_CODE_TTL_SEC',        # 60
    'SSO_ACCESS_TOKEN_TTL_SEC',  # 3600
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

blueprint_sso = Blueprint('sso', __name__)

_redis = StrictRedis(
    host=Config.REDIS_SESSION_HOST,
    port=Config.REDIS_SESSION_PORT,
    db=Config.SSO_REDIS_DB_NUMBER,
)

CODE_PREFIX = 'sso:auth_code:'
TOKEN_PREFIX = 'sso:access_token:'
SERVICE_ID_HEADER = 'X-Service-Id'          # /v1/users/<user_id> の資格情報 (PROTOCOL.md §4)
SERVICE_SECRET_HEADER = 'X-Service-Secret'


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _service_config(service_id):
    """登録済み service 設定を返す。未登録なら None。"""
    if not service_id:
        return None
    return Config.SSO_SERVICES.get(service_id)


def _issue_auth_code(user_id, service_id):
    """一回限りの認可コードを発行して Redis へ (TTL 付き)。"""
    auth_code = secrets.token_urlsafe(32)
    payload = json.dumps({'user_id': user_id, 'service_id': service_id})
    _redis.setex(CODE_PREFIX + auth_code, Config.SSO_CODE_TTL_SEC, payload)
    logger.info(cyan(f'SSO auth_code issued for user {user_id} service_id={service_id}'))
    return auth_code


def _consume_auth_code(auth_code):
    """auth_code を一回だけ読んで即無効化する。不正・期限切れ・使用済みは None。

    Redis 6.2+ の GETDEL で原子的に消費する。古い Redis では transaction pipeline に
    フォールバックする。
    """
    key = CODE_PREFIX + auth_code
    try:
        val = _redis.execute_command('GETDEL', key)
    except ResponseError as e:
        if 'unknown command' not in str(e).lower():
            raise
        pipe = _redis.pipeline(transaction=True)
        pipe.get(key)
        pipe.delete(key)
        val, _ = pipe.execute()

    if val is None:
        return None
    if isinstance(val, bytes):
        val = val.decode('utf-8')
    return json.loads(val)


def _issue_access_token(user_id, service_id):
    access_token = secrets.token_urlsafe(32)
    payload = json.dumps({'user_id': user_id, 'service_id': service_id})
    _redis.setex(TOKEN_PREFIX + access_token, Config.SSO_ACCESS_TOKEN_TTL_SEC, payload)
    return access_token


def _resolve_access_token(access_token):
    val = _redis.get(TOKEN_PREFIX + access_token)
    if val is None:
        return None
    if isinstance(val, bytes):
        val = val.decode('utf-8')
    return json.loads(val)


def _verify_service_secret(service_id, service_secret, lang):
    """service 資格情報の検証。(service_config, error_response) を返す。

    secret 比較は secrets.compare_digest でタイミング攻撃を避ける。
    """
    service_config = _service_config(service_id)
    if service_config is None:
        logger.info(yellow(f'unknown service_id: {service_id}'))
        error = ForbiddenAPIErrorFormat(lang=lang, field_name='service_id')
        return None, with_protocol_version(error).http_response()
    expected = service_config.get('service_secret') or ''
    if not secrets.compare_digest(service_secret or '', expected):
        logger.info(red(f'bad service_secret for service_id={service_id}'))
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='service_secret')
        return None, with_protocol_version(error).http_response()
    return service_config, None


def _userinfo_response(user, lang, extra=None):
    """UserInfo を SuccessFormat (フラット data + code + message) で返す。"""
    data = build_userinfo(user)
    if extra:
        data.update(extra)
    return SuccessFormat(
        data=data,
        code=SuccessCode.OK,
        message=locale.get('ok', lang),
    ).http_response()


# ----------------------------------------------------------------------
# GET /authorize  (ブラウザ向け・フロントチャネル)
# ----------------------------------------------------------------------
@blueprint_sso.route('/authorize', methods=['GET'])
@blueprint_sso.route('/<lang>/authorize', methods=['GET'])
@language_wrapper
def authorize(lang, lang_name):
    service_id = request.args.get('service_id', '')
    redirect_uri = request.args.get('redirect_uri', '')
    state = request.args.get('state', '')

    service_config = _service_config(service_id)

    # service / redirect_uri / state の検証。
    # NOTE: 不正な redirect_uri へは絶対に redirect しない (オープンリダイレクト防止)。
    #       エラーは auth 自身の画面で表示する。
    if service_config is None:
        logger.info(yellow(f'authorize: unknown service_id: {service_id}'))
        return render_template('sso_error.html', lang=lang,
                               message=locale.get('unknown_service', lang)), 403
    if redirect_uri not in service_config.get('redirect_uris', []):
        logger.info(yellow(f'authorize: redirect_uri not registered: {redirect_uri}'))
        return render_template('sso_error.html', lang=lang,
                               message=locale.get('invalid_redirect_uri', lang)), 400
    if not state:
        return render_template('sso_error.html', lang=lang,
                               message=locale.get('state_required', lang)), 400

    # 既ログイン -> 利用エントリを保証して即 auth_code 発行 (Google と同じ挙動)
    user_id = Session.user_id()
    if user_id:
        try:
            user = User.find_user_by_id(str(user_id))
        except UserNotFoundError:
            # セッションはあるがユーザーが消えている (異常系)。セッションを破棄してログインへ
            logger.error(red(f'authorize: session user not found: {user_id}'))
            Session.clear()
        else:
            user.ensure_service(service_id)
            auth_code = _issue_auth_code(str(user.id), service_id)
            query = urlencode({'auth_code': auth_code, 'state': state})
            return redirect(f'{redirect_uri}?{query}')

    # 未ログイン -> 中央ログイン画面。成功後フロントが同じ /authorize へ戻る
    return render_template(
        'signin.html',
        lang=lang, lang_name=lang_name,
        service_id=service_id, redirect_uri=redirect_uri, state=state,
    )


# ----------------------------------------------------------------------
# POST /v1/token/exchange  (サーバ間・バックチャネル)
# ----------------------------------------------------------------------
@blueprint_sso.route('/v1/token/exchange', methods=['POST'])
@blueprint_sso.route('/v1/<lang>/token/exchange', methods=['POST'])
@language_wrapper
@content_type_check_json
@required_fields_check(['auth_code', 'service_id', 'service_secret'])
def token_exchange(lang, lang_name):
    validation_error = validate_request(lang, locale)
    if validation_error:
        # バリデーションエラーは libcommon 全体共通の errors 配列型 (全アプリ共有契約) を
        # そのまま使う。protocol_version を焼くのは単体エラー (APIErrorFormat 系) のみ (PROTOCOL.md §5)
        return validation_error.http_response()

    auth_code = request.json.get('auth_code')
    service_id = request.json.get('service_id')
    service_secret = request.json.get('service_secret')

    _service_config_value, error_response = _verify_service_secret(service_id, service_secret, lang)
    if error_response:
        return error_response

    # auth_code 消費 (一回限り)。発行先 service と交換元 service の一致も検査する
    payload = _consume_auth_code(auth_code)
    if payload is None or payload.get('service_id') != service_id:
        logger.info(yellow(f'token_exchange: invalid/expired/used auth_code (service_id={service_id})'))
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='auth_code')
        return with_protocol_version(error).http_response()

    try:
        user = User.find_user_by_id(payload['user_id'])
    except UserNotFoundError:
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='user_id')
        return with_protocol_version(error).http_response()
    except Exception as e:
        logger.error(red(f'token_exchange: unexpected: {e}'))
        error = UnexpectedAPIErrorFormat(lang=lang)
        return with_protocol_version(error).http_response()

    access_token = _issue_access_token(str(user.id), service_id)
    logger.info(green(f'token_exchange OK user_id={user.id} service_id={service_id}'))
    return _userinfo_response(user, lang, extra={
        'access_token': access_token,
        'expires_in': int(Config.SSO_ACCESS_TOKEN_TTL_SEC),
    })


# ----------------------------------------------------------------------
# GET /v1/userinfo  (サーバ間・バックチャネル)
# ----------------------------------------------------------------------
@blueprint_sso.route('/v1/userinfo', methods=['GET'])
@blueprint_sso.route('/v1/<lang>/userinfo', methods=['GET'])
@language_wrapper
def userinfo(lang, lang_name):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='access_token')
        return with_protocol_version(error).http_response()

    payload = _resolve_access_token(auth_header[len('Bearer '):])
    if payload is None:
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='access_token')
        return with_protocol_version(error).http_response()

    try:
        user = User.find_user_by_id(payload['user_id'])
    except UserNotFoundError:
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='user_id')
        return with_protocol_version(error).http_response()

    return _userinfo_response(user, lang)


# ----------------------------------------------------------------------
# GET /v1/users/<user_id>  (サーバ間・バックチャネル。再照会の基本ルート)
# ----------------------------------------------------------------------
@blueprint_sso.route('/v1/users/<user_id>', methods=['GET'])
@blueprint_sso.route('/v1/<lang>/users/<user_id>', methods=['GET'])
@language_wrapper
def users_get(lang, lang_name, user_id):
    service_id = request.headers.get(SERVICE_ID_HEADER, '')
    service_secret = request.headers.get(SERVICE_SECRET_HEADER, '')
    if not service_id or not service_secret:
        error = BadRequestAPIErrorFormat(
            lang=lang, field_name='service_id',
            message=f'{SERVICE_ID_HEADER} and {SERVICE_SECRET_HEADER} headers are required')
        return with_protocol_version(error).http_response()

    _service_config_value, error_response = _verify_service_secret(service_id, service_secret, lang)
    if error_response:
        return error_response

    try:
        user = User.find_user_by_id(user_id)
    except UserNotFoundError:
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='user_id')
        return with_protocol_version(error).http_response()

    logger.info(cyan(f'users_get OK user_id={user_id} service_id={service_id}'))
    return _userinfo_response(user, lang)


# ----------------------------------------------------------------------
# GET /v1/logout  (ブラウザ向け・フロントチャネル)
# ----------------------------------------------------------------------
@blueprint_sso.route('/v1/logout', methods=['GET'])
@blueprint_sso.route('/v1/<lang>/logout', methods=['GET'])
@language_wrapper
def logout(lang, lang_name):
    Session.clear()
    redirect_uri = request.args.get('redirect_uri', '')
    # 登録済み logout_uri のみ許可。未指定・不一致は auth のトップへ
    for service_config in Config.SSO_SERVICES.values():
        if redirect_uri in service_config.get('logout_uris', []):
            return redirect(redirect_uri)
    return redirect('/')
