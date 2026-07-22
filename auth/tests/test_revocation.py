# auth/tests/test_revocation.py
#
# A-6 contract tests for global revocation, logout, and durable webhook delivery.

from datetime import datetime, timedelta
import json

import pytest
import pytz
import requests

from config import Config
from main import app
from models.data.auth_service import AuthService
from models.data.connected_service import ConnectedService
from models.data.revocation_outbox import RevocationOutbox
from models.data.user import User
from revocation import deliver_pending_revocations, revoke_user, webhook_signature


CLIENT_SECRET = 'client-secret-with-more-than-thirty-two-bytes'
WEBHOOK_SECRET = 'separate-webhook-secret-with-enough-entropy'


class SuccessfulResponse:
    status_code = 204


class RedirectResponse:
    status_code = 302


@pytest.fixture(autouse=True)
def clear_state():
    for model in (User, AuthService, ConnectedService, RevocationOutbox):
        model.drop_collection()


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
        last_auth_time=now,
    ).save()


def connect_service(user):
    service = AuthService.provision(
        client_id='reference',
        client_secret=CLIENT_SECRET,
        redirect_uris=['https://client.example/auth/callback'],
        allowed_scopes=['openid', 'email'],
    )
    service.revoke_url = 'https://client.example/v1/sessions/revoke'
    service.revoke_webhook_secret = WEBHOOK_SECRET
    service.save()
    ConnectedService.connect(user.subject_id, service.client_id)
    return service


def test_revoke_user_increments_generation_revokes_sessions_and_writes_outbox(
    monkeypatch,
):
    user = create_user()
    connect_service(user)
    revoked = []
    monkeypatch.setattr(
        'revocation.Session.revoke_all', lambda user_id: revoked.append(user_id)
    )

    generation = revoke_user(user, reason='password_reset')

    assert generation == 1
    assert revoked == [str(user.id)]
    record = RevocationOutbox.objects.get()
    assert record.client_id == 'reference'
    assert record.payload['subject'] == user.subject_id
    assert record.payload['auth_generation'] == 1
    assert record.payload['reason'] == 'password_reset'


def test_outbox_delivery_is_signed_and_marks_success(monkeypatch):
    user = create_user()
    connect_service(user)
    monkeypatch.setattr('revocation.Session.revoke_all', lambda _user_id: None)
    revoke_user(user, reason='global_logout')
    sent = []

    def post(url, **kwargs):
        sent.append((url, kwargs))
        return SuccessfulResponse()

    assert deliver_pending_revocations(post=post) == [True]
    record = RevocationOutbox.objects.get()
    assert record.status == 'delivered'
    url, arguments = sent[0]
    assert url == 'https://client.example/v1/sessions/revoke'
    assert arguments['timeout'] == (3.0, 10.0)
    assert arguments['allow_redirects'] is False
    payload = json.loads(arguments['data'])
    assert arguments['headers']['X-Auth-Signature'] == webhook_signature(
        WEBHOOK_SECRET, payload
    )


def test_failed_delivery_remains_pending_without_secret_in_error(monkeypatch):
    user = create_user()
    connect_service(user)
    monkeypatch.setattr('revocation.Session.revoke_all', lambda _user_id: None)
    revoke_user(user, reason='global_logout')

    def timeout(*_args, **_kwargs):
        raise requests.Timeout(f'timeout {WEBHOOK_SECRET}')

    assert deliver_pending_revocations(post=timeout) == [False]
    record = RevocationOutbox.objects.get()
    assert record.status == 'pending'
    assert record.attempts == 1
    assert record.last_error == 'Timeout'
    assert WEBHOOK_SECRET not in record.last_error


def test_redirect_response_is_failure_and_stale_processing_is_retried(monkeypatch):
    user = create_user()
    connect_service(user)
    monkeypatch.setattr('revocation.Session.revoke_all', lambda _user_id: None)
    revoke_user(user, reason='global_logout')
    record = RevocationOutbox.objects.get()
    record.status = 'processing'
    record.processing_started_at = datetime.now(pytz.utc) - timedelta(minutes=6)
    record.save()

    assert deliver_pending_revocations(
        post=lambda *_args, **_kwargs: RedirectResponse()
    ) == [False]
    retried = RevocationOutbox.objects.get(id=record.id)
    assert retried.status == 'pending'
    assert retried.last_error == 'HTTPError'


def test_auth_logout_clears_only_current_session(client, monkeypatch):
    user = create_user()
    cleared = []
    monkeypatch.setattr('oidc.endpoints.Session.clear_current', lambda: cleared.append(True))
    monkeypatch.setattr('oidc.endpoints.Session.user_id', lambda: str(user.id))

    response = client.post(
        '/oauth/logout',
        data={'logout_type': 'auth'},
        headers={'Origin': Config.AUTH_PUBLIC_BASE_URL},
    )

    assert response.status_code == 204
    assert cleared == [True]
    assert User.objects.get(id=user.id).auth_generation == 0
    assert RevocationOutbox.objects.count() == 0


def test_global_logout_is_default_and_reuses_revocation_flow(client, monkeypatch):
    user = create_user()
    connect_service(user)
    revoked = []
    monkeypatch.setattr('oidc.endpoints.Session.user_id', lambda: str(user.id))
    monkeypatch.setattr(
        'revocation.Session.revoke_all', lambda user_id: revoked.append(user_id)
    )

    response = client.post(
        '/oauth/logout', headers={'Origin': Config.AUTH_PUBLIC_BASE_URL}
    )

    assert response.status_code == 204
    assert revoked == [str(user.id)]
    assert User.objects.get(id=user.id).auth_generation == 1
    assert RevocationOutbox.objects.count() == 1


def test_logout_rejects_cross_origin_request(client):
    response = client.post(
        '/oauth/logout', headers={'Origin': 'https://evil.example'}
    )

    assert response.status_code == 400
    assert response.get_json() == {'error': 'invalid_request'}
