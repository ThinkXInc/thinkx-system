# auth/tests/test_data_models.py
#
# A-1 tests for auth identity, client registration, billing projection, and seed data.

from datetime import datetime, timedelta

from mongoengine import NotUniqueError
import pytest
import pytz

from models.data.auth_service import AuthService, digest_client_secret
from models.data.connected_service import ConnectedService
from models.data.service_entitlement import ServiceEntitlement
from models.data.signing_key import SigningKey
from models.data.user import User, UserAlreadyExistsError
from seed import seed_auth


@pytest.fixture(autouse=True)
def clear_auth_collections():
    for model in (User, AuthService, ConnectedService, ServiceEntitlement, SigningKey):
        model.drop_collection()


def test_user_uses_subject_id_and_argon2id_password():
    user = User.create_new('pending@example.com', 'correct horse battery staple')

    assert user.email is None
    assert user.suspended_email == 'pending@example.com'
    assert user.subject_id
    assert user.password.startswith('$argon2id$')
    assert user.check_password('correct horse battery staple')
    assert not user.check_password('wrong password')
    assert 'email_verified' not in User._fields
    assert 'services' not in User._fields
    assert 'stripe_customer_id' not in User._fields


def test_verified_email_is_derived_and_subject_id_is_unique():
    verified_at = datetime.now(pytz.utc)
    user = User(
        email='verified@example.com',
        verified_emails=[{
            'email': 'verified@example.com',
            'method': 'seed',
            'verified_at': verified_at,
        }],
    ).save()

    assert user.is_primary_email_verified()
    with pytest.raises(NotUniqueError):
        User(email='other@example.com', subject_id=user.subject_id).save()


def test_pending_email_cannot_create_duplicate_users():
    User.create_new('pending@example.com', 'first-password')

    with pytest.raises(UserAlreadyExistsError):
        User.create_new('pending@example.com', 'second-password')


def test_client_secret_is_digested_and_redirect_requires_exact_match():
    service = AuthService(
        client_id='reference',
        secret_digest=digest_client_secret('test-secret'),
        redirect_uris=['https://client.example/auth/callback'],
        allowed_scopes=['openid', 'email'],
    ).save()

    assert service.verify_secret('test-secret')
    assert not service.verify_secret('wrong-secret')
    assert service.valid_redirect('https://client.example/auth/callback')
    assert not service.valid_redirect('https://client.example/auth/callback/extra')


def test_connected_service_is_unique_per_subject_and_client():
    first = ConnectedService.connect('subject-1', 'reference')
    second = ConnectedService.connect('subject-1', 'reference')

    assert first.id == second.id
    assert ConnectedService.objects.count() == 1


def test_entitlement_projection_is_idempotent_and_monotonic():
    current_time = datetime.now(pytz.utc)
    current, applied = ServiceEntitlement.apply_projection(
        subject='subject-1',
        client_id='reference',
        plan='pro',
        billing_status='active',
        payment_event_id='event-current',
        source_event_timestamp=current_time,
    )
    duplicate, duplicate_applied = ServiceEntitlement.apply_projection(
        subject='subject-1',
        client_id='reference',
        plan='canceled',
        billing_status='canceled',
        payment_event_id='event-current',
        source_event_timestamp=current_time,
    )
    stale, stale_applied = ServiceEntitlement.apply_projection(
        subject='subject-1',
        client_id='reference',
        plan='free',
        billing_status='none',
        payment_event_id='event-stale',
        source_event_timestamp=current_time - timedelta(seconds=1),
    )

    assert applied
    assert not duplicate_applied
    assert not stale_applied
    assert duplicate.id == current.id == stale.id
    assert ServiceEntitlement.objects.get(id=current.id).billing_status == 'active'


def test_seed_is_idempotent_and_creates_active_signing_key():
    arguments = {
        'email': 'seed@example.com',
        'password': 'seed-password',
        'client_id': 'reference',
        'client_secret': 'reference-secret',
        'redirect_uri': 'https://client.example/auth/callback',
    }

    first_user, first_service, first_key = seed_auth(**arguments)
    second_user, second_service, second_key = seed_auth(**arguments)

    assert first_user.id == second_user.id
    assert first_service.id == second_service.id
    assert first_key.id == second_key.id
    assert first_user.is_primary_email_verified()
    assert first_service.verify_secret('reference-secret')
    assert first_key.private_key.startswith('-----BEGIN PRIVATE KEY-----')
    assert first_key.public_key.startswith('-----BEGIN PUBLIC KEY-----')
