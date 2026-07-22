# auth/web-server/oidc/id_token.py
#
# RS256 ID Token issuance and public RSA JWK conversion.

import base64
from datetime import datetime, timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
import jwt
import pytz

from models.data.signing_key import SigningKey


def base64url_uint(value):
    byte_length = max(1, (value.bit_length() + 7) // 8)
    encoded = base64.urlsafe_b64encode(value.to_bytes(byte_length, 'big'))
    return encoded.rstrip(b'=').decode('ascii')


def public_jwk(signing_key):
    public_key = serialization.load_pem_public_key(
        signing_key.public_key.encode('ascii')
    )
    if not isinstance(public_key, RSAPublicKey):
        raise ValueError('SigningKey public_key must be RSA')
    numbers = public_key.public_numbers()
    return {
        'kty': 'RSA',
        'use': 'sig',
        'alg': 'RS256',
        'kid': signing_key.kid,
        'n': base64url_uint(numbers.n),
        'e': base64url_uint(numbers.e),
    }


def public_jwks():
    keys = SigningKey.objects(status__ne='retired').order_by('created_at', 'kid')
    return {'keys': [public_jwk(key) for key in keys]}


class IDTokenIssuer:
    def __init__(self, *, issuer, lifetime_seconds):
        self.issuer = issuer
        self.lifetime_seconds = lifetime_seconds

    def issue(self, *, subject, audience, nonce, auth_time, now=None):
        signing_key = SigningKey.get_active()
        issued_at = now or datetime.now(pytz.utc)
        expires_at = issued_at + timedelta(seconds=self.lifetime_seconds)
        claims = {
            'iss': self.issuer,
            'sub': subject,
            'aud': audience,
            'exp': int(expires_at.timestamp()),
            'iat': int(issued_at.timestamp()),
            'nonce': nonce,
            'auth_time': int(auth_time.timestamp()),
        }
        return jwt.encode(
            claims,
            signing_key.private_key,
            algorithm='RS256',
            headers={'kid': signing_key.kid},
        )
