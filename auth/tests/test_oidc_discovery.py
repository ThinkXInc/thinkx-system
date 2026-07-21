# auth/tests/test_oidc_discovery.py
#
# A-2 contract tests for RS256 ID Tokens, JWKS, and provider metadata.

from datetime import datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import pytest
import pytz

from config import Config
from main import app
from models.data.signing_key import SigningKey
from oidc.id_token import IDTokenIssuer


def rsa_key_pair():
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


@pytest.fixture(autouse=True)
def clear_signing_keys():
    SigningKey.drop_collection()


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def create_signing_key(kid, status):
    private_key, public_key = rsa_key_pair()
    return SigningKey(
        kid=kid,
        public_key=public_key,
        private_key=private_key,
        status=status,
    ).save()


def test_metadata_describes_the_supported_provider_contract(client):
    response = client.get('/.well-known/openid-configuration')

    assert response.status_code == 200
    assert response.get_json() == {
        'issuer': Config.AUTH_PUBLIC_BASE_URL,
        'authorization_endpoint': f'{Config.AUTH_PUBLIC_BASE_URL}/oauth/authorize',
        'token_endpoint': f'{Config.AUTH_PUBLIC_BASE_URL}/oauth/token',
        'userinfo_endpoint': f'{Config.AUTH_PUBLIC_BASE_URL}/oauth/userinfo',
        'jwks_uri': f'{Config.AUTH_PUBLIC_BASE_URL}/oauth/jwks',
        'end_session_endpoint': f'{Config.AUTH_PUBLIC_BASE_URL}/oauth/logout',
        'response_types_supported': ['code'],
        'subject_types_supported': ['public'],
        'id_token_signing_alg_values_supported': ['RS256'],
        'scopes_supported': ['openid', 'email'],
        'token_endpoint_auth_methods_supported': ['client_secret_basic'],
        'code_challenge_methods_supported': ['S256'],
    }


def test_jwks_publishes_non_retired_public_keys_without_private_material(client):
    create_signing_key('active-key', 'active')
    create_signing_key('retiring-key', 'retiring')
    create_signing_key('retired-key', 'retired')

    response = client.get('/oauth/jwks')

    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'public, max-age=300'
    keys = response.get_json()['keys']
    assert {key['kid'] for key in keys} == {'active-key', 'retiring-key'}
    assert all(set(key) == {'kty', 'use', 'alg', 'kid', 'n', 'e'} for key in keys)
    assert all(key['kty'] == 'RSA' and key['alg'] == 'RS256' for key in keys)
    assert 'PRIVATE KEY' not in response.get_data(as_text=True)


def test_id_token_has_required_claims_and_active_key_id():
    signing_key = create_signing_key('active-key', 'active')
    now = datetime.now(pytz.utc)
    auth_time = now
    issuer = IDTokenIssuer(
        issuer=Config.AUTH_PUBLIC_BASE_URL,
        lifetime_seconds=Config.OIDC_ID_TOKEN_TTL_SEC,
    )

    token = issuer.issue(
        subject='subject-1',
        audience='reference',
        nonce='nonce-1',
        auth_time=auth_time,
        now=now,
    )

    assert jwt.get_unverified_header(token) == {
        'alg': 'RS256',
        'kid': 'active-key',
        'typ': 'JWT',
    }
    claims = jwt.decode(
        token,
        signing_key.public_key,
        algorithms=['RS256'],
        audience='reference',
        issuer=Config.AUTH_PUBLIC_BASE_URL,
        options={'require': ['iss', 'sub', 'aud', 'exp', 'iat', 'nonce', 'auth_time']},
    )
    assert claims == {
        'iss': Config.AUTH_PUBLIC_BASE_URL,
        'sub': 'subject-1',
        'aud': 'reference',
        'exp': int(now.timestamp()) + Config.OIDC_ID_TOKEN_TTL_SEC,
        'iat': int(now.timestamp()),
        'nonce': 'nonce-1',
        'auth_time': int(auth_time.timestamp()),
    }


def test_id_token_is_verifiable_with_the_published_jwk(client):
    create_signing_key('active-key', 'active')
    now = datetime.now(pytz.utc)
    token = IDTokenIssuer(
        issuer=Config.AUTH_PUBLIC_BASE_URL,
        lifetime_seconds=Config.OIDC_ID_TOKEN_TTL_SEC,
    ).issue(
        subject='subject-1',
        audience='reference',
        nonce='nonce-1',
        auth_time=now,
        now=now,
    )
    published_key = client.get('/oauth/jwks').get_json()['keys'][0]

    claims = jwt.decode(
        token,
        jwt.PyJWK.from_dict(published_key).key,
        algorithms=['RS256'],
        audience='reference',
        issuer=Config.AUTH_PUBLIC_BASE_URL,
    )

    assert jwt.get_unverified_header(token)['kid'] == published_key['kid']
    assert claims['sub'] == 'subject-1'
