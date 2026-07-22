# auth/tests/test_account_challenges.py
#
# A-5 contract tests for signup verification and password reset.

from datetime import datetime

import pytest
import pytz

import accounts
from main import app
from models.data.user import User, password_hasher
from models.data.verification_challenge import VerificationChallenge
from oidc.endpoints import redis_client


@pytest.fixture(autouse=True)
def clear_state(monkeypatch):
    User.drop_collection()
    VerificationChallenge.drop_collection()
    redis_client.flushdb()
    delivered = []
    monkeypatch.setattr(
        accounts,
        'deliver_challenge_email',
        lambda **message: delivered.append(message),
    )
    return delivered


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def create_verified_user(email='verified@example.com'):
    now = datetime.now(pytz.utc)
    return User(
        email=email,
        verified_emails=[{
            'email': email,
            'method': 'seed',
            'verified_at': now,
        }],
        password=password_hasher.hash('OldPassword1'),
    ).save()


def test_signup_delivers_unlogged_code_and_verifies_once(client, clear_state):
    create_response = client.post(
        '/v1/users/create',
        json={'email': 'new@example.com', 'password': 'StrongPass1'},
    )

    assert create_response.status_code == 202
    assert len(clear_state) == 1
    delivery = clear_state[0]
    assert delivery['destination'] == 'new@example.com'
    assert delivery['code'] not in create_response.get_data(as_text=True)
    challenge = VerificationChallenge.objects.get(destination='new@example.com')
    assert delivery['code'] not in challenge.code_hash

    verify_response = client.post(
        '/v1/users/verify',
        json={'email': 'new@example.com', 'code': delivery['code']},
    )
    replay_response = client.post(
        '/v1/users/verify',
        json={'email': 'new@example.com', 'code': delivery['code']},
    )

    assert verify_response.status_code == 200
    assert replay_response.status_code == 403
    user = User.find_user_by_email('new@example.com')
    assert user.email == 'new@example.com'
    assert user.suspended_email is None
    assert user.is_primary_email_verified()


def test_wrong_signup_code_is_limited_without_consuming_valid_code(
    client, clear_state
):
    client.post(
        '/v1/users/create',
        json={'email': 'new@example.com', 'password': 'StrongPass1'},
    )
    code = clear_state[0]['code']

    for _attempt in range(4):
        assert client.post(
            '/v1/users/verify',
            json={'email': 'new@example.com', 'code': 'wrong-code'},
        ).status_code == 403
    assert client.post(
        '/v1/users/verify',
        json={'email': 'new@example.com', 'code': code},
    ).status_code == 200


def test_password_reset_request_does_not_enumerate_accounts(client, clear_state):
    create_verified_user()

    existing = client.post(
        '/v1/password-reset/request', json={'email': 'verified@example.com'}
    )
    missing = client.post(
        '/v1/password-reset/request', json={'email': 'missing@example.com'}
    )

    assert existing.status_code == missing.status_code == 202
    assert existing.get_json() == missing.get_json()
    assert len(clear_state) == 1


def test_password_reset_changes_hash_generation_and_revokes_sessions(
    client, clear_state, monkeypatch
):
    user = create_verified_user()
    revoked = []
    monkeypatch.setattr(
        accounts.Session, 'revoke_all', lambda user_id: revoked.append(user_id)
    )
    client.post(
        '/v1/password-reset/request', json={'email': 'verified@example.com'}
    )
    code = clear_state[0]['code']
    generation = user.auth_generation

    response = client.post(
        '/v1/password-reset/complete',
        json={
            'email': 'verified@example.com',
            'code': code,
            'password': 'NewPassword1',
        },
    )

    assert response.status_code == 200
    reset_user = User.find_user_by_email('verified@example.com')
    assert reset_user.check_password('NewPassword1')
    assert not reset_user.check_password('OldPassword1')
    assert reset_user.auth_generation == generation + 1
    assert revoked == [str(user.id)]
