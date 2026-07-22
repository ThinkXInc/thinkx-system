# auth/tests/test_entitlements_endpoint.py
#
# A-7 contract tests for authenticated payment projection updates.

from datetime import datetime, timedelta

import pytest
import pytz

from entitlements import projection_signature
from main import app
from models.data.auth_service import AuthService
from models.data.service_entitlement import ServiceEntitlement
from models.data.user import User


CLIENT_SECRET = 'client-secret-with-more-than-thirty-two-bytes'


@pytest.fixture(autouse=True)
def clear_entitlements():
    ServiceEntitlement.drop_collection()
    User.drop_collection()
    AuthService.drop_collection()
    User(subject_id='subject-1').save()
    AuthService.provision(
        client_id='reference',
        client_secret=CLIENT_SECRET,
        redirect_uris=['https://client.example/auth/callback'],
        allowed_scopes=['openid', 'email'],
    )


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def projection_payload(timestamp=None):
    timestamp = timestamp or datetime.now(pytz.utc)
    return {
        'subject': 'subject-1',
        'client_id': 'reference',
        'plan': 'pro',
        'billing_status': 'active',
        'payment_event_id': 'payment-event-1',
        'source_event_timestamp': timestamp.isoformat(),
    }


def post_projection(client, payload, signature=None):
    return client.post(
        '/v1/internal/service-entitlements',
        json=payload,
        headers={
            'X-Payment-Signature': signature or projection_signature(payload)
        },
    )


def test_signed_projection_is_applied_and_replay_is_idempotent(client):
    payload = projection_payload()

    first = post_projection(client, payload)
    replay = post_projection(client, payload)

    assert first.status_code == 200
    assert first.get_json()['applied'] is True
    assert replay.status_code == 200
    assert replay.get_json()['applied'] is False
    assert ServiceEntitlement.objects.count() == 1


def test_unsigned_and_tampered_projection_are_rejected(client):
    payload = projection_payload()
    signature = projection_signature(payload)

    unsigned = client.post('/v1/internal/service-entitlements', json=payload)
    tampered = post_projection(
        client, {**payload, 'plan': 'free'}, signature=signature
    )

    assert unsigned.status_code == 401
    assert tampered.status_code == 401
    assert ServiceEntitlement.objects.count() == 0


def test_older_projection_does_not_overwrite_newer_state(client):
    now = datetime.now(pytz.utc)
    current = projection_payload(now)
    stale = {
        **projection_payload(now - timedelta(seconds=1)),
        'payment_event_id': 'payment-event-stale',
        'plan': 'free',
        'billing_status': 'none',
    }

    assert post_projection(client, current).get_json()['applied'] is True
    assert post_projection(client, stale).get_json()['applied'] is False
    saved = ServiceEntitlement.objects.get()
    assert saved.plan == 'pro'
    assert saved.billing_status == 'active'


def test_event_id_conflict_and_naive_timestamp_are_rejected(client):
    payload = projection_payload()
    post_projection(client, payload)
    conflict = {**payload, 'plan': 'free'}
    naive = {
        **payload,
        'payment_event_id': 'payment-event-2',
        'source_event_timestamp': '2026-07-22T12:00:00',
    }

    assert post_projection(client, conflict).status_code == 400
    assert post_projection(client, naive).status_code == 400


def test_unknown_identity_client_and_invalid_billing_status_are_rejected(client):
    payload = projection_payload()
    unknown_subject = {**payload, 'subject': 'unknown-subject'}
    unknown_client = {
        **payload,
        'payment_event_id': 'payment-event-2',
        'client_id': 'unknown-client',
    }
    invalid_status = {
        **payload,
        'payment_event_id': 'payment-event-3',
        'billing_status': 'arbitrary',
    }

    assert post_projection(client, unknown_subject).status_code == 400
    assert post_projection(client, unknown_client).status_code == 400
    assert post_projection(client, invalid_status).status_code == 400
    assert ServiceEntitlement.objects.count() == 0
