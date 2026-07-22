# auth/tests/test_key_rotation.py
#
# A-8 tests for deterministic overlap-based signing-key rotation.

from datetime import datetime, timedelta

import pytest
import pytz
import jwt

import init_mongodb  # noqa: F401
from models.data.signing_key import SigningKey
from oidc.id_token import IDTokenIssuer, public_jwks
from oidc.key_rotation import (
    RotationNotReadyError,
    activate_rotation,
    prepare_rotation,
    retire_old_keys,
)
from oidc.keys import generate_signing_key_pair


OVERLAP_SECONDS = 3600


@pytest.fixture(autouse=True)
def clear_keys():
    SigningKey.drop_collection()


def create_active_key(now):
    private_key, public_key = generate_signing_key_pair()
    return SigningKey(
        kid='old-active',
        public_key=public_key,
        private_key=private_key,
        status='active',
        status_changed_at=now,
    ).save()


def test_prepare_is_idempotent_and_publishes_next_key():
    now = datetime.now(pytz.utc)
    create_active_key(now)

    first, created = prepare_rotation(now=now)
    second, created_again = prepare_rotation(now=now + timedelta(minutes=1))

    assert created
    assert not created_again
    assert first.id == second.id
    assert {key['kid'] for key in public_jwks()['keys']} == {
        'old-active', first.kid
    }


def test_activation_requires_overlap_and_switches_signing_key():
    now = datetime.now(pytz.utc)
    old_key = create_active_key(now)
    next_key, _created = prepare_rotation(now=now)

    with pytest.raises(RotationNotReadyError):
        activate_rotation(overlap_seconds=OVERLAP_SECONDS, now=now)
    activated, changed = activate_rotation(
        overlap_seconds=OVERLAP_SECONDS,
        now=now + timedelta(seconds=OVERLAP_SECONDS),
    )

    assert changed
    assert activated.id == next_key.id
    assert SigningKey.objects.get(id=old_key.id).status == 'retiring'
    issuer = IDTokenIssuer(
        issuer='https://auth.example',
        lifetime_seconds=600,
    )
    token = issuer.issue(
        subject='subject-1', audience='reference', nonce='nonce-value',
        auth_time=now, now=now,
    )
    assert jwt.get_unverified_header(token)['kid'] == next_key.kid


def test_retire_waits_second_overlap_and_removes_old_jwk():
    now = datetime.now(pytz.utc)
    old_key = create_active_key(now)
    issuer = IDTokenIssuer(issuer='https://auth.example', lifetime_seconds=7200)
    old_token = issuer.issue(
        subject='subject-1', audience='reference', nonce='old-nonce',
        auth_time=now, now=now,
    )
    next_key, _created = prepare_rotation(now=now)
    activation_time = now + timedelta(seconds=OVERLAP_SECONDS)
    activate_rotation(overlap_seconds=OVERLAP_SECONDS, now=activation_time)
    new_token = issuer.issue(
        subject='subject-1', audience='reference', nonce='new-nonce',
        auth_time=now, now=activation_time,
    )

    assert jwt.decode(
        old_token, old_key.public_key, algorithms=['RS256'],
        audience='reference', issuer='https://auth.example',
        options={'verify_exp': False, 'verify_iat': False},
    )['nonce'] == 'old-nonce'
    assert jwt.decode(
        new_token, next_key.public_key, algorithms=['RS256'],
        audience='reference', issuer='https://auth.example',
        options={'verify_exp': False, 'verify_iat': False},
    )['nonce'] == 'new-nonce'

    with pytest.raises(RotationNotReadyError):
        retire_old_keys(overlap_seconds=OVERLAP_SECONDS, now=activation_time)
    retired = retire_old_keys(
        overlap_seconds=OVERLAP_SECONDS,
        now=activation_time + timedelta(seconds=OVERLAP_SECONDS),
    )

    assert [key.id for key in retired] == [old_key.id]
    published_keys = {
        key['kid']: key for key in public_jwks()['keys']
    }
    assert set(published_keys) == {next_key.kid}
    assert jwt.get_unverified_header(old_token)['kid'] not in published_keys


def test_activate_recovers_when_old_active_was_already_marked_retiring():
    now = datetime.now(pytz.utc)
    old_key = create_active_key(now)
    next_key, _created = prepare_rotation(now=now)
    old_key.status = 'retiring'
    old_key.status_changed_at = now + timedelta(seconds=OVERLAP_SECONDS)
    old_key.save()

    activated, changed = activate_rotation(
        overlap_seconds=OVERLAP_SECONDS,
        now=now + timedelta(seconds=OVERLAP_SECONDS),
    )

    assert changed
    assert activated.id == next_key.id
    assert SigningKey.get_active().id == next_key.id


def test_rotation_uses_created_at_for_keys_saved_before_status_timestamps():
    now = datetime.now(pytz.utc)
    create_active_key(now)
    next_key, _created = prepare_rotation(now=now)
    SigningKey._get_collection().update_one(
        {'_id': next_key.id},
        {'$unset': {'status_changed_at': ''}},
    )

    activated, changed = activate_rotation(
        overlap_seconds=OVERLAP_SECONDS,
        now=now + timedelta(seconds=OVERLAP_SECONDS),
    )

    assert changed
    assert activated.id == next_key.id
