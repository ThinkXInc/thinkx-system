# auth/web-server/oidc/endpoints.py
#
# Read-only OpenID Provider metadata and JWKS endpoints.

import hmac
import re
from urllib.parse import urlencode

from flask import Blueprint, jsonify, redirect, render_template, request
from redis import StrictRedis

from config import Config, check_config
from libcommon.web.session import Session
from models.data.auth_service import AuthService
from models.data.connected_service import ConnectedService
from models.data.user import User
from oidc.id_token import public_jwks
from oidc.id_token import IDTokenIssuer
from oidc.signin import issue_signin_csrf_token
from oidc.stores import AuthorizationRequestStore, SSOStore, sha256_hex


REQUIRED_KEYS_IN_CONFIG = [
    'AUTH_PUBLIC_BASE_URL',
    'OIDC_ID_TOKEN_TTL_SEC',
    'OIDC_AUTHORIZATION_REQUEST_TTL_SEC',
    'REDIS_SESSION_HOST',
    'REDIS_SESSION_PORT',
    'SSO_REDIS_DB_NUMBER',
    'SSO_CODE_TTL_SEC',
    'SSO_ACCESS_TOKEN_TTL_SEC',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

blueprint_oidc = Blueprint('oidc', __name__)
redis_client = StrictRedis(
    host=Config.REDIS_SESSION_HOST,
    port=Config.REDIS_SESSION_PORT,
    db=Config.SSO_REDIS_DB_NUMBER,
)
authorization_requests = AuthorizationRequestStore(
    redis_client, Config.OIDC_AUTHORIZATION_REQUEST_TTL_SEC
)
sso_store = SSOStore(
    redis_client, Config.SSO_CODE_TTL_SEC, Config.SSO_ACCESS_TOKEN_TTL_SEC
)
id_token_issuer = IDTokenIssuer(
    issuer=Config.AUTH_PUBLIC_BASE_URL.rstrip('/'),
    lifetime_seconds=Config.OIDC_ID_TOKEN_TTL_SEC,
)
OAUTH_RANDOM_VALUE_PATTERN = re.compile(r'^[A-Za-z0-9._~-]{16,256}$')
PKCE_CODE_CHALLENGE_PATTERN = re.compile(r'^[A-Za-z0-9_-]{43}$')
PKCE_CODE_VERIFIER_PATTERN = re.compile(r'^[A-Za-z0-9._~-]{43,128}$')


def provider_url(path):
    return f"{Config.AUTH_PUBLIC_BASE_URL.rstrip('/')}{path}"


def oauth_error(error, status=400):
    response = jsonify({'error': error})
    response.status_code = status
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


def single_query_parameters(names):
    values = {}
    for name in names:
        candidates = request.args.getlist(name)
        if len(candidates) != 1:
            return None
        values[name] = candidates[0]
    return values


def browser_context_hash():
    return sha256_hex(Session.browser_context_id())


def validated_authorization_parameters():
    names = (
        'response_type', 'client_id', 'redirect_uri', 'scope', 'state',
        'nonce', 'code_challenge', 'code_challenge_method',
    )
    parameters = single_query_parameters(names)
    if parameters is None:
        return None, 'invalid_request'
    service = AuthService.find(parameters['client_id'])
    if not service or service.status != 'active':
        return None, 'unauthorized_client'
    if not service.valid_redirect(parameters['redirect_uri']):
        return None, 'invalid_redirect_uri'
    if parameters['response_type'] != 'code':
        return parameters, 'unsupported_response_type'
    scopes = parameters['scope'].split()
    if 'openid' not in scopes or not set(scopes) <= set(service.allowed_scopes):
        return parameters, 'invalid_scope'
    if parameters['code_challenge_method'] != 'S256':
        return parameters, 'invalid_request'
    if any(
        not OAUTH_RANDOM_VALUE_PATTERN.fullmatch(parameters[name])
        for name in ('state', 'nonce')
    ):
        return parameters, 'invalid_request'
    if not PKCE_CODE_CHALLENGE_PATTERN.fullmatch(parameters['code_challenge']):
        return parameters, 'invalid_request'
    return parameters, None


def current_active_user():
    user_id = Session.user_id()
    user = User.objects(id=user_id).first() if user_id else None
    if (
        user
        and user.is_active()
        and user.is_primary_email_verified()
        and user.last_auth_time
    ):
        return user
    return None


def resumed_authorization_parameters(request_handle):
    parameters = authorization_requests.get(request_handle)
    if not parameters:
        return None
    if not hmac.compare_digest(
        parameters['browser_context_hash'], browser_context_hash()
    ):
        return None
    return parameters


def issue_code_and_redirect(user, parameters, request_handle=None):
    code = sso_store.issue_code({
        'subject': user.subject_id,
        'client_id': parameters['client_id'],
        'redirect_uri': parameters['redirect_uri'],
        'code_challenge': parameters['code_challenge'],
        'nonce': parameters['nonce'],
        'scope': parameters['scope'],
        'auth_generation': user.auth_generation,
    })
    ConnectedService.connect(user.subject_id, parameters['client_id'])
    if request_handle:
        authorization_requests.delete(request_handle)
    query = urlencode({
        'code': code,
        'state': parameters['state'],
        'iss': Config.AUTH_PUBLIC_BASE_URL.rstrip('/'),
    })
    return redirect(f"{parameters['redirect_uri']}?{query}")


def authorization_error_redirect(parameters, error):
    query = urlencode({
        'error': error,
        'state': parameters['state'],
        'iss': Config.AUTH_PUBLIC_BASE_URL.rstrip('/'),
    })
    return redirect(f"{parameters['redirect_uri']}?{query}")


@blueprint_oidc.get('/signin')
def signin():
    request_handle = request.args.get('request_handle', '')
    record = authorization_requests.get(request_handle) if request_handle else None
    if not record or not hmac.compare_digest(
        record['browser_context_hash'], browser_context_hash()
    ):
        return oauth_error('invalid_request')
    return render_template(
        'signin.html',
        lang=Config.DEFAULT_LANG,
        lang_name=Config.DEFAULT_LANG,
        request_handle=request_handle,
        csrf_token=issue_signin_csrf_token(request_handle),
        service_id='',
        redirect_uri='',
        state='',
    )


@blueprint_oidc.get('/oauth/authorize')
def authorize():
    request_handle = request.args.get('request_handle')
    if request_handle:
        parameters = resumed_authorization_parameters(request_handle)
        if not parameters:
            return oauth_error('invalid_request')
    else:
        parameters, error = validated_authorization_parameters()
        if error:
            if parameters:
                return authorization_error_redirect(parameters, error)
            return oauth_error(error)

    user = current_active_user()
    if user:
        return issue_code_and_redirect(user, parameters, request_handle)

    if request_handle:
        return redirect(f'/signin?{urlencode({"request_handle": request_handle})}')
    parameters['browser_context_hash'] = browser_context_hash()
    request_handle = authorization_requests.create(parameters)
    return redirect(f'/signin?{urlencode({"request_handle": request_handle})}')


def authenticated_client():
    authorization = request.authorization
    if not authorization or authorization.type.lower() != 'basic':
        return None
    service = AuthService.find(authorization.username)
    if not service or not service.verify_secret(authorization.password or ''):
        return None
    return service


def token_request_values():
    names = ('grant_type', 'code', 'redirect_uri', 'code_verifier')
    if any(len(request.form.getlist(name)) != 1 for name in names):
        return None
    return {name: request.form[name] for name in names}


@blueprint_oidc.post('/oauth/token')
def token():
    if request.mimetype != 'application/x-www-form-urlencoded':
        return oauth_error('invalid_request')
    service = authenticated_client()
    if not service:
        return oauth_error('invalid_client', 401)
    values = token_request_values()
    if not values:
        return oauth_error('invalid_request')
    if values['grant_type'] != 'authorization_code':
        return oauth_error('unsupported_grant_type')
    if not PKCE_CODE_VERIFIER_PATTERN.fullmatch(values['code_verifier']):
        return oauth_error('invalid_grant')
    record = sso_store.begin_consume(
        code=values['code'],
        client_id=service.client_id,
        redirect_uri=values['redirect_uri'],
        code_verifier=values['code_verifier'],
    )
    if record is None:
        return oauth_error('invalid_grant')
    user = User.objects(subject_id=record['subject']).first()
    if (
        not user
        or not user.is_active()
        or user.auth_generation != record['auth_generation']
    ):
        return oauth_error('invalid_grant')
    id_token = id_token_issuer.issue(
        subject=user.subject_id,
        audience=service.client_id,
        nonce=record['nonce'],
        auth_time=user.last_auth_time,
    )
    access_token = sso_store.finish_consume_and_issue_access_token(
        code=values['code'], record=record
    )
    if access_token is None:
        return oauth_error('invalid_grant')
    response = jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': Config.SSO_ACCESS_TOKEN_TTL_SEC,
        'id_token': id_token,
    })
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


@blueprint_oidc.get('/.well-known/openid-configuration')
def openid_configuration():
    return jsonify({
        'issuer': Config.AUTH_PUBLIC_BASE_URL.rstrip('/'),
        'authorization_endpoint': provider_url('/oauth/authorize'),
        'token_endpoint': provider_url('/oauth/token'),
        'userinfo_endpoint': provider_url('/oauth/userinfo'),
        'jwks_uri': provider_url('/oauth/jwks'),
        'end_session_endpoint': provider_url('/oauth/logout'),
        'response_types_supported': ['code'],
        'subject_types_supported': ['public'],
        'id_token_signing_alg_values_supported': ['RS256'],
        'scopes_supported': ['openid', 'email'],
        'token_endpoint_auth_methods_supported': ['client_secret_basic'],
        'code_challenge_methods_supported': ['S256'],
    })


@blueprint_oidc.get('/oauth/jwks')
def jwks():
    response = jsonify(public_jwks())
    response.headers['Cache-Control'] = 'public, max-age=300'
    return response
