# auth/web-server/oidc/endpoints.py
#
# Read-only OpenID Provider metadata and JWKS endpoints.

from flask import Blueprint, jsonify

from config import Config, check_config
from oidc.id_token import public_jwks


REQUIRED_KEYS_IN_CONFIG = ['AUTH_PUBLIC_BASE_URL']
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

blueprint_oidc = Blueprint('oidc', __name__)


def provider_url(path):
    return f"{Config.AUTH_PUBLIC_BASE_URL.rstrip('/')}{path}"


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
