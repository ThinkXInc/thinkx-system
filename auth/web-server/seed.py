# auth/web-server/seed.py
#
# Idempotently seeds a test user, OAuth client registration, and active RS256 signing key.

import argparse
from datetime import datetime
import os
import secrets

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import pytz

import init_mongodb  # noqa: F401
from models.data.auth_service import AuthService, digest_client_secret
from models.data.signing_key import SigningKey
from models.data.user import User, password_hasher


def generate_signing_key():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode('ascii')
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode('ascii')
    return private_pem, public_pem


def seed_auth(*, email, password, client_id, client_secret, redirect_uri):
    now = datetime.now(pytz.utc)
    user = User.objects(email=email).first()
    if not user:
        user = User(
            email=email,
            verified_emails=[{'email': email, 'method': 'seed', 'verified_at': now}],
            password=password_hasher.hash(password),
            last_auth_time=now,
        ).save()

    service = AuthService.objects(client_id=client_id).first()
    if not service:
        service = AuthService(client_id=client_id)
    service.secret_digest = digest_client_secret(client_secret)
    service.redirect_uris = [redirect_uri]
    service.allowed_scopes = ['openid', 'email']
    service.trusted_first_party = True
    service.save()

    signing_key = SigningKey.objects(status='active').first()
    if not signing_key:
        private_key, public_key = generate_signing_key()
        signing_key = SigningKey(
            kid=secrets.token_urlsafe(16),
            public_key=public_key,
            private_key=private_key,
            status='active',
        ).save()
    return user, service, signing_key


def parse_args():
    parser = argparse.ArgumentParser()
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
