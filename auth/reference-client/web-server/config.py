# auth/reference-client/web-server/config.py
#
# Environment-backed configuration for the self-contained OIDC reference client.

import os


class Config:
    ENV = os.environ.get('ENV', 'development')
    PUBLIC_BASE_URL = os.environ.get(
        'REFERENCE_CLIENT_PUBLIC_BASE_URL', 'http://127.0.0.1:8030'
    ).rstrip('/')
    CLIENT_ID = os.environ.get('REFERENCE_CLIENT_ID', 'reference')
    CLIENT_SECRET = os.environ.get('REFERENCE_CLIENT_SECRET')
    REDIRECT_URI = f'{PUBLIC_BASE_URL}/auth/callback'

    AUTH_ISSUER = os.environ.get(
        'AUTH_PUBLIC_BASE_URL', 'http://127.0.0.1:8020'
    ).rstrip('/')
    AUTHORIZATION_ENDPOINT = os.environ.get(
        'AUTH_AUTHORIZATION_ENDPOINT', f'{AUTH_ISSUER}/oauth/authorize'
    )
    TOKEN_ENDPOINT = os.environ.get(
        'AUTH_TOKEN_ENDPOINT', f'{AUTH_ISSUER}/oauth/token'
    )
    USERINFO_ENDPOINT = os.environ.get(
        'AUTH_USERINFO_ENDPOINT', f'{AUTH_ISSUER}/oauth/userinfo'
    )
    JWKS_URI = os.environ.get('AUTH_JWKS_URI', f'{AUTH_ISSUER}/oauth/jwks')
    LOGOUT_ENDPOINT = os.environ.get(
        'AUTH_LOGOUT_ENDPOINT', f'{AUTH_ISSUER}/oauth/logout'
    )

    MONGODB_DB_NAME = os.environ.get(
        'REFERENCE_CLIENT_MONGODB_DB_NAME', 'thinkx_auth_reference_client'
    )
    MONGODB_HOST = os.environ.get('REFERENCE_CLIENT_MONGODB_HOST', '127.0.0.1')
    MONGODB_PORT = int(os.environ.get('REFERENCE_CLIENT_MONGODB_PORT', '27017'))

    REDIS_SESSION_HOST = os.environ.get(
        'REFERENCE_CLIENT_REDIS_HOST', '127.0.0.1'
    )
    REDIS_SESSION_PORT = int(
        os.environ.get('REFERENCE_CLIENT_REDIS_PORT', '6379')
    )
    REDIS_SESSION_DB_NUMBER = int(
        os.environ.get('REFERENCE_CLIENT_REDIS_DB_NUMBER', '5')
    )
    REDIS_SESSION_EXPIRATION_TIME_SEC = 60 * 60 * 24 * 30
    REDIS_SESSION_KEY_PREFIX = 'reference_session:'
    SESSION_COOKIE_NAME = 'thinkx_reference_session'

    CLIENT_TRANSACTION_TTL_SEC = 600
    HTTP_RESPONSE_BYTE_LIMIT = 65_536
    REVOCATION_TIMESTAMP_TOLERANCE_SEC = 300
    REVOCATION_WEBHOOK_SECRET = os.environ.get(
        'REFERENCE_CLIENT_REVOCATION_WEBHOOK_SECRET'
    )


def check_config(config, required_keys):
    for key in required_keys:
        value = getattr(config, key, None)
        if value is None or value == '':
            raise RuntimeError(f'Config missing required key: {key}')


def check_secrets(config):
    check_config(config, ('CLIENT_SECRET', 'REVOCATION_WEBHOOK_SECRET'))
    if len(config.CLIENT_SECRET.encode('utf-8')) < 32:
        raise RuntimeError('CLIENT_SECRET must contain at least 32 bytes')
    if len(config.REVOCATION_WEBHOOK_SECRET.encode('utf-8')) < 32:
        raise RuntimeError(
            'REVOCATION_WEBHOOK_SECRET must contain at least 32 bytes'
        )
