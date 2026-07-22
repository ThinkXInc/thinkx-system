#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# accounts.py (auth)
#
# 中央ログイン/登録の API。quantz-web/accounts.py のデコレータ積層をそのまま踏襲。
# /authorize が未ログイン時に signin.html を表示し、そのフォームがここへ POST する。
# 成功すると auth の中央セッションを開始する。サイト側のローカルセッションは、
# その後 /v1/token/exchange の結果を受けた各サイトが自分で開始する。

from datetime import datetime

from flask import Blueprint, request
import pytz

from libcommon.web.session import Session
from libcommon.web.flask_helpers import (
    language_wrapper, content_type_check_json, required_fields_check,
    regex_check, validate_request,
)
from libcommon.web.regex_patterns import (
    EMAIL_REGEX, PASSWORD_AT_LEAST_ONE_UPPER_AND_NUMERIC_REGEX,
)
from libcommon.web.http_response_formatter import SuccessFormat, SuccessCode
from libcommon.web.http_errors import (
    UnexpectedAPIErrorFormat, ResourceNotFoundAPIErrorFormat,
    IncorrectPasswordAPIErrorFormat, UserAlreadyExistsErrorFormat,
    UnauthorizedAPIErrorFormat, ForbiddenAPIErrorFormat,
)
from libcommon.web.google_oauth_helper import (
    verify_token, InvalidTokenError, WrongIssuerError,
    ClientIDMismatchError, TokenExpiredError, EmailNotVerifiedError,
)

from models.data.user import (
    UnauthorizedAccessError, User, UserNotFoundError,
    UserAlreadyExistsError, UserSaveError, VerifiedEmail, password_hasher,
)
from models.data.connected_service import ConnectedService
from models.data.service_entitlement import ServiceEntitlement
from account_challenges import consume_email_challenge, issue_email_challenge
from challenge_email import deliver_challenge_email
from oidc.signin import clear_signin_csrf, valid_signin_csrf
from protocol import build_userinfo, with_protocol_version

# Logger
from libcommon.logger import Logger
from libcommon.color import *
logger = Logger()
logger.setLevel(logger.DEBUG)

# Locale
from libcommon.locale import Locale
locale = Locale('accounts.json')

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'DEFAULT_LANG',
    'SIGNUP_CHALLENGE_TTL_SEC',
    'PASSWORD_RESET_EXPIRATION_SECONDS',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

blueprint_accounts = Blueprint('accounts', __name__)


def _build_userinfo(user):
    return build_userinfo(
        user,
        connected_services=ConnectedService.objects(subject=user.subject_id),
        entitlements=ServiceEntitlement.objects(subject=user.subject_id),
    )


def _signin_success(user, lang):
    """中央セッションを開始して UserInfo を返す (signin/signup 共通の終端)。"""
    browser_context_id = Session.browser_context_id()
    user.last_auth_time = datetime.now(pytz.utc)
    user.save()
    Session.start(str(user.id), browser_context_id=browser_context_id)
    data = _build_userinfo(user)
    request_handle = request.json.get('request_handle') if request.is_json else None
    if request_handle:
        clear_signin_csrf()
        data['next'] = f'/oauth/authorize?request_handle={request_handle}'
    return SuccessFormat(
        data=data,
        code=SuccessCode.OK,
        message=locale.get('signin_success', lang),
    ).http_response()


def _signup_pending(user, lang):
    return SuccessFormat(
        data=_build_userinfo(user),
        code=SuccessCode.ACCEPTED,
        message=locale.get('signup_pending', lang),
    ).http_response()


# ----------------------------------------------------------------------
# POST /v1/users/create  (メール + パスワード登録)
# ----------------------------------------------------------------------
@blueprint_accounts.route('/v1/users/create', methods=['POST'])
@blueprint_accounts.route('/v1/<lang>/users/create', methods=['POST'])
@language_wrapper
@content_type_check_json
@required_fields_check(['email', 'password'])
@regex_check('email', EMAIL_REGEX, 'email_format')
@regex_check('password', PASSWORD_AT_LEAST_ONE_UPPER_AND_NUMERIC_REGEX, 'invalid_password_format')
def users_create(lang, lang_name):
    validation_error = validate_request(lang, locale)
    if validation_error:
        return validation_error.http_response()

    email = request.json.get('email')
    password = request.json.get('password')
    logger.info(magenta(f'[POST] users/create => email: {email} password: ****'))

    try:
        user = User.create_new(email=email, password=password, lang=lang)
    except UserAlreadyExistsError:
        error = UserAlreadyExistsErrorFormat(
            lang=lang, message=locale.get('user_already_exists', lang, [email]))
        return with_protocol_version(error).http_response()
    except UserSaveError:
        error = UnexpectedAPIErrorFormat(lang=lang)
        return with_protocol_version(error).http_response()

    issue_email_challenge(
        purpose='signup',
        destination=email,
        lifetime_seconds=Config.SIGNUP_CHALLENGE_TTL_SEC,
        deliver=deliver_challenge_email,
    )

    # NOTE: 確認コードメールの送信 (libcommon.sendmail) はここに入る。
    # email_verified は verify_code 完了時に True にする (quantz の verify_code と同型)。

    # A pending email is not an authenticated identity. Verification will be
    # implemented by the challenge flow; until then this endpoint fails closed
    # by returning without issuing a central Session.
    return _signup_pending(user, lang)


@blueprint_accounts.route('/v1/users/verify', methods=['POST'])
@blueprint_accounts.route('/v1/<lang>/users/verify', methods=['POST'])
@language_wrapper
@content_type_check_json
@required_fields_check(['email', 'code'])
def users_verify(lang, lang_name):
    validation_error = validate_request(lang, locale)
    if validation_error:
        return validation_error.http_response()
    email = request.json.get('email')
    code = request.json.get('code')
    if not consume_email_challenge(
        purpose='signup', destination=email, code=code
    ):
        error = ForbiddenAPIErrorFormat(lang=lang, field_name='code')
        return with_protocol_version(error).http_response()
    try:
        user = User.find_user_by_email(email)
    except UserNotFoundError:
        error = ForbiddenAPIErrorFormat(lang=lang, field_name='code')
        return with_protocol_version(error).http_response()
    user.email = email
    user.suspended_email = None
    user.verified_emails.append(VerifiedEmail(
        email=email,
        method='email_code',
        verified_at=datetime.now(pytz.utc),
    ))
    user.save()
    return SuccessFormat(
        data={'email': email},
        code=SuccessCode.OK,
        message=locale.get('email_verified', lang),
    ).http_response()


@blueprint_accounts.route('/v1/password-reset/request', methods=['POST'])
@blueprint_accounts.route('/v1/<lang>/password-reset/request', methods=['POST'])
@language_wrapper
@content_type_check_json
@required_fields_check(['email'])
def password_reset_request(lang, lang_name):
    validation_error = validate_request(lang, locale)
    if validation_error:
        return validation_error.http_response()
    email = request.json.get('email')
    try:
        user = User.find_user_by_email(email)
    except UserNotFoundError:
        user = None
    if user and user.email == email and user.is_primary_email_verified():
        issue_email_challenge(
            purpose='password_reset',
            destination=email,
            lifetime_seconds=Config.PASSWORD_RESET_EXPIRATION_SECONDS,
            deliver=deliver_challenge_email,
        )
    return SuccessFormat(
        data={},
        code=SuccessCode.ACCEPTED,
        message=locale.get('password_reset_requested', lang),
    ).http_response()


@blueprint_accounts.route('/v1/password-reset/complete', methods=['POST'])
@blueprint_accounts.route('/v1/<lang>/password-reset/complete', methods=['POST'])
@language_wrapper
@content_type_check_json
@required_fields_check(['email', 'code', 'password'])
@regex_check('password', PASSWORD_AT_LEAST_ONE_UPPER_AND_NUMERIC_REGEX, 'invalid_password_format')
def password_reset_complete(lang, lang_name):
    validation_error = validate_request(lang, locale)
    if validation_error:
        return validation_error.http_response()
    email = request.json.get('email')
    code = request.json.get('code')
    if not consume_email_challenge(
        purpose='password_reset', destination=email, code=code
    ):
        error = ForbiddenAPIErrorFormat(lang=lang, field_name='code')
        return with_protocol_version(error).http_response()
    try:
        user = User.find_user_by_email(email)
    except UserNotFoundError:
        error = ForbiddenAPIErrorFormat(lang=lang, field_name='code')
        return with_protocol_version(error).http_response()
    user.password = password_hasher.hash(request.json.get('password'))
    user.auth_generation += 1
    user.updated_at = datetime.now(pytz.utc)
    user.save()
    Session.revoke_all(str(user.id))
    return SuccessFormat(
        data={},
        code=SuccessCode.OK,
        message=locale.get('password_reset_complete', lang),
    ).http_response()


# ----------------------------------------------------------------------
# POST /v1/users/signin  (メール + パスワード)
# ----------------------------------------------------------------------
@blueprint_accounts.route('/v1/users/signin', methods=['POST'])
@blueprint_accounts.route('/v1/<lang>/users/signin', methods=['POST'])
@language_wrapper
@content_type_check_json
@required_fields_check(['email', 'password'])
def users_signin(lang, lang_name):
    validation_error = validate_request(lang, locale)
    if validation_error:
        return validation_error.http_response()

    if request.json.get('request_handle') and not valid_signin_csrf(request.json):
        error = ForbiddenAPIErrorFormat(lang=lang, field_name='csrf_token')
        return with_protocol_version(error).http_response()

    email = request.json.get('email')
    password = request.json.get('password')
    logger.info(cyan(f'request: {request.url} => email:{email} password: *****'))

    try:
        user = User.find_user_by_email(email)
    except UserNotFoundError:
        error = ResourceNotFoundAPIErrorFormat(
            lang=lang, field_name='email',
            message=locale.get('user_not_found_with_email', lang, [email]))
        return with_protocol_version(error).http_response()

    if not user.check_password(password):
        logger.info(red("Password doesn't match."))
        error = IncorrectPasswordAPIErrorFormat(lang=lang)
        return with_protocol_version(error).http_response()

    if not user.is_active() or not user.is_primary_email_verified():
        error = ForbiddenAPIErrorFormat(lang=lang, field_name='email')
        return with_protocol_version(error).http_response()

    return _signin_success(user, lang)


# ----------------------------------------------------------------------
# POST /v1/users/signin/googleoauth
# ----------------------------------------------------------------------
@blueprint_accounts.route('/v1/users/signin/googleoauth', methods=['POST'])
@blueprint_accounts.route('/v1/<lang>/users/signin/googleoauth', methods=['POST'])
@language_wrapper
@content_type_check_json
@required_fields_check(['token'])
def users_signin_googleoauth(lang, lang_name):
    validation_error = validate_request(lang, locale)
    if validation_error:
        return validation_error.http_response()

    token = request.json.get('token')
    try:
        id_info = verify_token(token)
    except (InvalidTokenError, WrongIssuerError, ClientIDMismatchError,
            TokenExpiredError, EmailNotVerifiedError) as e:
        logger.info(yellow(f'Google OAuth verification failed: {e}'))
        error = UnauthorizedAPIErrorFormat(
            lang=lang, field_name='token',
            message=locale.get('google_oauth_failed', lang))
        return with_protocol_version(error).http_response()

    # Google の境界: Google のトークンは Google の名前 (sub, email) で読む (境界規則)
    email = id_info['email']
    google_id = id_info['sub']

    try:
        user = User.find_user_by_google_id(google_id)
    except UserNotFoundError:
        try:
            user = User.find_user_by_email(email)
        except UserNotFoundError:
            try:
                user = User.create_new_google_oauth(
                    email=email, google_id=google_id, lang=lang
                )
            except UserAlreadyExistsError:
                error = UnauthorizedAPIErrorFormat(
                    lang=lang, field_name='token'
                )
                return with_protocol_version(error).http_response()
        else:
            # A pending password signup is not promoted here: an attacker may
            # have chosen its password before the email owner used Google.
            if not user.is_active() or not user.is_primary_email_verified():
                error = ForbiddenAPIErrorFormat(lang=lang, field_name='email')
                return with_protocol_version(error).http_response()

    if not user.is_active():
        error = ForbiddenAPIErrorFormat(lang=lang, field_name='email')
        return with_protocol_version(error).http_response()
    try:
        user.apply_google_identity(email, google_id)
    except (UnauthorizedAccessError, UserAlreadyExistsError):
        error = UnauthorizedAPIErrorFormat(lang=lang, field_name='token')
        return with_protocol_version(error).http_response()

    return _signin_success(user, lang)
