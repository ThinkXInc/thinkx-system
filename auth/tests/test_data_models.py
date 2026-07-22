# auth/tests/test_data_models.py
#
# A-1 tests for auth identity, client registration, billing projection, and seed data.

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
from threading import Barrier

from mongoengine import NotUniqueError, ValidationError
import pytest
import pytz
from redis import StrictRedis

from models.data.auth_service import AuthService, digest_client_secret
from models.data.connected_service import ConnectedService
from models.data.service_entitlement import (
    PaymentEventConflictError,
    ServiceEntitlement,
)
from models.data.signing_key import ActiveSigningKeyNotFoundError, SigningKey
from models.data.user import User, UserAlreadyExistsError
from models.data.verification_challenge import VerificationChallenge
from config import Config
from seed import (
    AUTH_SESSION_BODY_PREFIX,
    LEGACY_CODE_PREFIX,
    LEGACY_TOKEN_PREFIX,
    seed_auth,
)


TEST_CLIENT_SECRET = 'test-only-client-secret-with-32-bytes-minimum'


@pytest.fixture(autouse=True)
def clear_auth_collections():
    for model in (
        User,
        AuthService,
        ConnectedService,
        ServiceEntitlement,
        SigningKey,
        VerificationChallenge,
    ):
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


def test_verified_and_pending_email_share_one_uniqueness_boundary():
    User(
        email='same@example.com',
        verified_emails=[{
            'email': 'same@example.com',
            'method': 'seed',
            'verified_at': datetime.now(pytz.utc),
        }],
    ).save()

    with pytest.raises(UserAlreadyExistsError):
        User.create_new('same@example.com', 'second-password')

    pending = User.create_new('pending@example.com', 'pending-password')
    with pytest.raises(UserAlreadyExistsError):
        User.create_new_google_oauth(
            email='pending@example.com',
            google_id='different-google-subject',
        )

    pending.email = 'old@example.com'
    pending.suspended_email = 'new@example.com'
    pending.save()
    assert pending.email_identity_keys == ['old@example.com', 'new@example.com']
    with pytest.raises(UserAlreadyExistsError):
        User.create_new('new@example.com', 'other-password')


def test_google_identity_and_verified_email_entries_are_schema_checked():
    User.create_new_google_oauth(
        email='first@example.com',
        google_id='google-subject',
    )

    with pytest.raises(UserAlreadyExistsError):
        User.create_new_google_oauth(
            email='second@example.com',
            google_id='google-subject',
        )
    with pytest.raises(ValidationError):
        User(
            email='malformed@example.com',
            verified_emails=[{
                'email': 'malformed@example.com',
                'method': 'seed',
            }],
        ).save()


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


def test_connected_service_is_idempotent_under_concurrent_first_use():
    workers = 8
    barrier = Barrier(workers)
    ConnectedService.ensure_indexes()

    def connect_once():
        barrier.wait()
        return ConnectedService.connect('subject-concurrent', 'reference').id

    with ThreadPoolExecutor(max_workers=workers) as executor:
        ids = list(executor.map(lambda _index: connect_once(), range(workers)))

    assert len(set(ids)) == 1
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
        plan='pro',
        billing_status='active',
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

    with pytest.raises(PaymentEventConflictError):
        ServiceEntitlement.apply_projection(
            subject='subject-1',
            client_id='reference',
            plan='canceled',
            billing_status='canceled',
            payment_event_id='event-current',
            source_event_timestamp=current_time,
        )


def test_equal_timestamp_event_applies_but_reused_event_id_fails_loudly():
    event_time = datetime.now(pytz.utc)
    ServiceEntitlement.apply_projection(
        subject='subject-1',
        client_id='reference',
        plan='free',
        billing_status='none',
        payment_event_id='event-a',
        source_event_timestamp=event_time,
    )
    current, applied = ServiceEntitlement.apply_projection(
        subject='subject-1',
        client_id='reference',
        plan='pro',
        billing_status='active',
        payment_event_id='event-b',
        source_event_timestamp=event_time,
    )

    assert applied
    assert current.payment_event_id == 'event-b'
    replay, replay_applied = ServiceEntitlement.apply_projection(
        subject='subject-1',
        client_id='reference',
        plan='free',
        billing_status='none',
        payment_event_id='event-a',
        source_event_timestamp=event_time,
    )
    assert not replay_applied
    assert replay.payment_event_id == 'event-b'
    with pytest.raises(PaymentEventConflictError):
        ServiceEntitlement.apply_projection(
            subject='different-subject',
            client_id='reference',
            plan='pro',
            billing_status='active',
            payment_event_id='event-b',
            source_event_timestamp=event_time,
        )
    with pytest.raises(ValidationError):
        ServiceEntitlement.apply_projection(
            subject='subject-1',
            client_id='reference',
            plan='pro',
            billing_status='arbitrary',
            payment_event_id='event-invalid-status',
            source_event_timestamp=event_time + timedelta(seconds=1),
        )


def test_entitlement_projection_stays_monotonic_under_concurrent_updates():
    base_time = datetime.now(pytz.utc)
    ServiceEntitlement.apply_projection(
        subject='subject-concurrent',
        client_id='reference',
        plan='free',
        billing_status='none',
        payment_event_id='event-base',
        source_event_timestamp=base_time,
    )
    barrier = Barrier(2)

    def apply(event_id, timestamp, status):
        barrier.wait()
        return ServiceEntitlement.apply_projection(
            subject='subject-concurrent',
            client_id='reference',
            plan='pro',
            billing_status=status,
            payment_event_id=event_id,
            source_event_timestamp=timestamp,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        older = executor.submit(
            apply,
            'event-older',
            base_time + timedelta(seconds=1),
            'past_due',
        )
        newer = executor.submit(
            apply,
            'event-newer',
            base_time + timedelta(seconds=2),
            'active',
        )
        older.result()
        newer.result()

    current = ServiceEntitlement.objects.get(
        subject='subject-concurrent', client_id='reference'
    )
    assert current.payment_event_id == 'event-newer'
    assert current.billing_status == 'active'


def test_concurrent_duplicate_entitlement_event_is_applied_once():
    workers = 8
    barrier = Barrier(workers)
    ServiceEntitlement.ensure_indexes()
    event_time = datetime.now(pytz.utc)

    def apply_once():
        barrier.wait()
        return ServiceEntitlement.apply_projection(
            subject='subject-duplicate',
            client_id='reference',
            plan='pro',
            billing_status='active',
            payment_event_id='event-duplicate',
            source_event_timestamp=event_time,
        )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda _index: apply_once(), range(workers)))

    assert sum(applied for _entitlement, applied in results) == 1
    assert len({entitlement.id for entitlement, _applied in results}) == 1
    assert ServiceEntitlement.objects.count() == 1


def test_only_one_signing_key_can_be_active_or_next():
    with pytest.raises(ActiveSigningKeyNotFoundError):
        SigningKey.get_active()

    SigningKey(
        kid='active-one',
        public_key='public-one',
        private_key='private-one',
        status='active',
    ).save()

    with pytest.raises(NotUniqueError):
        SigningKey(
            kid='active-two',
            public_key='public-two',
            private_key='private-two',
            status='active',
        ).save()

    SigningKey(
        kid='next-one',
        public_key='public-next-one',
        private_key='private-next-one',
        status='next',
    ).save()
    with pytest.raises(NotUniqueError):
        SigningKey(
            kid='next-two',
            public_key='public-next-two',
            private_key='private-next-two',
            status='next',
        ).save()


def test_verification_challenge_rejects_invalid_shape():
    with pytest.raises(ValidationError):
        VerificationChallenge(
            purpose='unknown',
            channel='email',
            code_hash='hash',
            destination='user@example.com',
            expires_at=datetime.now(pytz.utc) + timedelta(hours=1),
        ).save()
    with pytest.raises(ValidationError):
        VerificationChallenge(
            purpose='signup',
            channel='email',
            code_hash='hash',
            destination='user@example.com',
            expires_at=datetime.now(pytz.utc) + timedelta(hours=1),
            attempts=-1,
        ).save()


def test_seed_is_rerunnable_and_creates_active_signing_key(monkeypatch):
    monkeypatch.setattr(Config, 'ENV', 'staging')
    monkeypatch.setenv('ENV', 'staging')
    monkeypatch.setenv('AUTH_SEED_ENABLED', '1')
    arguments = {
        'email': 'seed@example.com',
        'password': 'seed-password',
        'client_id': 'reference',
        'client_secret': TEST_CLIENT_SECRET,
        'redirect_uri': 'https://client.example/auth/callback',
    }

    first_user, first_service, first_key = seed_auth(**arguments)
    second_user, second_service, second_key = seed_auth(**arguments)

    assert first_user.id == second_user.id
    assert first_service.id == second_service.id
    assert first_key.id == second_key.id
    assert first_user.is_primary_email_verified()
    assert first_service.verify_secret(TEST_CLIENT_SECRET)
    assert first_key.private_key.startswith('-----BEGIN PRIVATE KEY-----')
    assert first_key.public_key.startswith('-----BEGIN PUBLIC KEY-----')


def test_seed_resets_existing_test_user_and_client_credentials(monkeypatch):
    monkeypatch.setattr(Config, 'ENV', 'staging')
    monkeypatch.setenv('ENV', 'staging')
    monkeypatch.setenv('AUTH_SEED_ENABLED', '1')
    user, service, signing_key = seed_auth(
        email='seed@example.com',
        password='initial-password',
        client_id='reference',
        client_secret=TEST_CLIENT_SECRET,
        redirect_uri='https://client.example/old-callback',
    )
    previous_generation = user.auth_generation
    replacement_secret = 'replacement-test-client-secret-over-32-bytes'
    session_redis = StrictRedis(db=Config.REDIS_SESSION_DB_NUMBER)
    session_redis.sadd(f'sessions:{user.id}', 'seed-session')
    session_redis.set(f'{AUTH_SESSION_BODY_PREFIX}seed-session', 'body')
    session_redis.set('session:seed-session', 'placeholder')
    session_redis.set('user_id:seed-session', str(user.id))
    sso_redis = StrictRedis(db=Config.SSO_REDIS_DB_NUMBER)
    payload = json.dumps({'user_id': str(user.id), 'service_id': 'reference'})
    sso_redis.set(f'{LEGACY_CODE_PREFIX}seed-code', payload)
    sso_redis.set(f'{LEGACY_TOKEN_PREFIX}seed-token', payload)

    reset_user, reset_service, reset_key = seed_auth(
        email='seed@example.com',
        password='replacement-password',
        client_id='reference',
        client_secret=replacement_secret,
        redirect_uri='https://client.example/new-callback',
    )

    assert reset_user.id == user.id
    assert reset_user.check_password('replacement-password')
    assert not reset_user.check_password('initial-password')
    assert reset_user.auth_generation == previous_generation + 1
    assert reset_user.is_primary_email_verified()
    assert reset_user.status == 'active'
    assert reset_service.id == service.id
    assert reset_service.verify_secret(replacement_secret)
    assert not reset_service.verify_secret(TEST_CLIENT_SECRET)
    assert reset_service.redirect_uris == ['https://client.example/new-callback']
    assert reset_key.id == signing_key.id
    assert not session_redis.exists(f'sessions:{user.id}')
    assert not session_redis.exists(f'{AUTH_SESSION_BODY_PREFIX}seed-session')
    assert not session_redis.exists('session:seed-session')
    assert not session_redis.exists('user_id:seed-session')
    assert not sso_redis.exists(f'{LEGACY_CODE_PREFIX}seed-code')
    assert not sso_redis.exists(f'{LEGACY_TOKEN_PREFIX}seed-token')


def test_seed_rejects_production_and_short_client_secret_before_writing(
    monkeypatch,
):
    arguments = {
        'email': 'seed@example.com',
        'password': 'seed-password',
        'client_id': 'reference',
        'client_secret': TEST_CLIENT_SECRET,
        'redirect_uri': 'https://client.example/auth/callback',
    }

    monkeypatch.setattr(Config, 'ENV', 'staging')
    monkeypatch.setenv('ENV', 'staging')
    monkeypatch.delenv('AUTH_SEED_ENABLED', raising=False)
    with pytest.raises(RuntimeError, match='AUTH_SEED_ENABLED'):
        seed_auth(**arguments)

    monkeypatch.setenv('AUTH_SEED_ENABLED', '1')
    monkeypatch.setattr(Config, 'ENV', 'production')
    monkeypatch.setenv('ENV', 'production')
    with pytest.raises(RuntimeError, match='production'):
        seed_auth(**arguments)
    monkeypatch.setattr(Config, 'ENV', 'unexpected')
    monkeypatch.setenv('ENV', 'unexpected')
    with pytest.raises(RuntimeError, match='unexpected'):
        seed_auth(**arguments)
    monkeypatch.setattr(Config, 'ENV', 'staging')
    monkeypatch.setenv('ENV', 'development')
    with pytest.raises(RuntimeError, match='Config.ENV=staging'):
        seed_auth(**arguments)
    monkeypatch.setenv('ENV', 'staging')
    with pytest.raises(ValueError, match='32 bytes'):
        seed_auth(**{**arguments, 'client_secret': 'too-short'})

    assert User.objects.count() == 0
    assert AuthService.objects.count() == 0
    assert SigningKey.objects.count() == 0
