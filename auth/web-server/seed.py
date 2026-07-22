# auth/web-server/seed.py
#
# Rerunnably resets test identity, client registration, and auth state.

import argparse
from datetime import datetime
import json
import os
import secrets

import pytz
from mongoengine import NotUniqueError
from redis import StrictRedis

import init_mongodb  # noqa: F401
from config import Config
from models.data.auth_service import AuthService, validate_client_secret
from models.data.signing_key import (
    ActiveSigningKeyNotFoundError,
    SigningKey,
)
from models.data.user import (
    User,
    UserNotFoundError,
    VerifiedEmail,
    password_hasher,
)
from oidc.keys import generate_signing_key_pair


SEED_ENVIRONMENTS = frozenset({'development', 'test', 'staging'})
AUTH_SESSION_BODY_PREFIX = Config.REDIS_SESSION_KEY_PREFIX
LEGACY_CODE_PREFIX = 'sso:auth_code:'
LEGACY_TOKEN_PREFIX = 'sso:access_token:'


def _decode(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value


def revoke_seed_user_auth_state(user_id):
    user_id = str(user_id)
    session_redis = StrictRedis(
        host=Config.REDIS_SESSION_HOST,
        port=Config.REDIS_SESSION_PORT,
        db=Config.REDIS_SESSION_DB_NUMBER,
    )
    sessions_key = f'sessions:{user_id}'
    session_ids = session_redis.smembers(sessions_key)
    pipeline = session_redis.pipeline(transaction=True)
    for session_id in session_ids:
        session_id = _decode(session_id)
        pipeline.delete(f'{AUTH_SESSION_BODY_PREFIX}{session_id}')
        pipeline.delete(f'session:{session_id}')
        pipeline.delete(f'user_id:{session_id}')
    pipeline.delete(sessions_key)
    pipeline.execute()

    sso_redis = StrictRedis(
        host=Config.REDIS_SESSION_HOST,
        port=Config.REDIS_SESSION_PORT,
        db=Config.SSO_REDIS_DB_NUMBER,
    )
    for prefix in (LEGACY_CODE_PREFIX, LEGACY_TOKEN_PREFIX):
        for key in sso_redis.scan_iter(match=f'{prefix}*'):
            raw = sso_redis.get(key)
            if raw is None:
                continue
            try:
                payload = json.loads(_decode(raw))
            except (TypeError, ValueError):
                continue
            if str(payload.get('user_id')) == user_id:
                sso_redis.delete(key)


def seed_auth(*, email, password, client_id, client_secret, redirect_uri):
    runtime_environment = os.environ.get('ENV')
    if (
        runtime_environment not in SEED_ENVIRONMENTS
        or Config.ENV != runtime_environment
    ):
        raise RuntimeError(
            'auth seed requires matching explicit non-production ENV '
            f'(Config.ENV={Config.ENV}, ENV={runtime_environment})'
        )
    if os.environ.get('AUTH_SEED_ENABLED') != '1':
        raise RuntimeError('AUTH_SEED_ENABLED=1 is required')
    validate_client_secret(client_secret)

    now = datetime.now(pytz.utc)
    user_was_existing = True
    try:
        user = User.find_user_by_email(email)
    except UserNotFoundError:
        user_was_existing = False
        try:
            user = User(
                email=email,
                verified_emails=[{
                    'email': email,
                    'method': 'seed',
                    'verified_at': now,
                }],
                password=password_hasher.hash(password),
                last_auth_time=now,
                status='active',
            ).save()
        except NotUniqueError:
            user = User.find_user_by_email(email)
            user_was_existing = True

    password_changed = not user.check_password(password)
    if password_changed:
        user.password = password_hasher.hash(password)
    if user_was_existing:
        user.auth_generation = (user.auth_generation or 0) + 1
    verified_at = next(
        (
            entry.verified_at
            for entry in user.verified_emails
            if entry.email == email
        ),
        now,
    )
    user.email = email
    user.suspended_email = None
    user.verified_emails = [VerifiedEmail(
        email=email,
        method='seed',
        verified_at=verified_at,
    )]
    user.last_auth_time = user.last_auth_time or now
    user.status = 'active'
    user.updated_at = now
    user.save()
    if user_was_existing:
        revoke_seed_user_auth_state(user.id)

    service = AuthService.provision(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uris=[redirect_uri],
        allowed_scopes=['openid', 'email'],
        trusted_first_party=True,
    )

    try:
        signing_key = SigningKey.get_active()
    except ActiveSigningKeyNotFoundError:
        private_key, public_key = generate_signing_key_pair()
        signing_key = SigningKey.ensure_active(
            kid=secrets.token_urlsafe(16),
            public_key=public_key,
            private_key=private_key,
        )
    if SigningKey.objects(status='active').count() != 1:
        raise RuntimeError('auth seed requires exactly one active signing key')
    return user, service, signing_key


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset', action='store_true', required=True)
    parser.add_argument('--email', required=True)
    parser.add_argument('--client-id', required=True)
    parser.add_argument('--redirect-uri', required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    password = os.environ.get('AUTH_SEED_USER_PASSWORD')
    client_secret = os.environ.get('AUTH_SEED_CLIENT_SECRET')
    if not password or not client_secret:
        raise RuntimeError(
            'AUTH_SEED_USER_PASSWORD and AUTH_SEED_CLIENT_SECRET are required'
        )
    seed_auth(
        email=args.email,
        password=password,
        client_id=args.client_id,
        client_secret=client_secret,
        redirect_uri=args.redirect_uri,
    )


if __name__ == '__main__':
    main()
