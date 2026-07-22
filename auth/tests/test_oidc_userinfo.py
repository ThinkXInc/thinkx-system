# auth/tests/test_oidc_userinfo.py
#
# A-4 contract tests for UserInfo scope and access-token generation checks.

from datetime import datetime
import json

import pytest
import pytz

from main import app
from models.data.user import User
from oidc.endpoints import redis_client, sso_store
from oidc.stores import sha256_hex


ACCESS_TOKEN = 'opaque-access-token-with-enough-random-characters'


@pytest.fixture(autouse=True)
def clear_state():
    User.drop_collection()
    redis_client.flushdb()


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def create_user():
    now = datetime.now(pytz.utc)
    return User(
        email='verified@example.com',
        verified_emails=[{
            'email': 'verified@example.com',
            'method': 'seed',
            'verified_at': now,
        }],
    ).save()


def store_access_token(user, scope='openid email'):
    redis_client.setex(
        sso_store.TOKEN_PREFIX + sha256_hex(ACCESS_TOKEN),
        3600,
        json.dumps({
            'subject': user.subject_id,
            'client_id': 'reference',
            'scope': scope,
            'auth_generation': user.auth_generation,
        }),
    )


def bearer_header(access_token=ACCESS_TOKEN):
    return {'Authorization': f'Bearer {access_token}'}


def test_userinfo_returns_subject_and_email_scope_claims(client):
    user = create_user()
    store_access_token(user)

    response = client.get('/oauth/userinfo', headers=bearer_header())

    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.get_json() == {
        'sub': user.subject_id,
        'email': 'verified@example.com',
        'email_verified': True,
    }


def test_userinfo_post_and_openid_only_scope_return_subject_only(client):
    user = create_user()
    store_access_token(user, scope='openid')

    response = client.post('/oauth/userinfo', headers=bearer_header())

    assert response.status_code == 200
    assert response.get_json() == {'sub': user.subject_id}


def test_userinfo_rechecks_auth_generation_and_user_status(client):
    user = create_user()
    store_access_token(user)
    user.auth_generation += 1
    user.save()

    generation_response = client.get('/oauth/userinfo', headers=bearer_header())
    user.auth_generation -= 1
    user.status = 'suspended'
    user.save()
    status_response = client.get('/oauth/userinfo', headers=bearer_header())

    assert generation_response.status_code == 401
    assert status_response.status_code == 401
    assert generation_response.get_json() == {'error': 'invalid_token'}


@pytest.mark.parametrize(
    'authorization',
    [None, 'Basic abc', 'Bearer', 'Bearer unknown-token', 'Bearer token extra'],
)
def test_userinfo_rejects_missing_or_invalid_bearer_token(client, authorization):
    headers = {'Authorization': authorization} if authorization else {}

    response = client.get('/oauth/userinfo', headers=headers)

    assert response.status_code == 401
    assert response.get_json() == {'error': 'invalid_token'}
    assert response.headers['WWW-Authenticate'] == 'Bearer error="invalid_token"'
