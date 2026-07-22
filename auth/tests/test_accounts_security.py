# auth/tests/test_accounts_security.py
#
# Security regression tests for the temporary account scaffold.

from datetime import datetime

import pytest
import pytz

import accounts
from main import app
from models.data.connected_service import ConnectedService
from models.data.service_entitlement import ServiceEntitlement
from models.data.user import User, password_hasher


@pytest.fixture(autouse=True)
def clear_users():
    for model in (User, ConnectedService, ServiceEntitlement):
        model.drop_collection()


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def fail_if_session_starts(*_args, **_kwargs):
    raise AssertionError('pending or suspended user started a Session')


def test_signup_creates_pending_user_without_starting_session(client, monkeypatch):
    monkeypatch.setattr(accounts.Session, 'start', fail_if_session_starts)

    response = client.post(
        '/v1/users/create',
        json={'email': 'pending@example.com', 'password': 'StrongPass1'},
    )

    assert response.status_code == 202
    user = User.find_user_by_email('pending@example.com')
    assert user.email is None
    assert user.suspended_email == 'pending@example.com'


def test_password_signin_rejects_pending_and_suspended_users(client, monkeypatch):
    monkeypatch.setattr(accounts.Session, 'start', fail_if_session_starts)
    User.create_new('pending@example.com', 'StrongPass1')
    verified_at = datetime.now(pytz.utc)
    User(
        email='suspended@example.com',
        verified_emails=[{
            'email': 'suspended@example.com',
            'method': 'seed',
            'verified_at': verified_at,
        }],
        password=password_hasher.hash('StrongPass1'),
        status='suspended',
    ).save()

    pending_response = client.post(
        '/v1/users/signin',
        json={'email': 'pending@example.com', 'password': 'StrongPass1'},
    )
    suspended_response = client.post(
        '/v1/users/signin',
        json={'email': 'suspended@example.com', 'password': 'StrongPass1'},
    )

    assert pending_response.status_code == 403
    assert suspended_response.status_code == 403


def test_google_signin_rejects_pending_user(client, monkeypatch):
    monkeypatch.setattr(accounts.Session, 'start', fail_if_session_starts)
    monkeypatch.setattr(
        accounts,
        'verify_token',
        lambda _token: {'email': 'pending@example.com', 'sub': 'google-subject'},
    )
    User.create_new('pending@example.com', 'StrongPass1')

    response = client.post(
        '/v1/users/signin/googleoauth',
        json={'token': 'verified-google-token'},
    )

    assert response.status_code == 403


def test_verified_active_password_signin_starts_session_and_returns_projection(
    client, monkeypatch
):
    started_users = []
    monkeypatch.setattr(
        accounts.Session,
        'start',
        lambda user_id, **_kwargs: started_users.append(user_id),
    )
    verified_at = datetime.now(pytz.utc)
    user = User(
        email='verified@example.com',
        verified_emails=[{
            'email': 'verified@example.com',
            'method': 'seed',
            'verified_at': verified_at,
        }],
        password=password_hasher.hash('StrongPass1'),
    ).save()
    ConnectedService.connect(user.subject_id, 'reference')
    ServiceEntitlement.apply_projection(
        subject=user.subject_id,
        client_id='reference',
        plan='pro',
        billing_status='active',
        payment_event_id='event-active',
        source_event_timestamp=verified_at,
    )

    response = client.post(
        '/v1/users/signin',
        json={'email': 'verified@example.com', 'password': 'StrongPass1'},
    )

    assert response.status_code == 200
    assert started_users == [str(user.id)]
    assert response.get_json()['services'] == {
        'reference': {'plan': 'pro', 'billing_status': 'active'},
    }


def test_google_signin_resolves_stable_subject_before_changed_email(
    client, monkeypatch
):
    started_users = []
    monkeypatch.setattr(
        accounts.Session,
        'start',
        lambda user_id, **_kwargs: started_users.append(user_id),
    )
    monkeypatch.setattr(
        accounts,
        'verify_token',
        lambda _token: {
            'email': 'new-google@example.com',
            'sub': 'stable-google-subject',
        },
    )
    user = User.create_new_google_oauth(
        email='old-google@example.com',
        google_id='stable-google-subject',
    )

    response = client.post(
        '/v1/users/signin/googleoauth',
        json={'token': 'verified-google-token'},
    )

    assert response.status_code == 200
    assert started_users == [str(user.id)]
    updated = User.find_user_by_google_id('stable-google-subject')
    assert updated.email == 'new-google@example.com'
    assert updated.is_primary_email_verified()


def test_google_signin_rejects_mismatched_subject_for_existing_email(
    client, monkeypatch
):
    monkeypatch.setattr(accounts.Session, 'start', fail_if_session_starts)
    monkeypatch.setattr(
        accounts,
        'verify_token',
        lambda _token: {
            'email': 'google@example.com',
            'sub': 'different-google-subject',
        },
    )
    User.create_new_google_oauth(
        email='google@example.com',
        google_id='original-google-subject',
    )

    response = client.post(
        '/v1/users/signin/googleoauth',
        json={'token': 'verified-google-token'},
    )

    assert response.status_code == 401
