# auth/reference-client/tests/test_id_token_verifier.py
#
# Contract tests for strict client-side validation of auth ID Tokens.

from pathlib import Path
import sys
import time

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import pytest


WEB_SERVER = Path(__file__).resolve().parents[1] / 'web-server'
if str(WEB_SERVER) not in sys.path:
    sys.path.insert(0, str(WEB_SERVER))

from oidc_client.errors import AuthError  # noqa: E402
from oidc_client.id_token import IDTokenVerifier  # noqa: E402


CLIENT_ID = 'reference'
ISSUER = 'https://auth.example.test'
NONCE = 'nonce-value-with-enough-entropy'
TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ACTIVE_JWK = jwt.algorithms.RSAAlgorithm.to_jwk(
    TEST_PRIVATE_KEY.public_key(), as_dict=True
)
ACTIVE_JWK.update({'use': 'sig', 'alg': 'RS256', 'kid': 'active-key'})


@pytest.fixture
def verifier():
    return IDTokenVerifier(CLIENT_ID, ISSUER)


@pytest.fixture
def jwks():
    return {'keys': [dict(ACTIVE_JWK)]}


@pytest.fixture
def claims():
    now = int(time.time())
    return {
        'iss': ISSUER,
        'sub': 'subject-1',
        'aud': CLIENT_ID,
        'exp': now + 300,
        'iat': now,
        'nonce': NONCE,
        'auth_time': now - 1,
    }


def issue_id_token(claims, *, kid='active-key', algorithm='RS256'):
    headers = {'kid': kid} if kid is not None else None
    signing_key = (
        TEST_PRIVATE_KEY
        if algorithm == 'RS256'
        else 'test-hmac-secret-with-at-least-thirty-two-bytes'
    )
    return jwt.encode(claims, signing_key, algorithm=algorithm, headers=headers)


def test_valid_id_token_returns_verified_claims(verifier, jwks, claims):
    verified = verifier.verify(issue_id_token(claims), NONCE, jwks)

    assert verified == claims


@pytest.mark.parametrize(
    'missing_claim',
    ('iss', 'sub', 'aud', 'exp', 'iat', 'nonce', 'auth_time'),
)
def test_missing_required_claim_is_rejected(
    verifier, jwks, claims, missing_claim
):
    claims.pop(missing_claim)

    with pytest.raises(AuthError):
        verifier.verify(issue_id_token(claims), NONCE, jwks)


@pytest.mark.parametrize(
    ('claim_name', 'claim_value'),
    (
        ('iss', 'https://wrong-issuer.example'),
        ('aud', 'wrong-client'),
        ('nonce', 'wrong-nonce-value'),
    ),
)
def test_wrong_bound_claim_is_rejected(
    verifier, jwks, claims, claim_name, claim_value
):
    claims[claim_name] = claim_value

    with pytest.raises(AuthError):
        verifier.verify(issue_id_token(claims), NONCE, jwks)


@pytest.mark.parametrize('authorized_party', (None, 'wrong-client'))
def test_multiple_audiences_require_matching_azp(
    verifier, jwks, claims, authorized_party
):
    claims['aud'] = [CLIENT_ID, 'another-client']
    if authorized_party is not None:
        claims['azp'] = authorized_party

    with pytest.raises(AuthError):
        verifier.verify(issue_id_token(claims), NONCE, jwks)


def test_multiple_audiences_accept_matching_azp(verifier, jwks, claims):
    claims['aud'] = [CLIENT_ID, 'another-client']
    claims['azp'] = CLIENT_ID

    verified = verifier.verify(issue_id_token(claims), NONCE, jwks)

    assert verified['azp'] == CLIENT_ID


def test_present_azp_must_match_for_single_audience(verifier, jwks, claims):
    claims['azp'] = 'wrong-client'

    with pytest.raises(AuthError):
        verifier.verify(issue_id_token(claims), NONCE, jwks)


@pytest.mark.parametrize(
    ('claim_name', 'claim_value'),
    (
        ('sub', ''),
        ('sub', 123),
        ('nonce', ''),
        ('nonce', 123),
    ),
)
def test_subject_and_nonce_must_be_non_empty_strings(
    verifier, jwks, claims, claim_name, claim_value
):
    claims[claim_name] = claim_value

    with pytest.raises(AuthError):
        verifier.verify(issue_id_token(claims), NONCE, jwks)


def test_unknown_or_retired_absent_key_id_is_rejected(verifier, jwks, claims):
    with pytest.raises(AuthError):
        verifier.verify(
            issue_id_token(claims, kid='retired-key'),
            NONCE,
            jwks,
        )


def test_missing_key_id_is_rejected(verifier, jwks, claims):
    with pytest.raises(AuthError):
        verifier.verify(issue_id_token(claims, kid=None), NONCE, jwks)


@pytest.mark.parametrize(
    ('jwk_field', 'jwk_value'),
    (('kty', 'EC'), ('use', 'enc'), ('alg', 'RS384')),
)
def test_known_key_must_be_an_rs256_rsa_signature_key(
    verifier, jwks, claims, jwk_field, jwk_value
):
    jwks['keys'][0][jwk_field] = jwk_value

    with pytest.raises(AuthError):
        verifier.verify(issue_id_token(claims), NONCE, jwks)


def test_wrong_algorithm_is_rejected_before_key_use(verifier, jwks, claims):
    token = issue_id_token(claims, algorithm='HS256')

    with pytest.raises(AuthError):
        verifier.verify(token, NONCE, jwks)


def test_expired_token_is_rejected_beyond_leeway(verifier, jwks, claims):
    claims['exp'] = int(time.time()) - 120

    with pytest.raises(AuthError):
        verifier.verify(issue_id_token(claims), NONCE, jwks)
