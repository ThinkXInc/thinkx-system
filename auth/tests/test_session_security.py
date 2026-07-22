# auth/tests/test_session_security.py
#
# Integration regressions for auth's vendored Redis Session boundary.

from datetime import datetime

import pytest
import pytz

from config import Config
from libcommon.web.session import Session
from main import app
from models.data.auth_service import AuthService
from models.data.connected_service import ConnectedService
from models.data.revocation_outbox import RevocationOutbox
from models.data.user import User, password_hasher
from oidc.endpoints import redis_client
from oidc.stores import pkce_s256_challenge


AUTH_BASE_URL = 'https://auth.example.test'
CLIENT_ID = 'reference'
CLIENT_SECRET = 'reference-client-secret-with-at-least-32-bytes'
CODE_VERIFIER = 'code-verifier-value-with-more-than-forty-three-characters'
PASSWORD = 'StrongPass1'
REDIRECT_URI = 'https://client.example/auth/callback'


@pytest.fixture(autouse=True)
def clear_state(monkeypatch):
    for model in (User, AuthService, ConnectedService, RevocationOutbox):
        model.drop_collection()
    Session._r().flushdb()
    redis_client.flushdb()
    monkeypatch.setitem(app.config, 'TESTING', True)
    monkeypatch.setitem(app.config, 'SESSION_COOKIE_SECURE', True)
    monkeypatch.setitem(app.config, 'SESSION_COOKIE_HTTPONLY', True)
    monkeypatch.setitem(app.config, 'SESSION_COOKIE_SAMESITE', 'Lax')
    monkeypatch.setattr(Config, 'AUTH_PUBLIC_BASE_URL', AUTH_BASE_URL)


def create_user():
    now = datetime.now(pytz.utc)
    return User(
        email='verified@example.com',
        verified_emails=[{
            'email': 'verified@example.com',
            'method': 'seed',
            'verified_at': now,
        }],
        password=password_hasher.hash(PASSWORD),
        last_auth_time=now,
    ).save()


def signin(client):
    response = client.post(
        '/v1/users/signin',
        base_url=AUTH_BASE_URL,
        json={'email': 'verified@example.com', 'password': PASSWORD},
    )
    assert response.status_code == 200
    return response


def authorization_query():
    return {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid',
        'state': 'state-value-with-enough-entropy',
        'nonce': 'nonce-value-with-enough-entropy',
        'code_challenge': pkce_s256_challenge(CODE_VERIFIER),
        'code_challenge_method': 'S256',
    }


def test_signin_set_cookie_applies_security_config():
    create_user()

    response = signin(app.test_client())

    cookie_parts = response.headers['Set-Cookie'].split('; ')
    assert cookie_parts[0].startswith(f'{Config.SESSION_COOKIE_NAME}=')
    assert {'Secure', 'HttpOnly', 'SameSite=Lax'} <= set(cookie_parts[1:])
    assert not any(part.startswith('Domain=') for part in cookie_parts)


def test_global_logout_revokes_second_browser_session():
    user = create_user()
    AuthService.provision(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uris=[REDIRECT_URI],
        allowed_scopes=['openid'],
        trusted_first_party=True,
    )
    first_client = app.test_client()
    second_client = app.test_client()
    signin(first_client)
    signin(second_client)

    before = second_client.get(
        '/oauth/authorize',
        base_url=AUTH_BASE_URL,
        query_string=authorization_query(),
    )
    assert before.status_code == 302
    assert before.headers['Location'].startswith(f'{REDIRECT_URI}?')

    logout = first_client.post(
        '/oauth/logout',
        base_url=AUTH_BASE_URL,
        headers={'Origin': AUTH_BASE_URL},
    )
    assert logout.status_code == 204

    after = second_client.get(
        '/oauth/authorize',
        base_url=AUTH_BASE_URL,
        query_string=authorization_query(),
    )
    assert after.status_code == 302
    assert after.headers['Location'].startswith('/signin?request_handle=')
    assert User.objects.get(id=user.id).auth_generation == 1
