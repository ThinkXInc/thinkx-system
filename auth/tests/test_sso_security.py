# auth/tests/test_sso_security.py
#
# Security regression tests for legacy SSO while OIDC endpoints replace it.

from datetime import datetime

import pytest
import pytz

from config import Config
from main import app
from models.data.user import User
import sso


@pytest.fixture(autouse=True)
def clear_state():
    User.drop_collection()
    sso._redis.flushdb()


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def create_verified_user():
    verified_at = datetime.now(pytz.utc)
    return User(
        email='verified@example.com',
        verified_emails=[{
            'email': 'verified@example.com',
            'method': 'seed',
            'verified_at': verified_at,
        }],
    ).save()


def service_secret():
    return Config.SSO_SERVICES['quantz']['service_secret']


def test_auth_generation_invalidates_legacy_code(client):
    user = create_verified_user()
    auth_code = sso._issue_auth_code(
        str(user.id), 'quantz', user.auth_generation
    )
    user.auth_generation += 1
    user.save()

    response = client.post(
        '/v1/token/exchange',
        json={
            'auth_code': auth_code,
            'service_id': 'quantz',
            'service_secret': service_secret(),
        },
    )

    assert response.status_code == 401


def test_suspended_user_cannot_use_legacy_access_token_or_user_lookup(client):
    user = create_verified_user()
    access_token = sso._issue_access_token(
        str(user.id), 'quantz', user.auth_generation
    )
    user.status = 'suspended'
    user.save()

    userinfo_response = client.get(
        '/v1/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    lookup_response = client.get(
        f'/v1/users/{user.id}',
        headers={
            sso.SERVICE_ID_HEADER: 'quantz',
            sso.SERVICE_SECRET_HEADER: service_secret(),
        },
    )

    assert userinfo_response.status_code == 401
    assert lookup_response.status_code == 401


def test_authorize_clears_suspended_central_session(client, monkeypatch):
    user = create_verified_user()
    user.status = 'suspended'
    user.save()
    cleared = []
    monkeypatch.setattr(sso.Session, 'user_id', lambda: str(user.id))
    monkeypatch.setattr(sso.Session, 'clear', lambda: cleared.append(True))

    response = client.get(
        '/authorize',
        query_string={
            'service_id': 'quantz',
            'redirect_uri': Config.SSO_SERVICES['quantz']['redirect_uris'][0],
            'state': 'state-value',
        },
    )

    assert response.status_code == 200
    assert cleared == [True]
