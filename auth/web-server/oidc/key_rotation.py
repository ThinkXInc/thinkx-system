# auth/web-server/oidc/key_rotation.py
#
# Deterministic prepare/activate/retire state machine for signing-key rotation.

from datetime import datetime, timedelta
import secrets

import pytz
from mongoengine import NotUniqueError

from models.data.signing_key import SigningKey
from oidc.keys import generate_signing_key_pair


class RotationNotReadyError(RuntimeError):
    pass


def as_utc(timestamp):
    if timestamp.tzinfo is None:
        return pytz.utc.localize(timestamp)
    return timestamp.astimezone(pytz.utc)


def prepare_rotation(now=None):
    existing = SigningKey.objects(status='next').first()
    if existing:
        return existing, False
    now = now or datetime.now(pytz.utc)
    private_key, public_key = generate_signing_key_pair()
    try:
        key = SigningKey(
            kid=secrets.token_urlsafe(16),
            public_key=public_key,
            private_key=private_key,
            status='next',
            created_at=now,
            status_changed_at=now,
        ).save()
    except NotUniqueError:
        return SigningKey.objects.get(status='next'), False
    return key, True


def activate_rotation(*, overlap_seconds, now=None):
    now = now or datetime.now(pytz.utc)
    next_key = SigningKey.objects(status='next').first()
    if not next_key:
        active = SigningKey.get_active()
        return active, False
    status_changed_at = next_key.status_changed_at or next_key.created_at
    ready_at = as_utc(status_changed_at) + timedelta(
        seconds=overlap_seconds
    )
    if now < ready_at:
        raise RotationNotReadyError('next key has not completed publication overlap')

    active = SigningKey.objects(status='active').first()
    if active:
        active.status = 'retiring'
        active.status_changed_at = now
        active.save()
    next_key.status = 'active'
    next_key.status_changed_at = now
    next_key.save()
    return next_key, True


def retire_old_keys(*, overlap_seconds, now=None):
    now = now or datetime.now(pytz.utc)
    retired = []
    for key in SigningKey.objects(status='retiring'):
        status_changed_at = key.status_changed_at or key.created_at
        ready_at = as_utc(status_changed_at) + timedelta(
            seconds=overlap_seconds
        )
        if now < ready_at:
            continue
        key.status = 'retired'
        key.status_changed_at = now
        key.save()
        retired.append(key)
    if not retired and SigningKey.objects(status='retiring').count():
        raise RotationNotReadyError('retiring keys have not completed overlap')
    return retired
