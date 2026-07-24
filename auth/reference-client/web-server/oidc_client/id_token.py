# auth/reference-client/web-server/oidc_client/id_token.py
#
# Verifies auth-issued RS256 ID Tokens against a trusted issuer and JWKS.

import hmac

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
import jwt

from oidc_client.errors import AuthError


REQUIRED_CLAIMS = (
    'iss',
    'sub',
    'aud',
    'exp',
    'iat',
    'nonce',
    'auth_time',
)


class IDTokenVerifier:
    def __init__(self, client_id, issuer, leeway_seconds=60):
        if not isinstance(client_id, str) or not client_id:
            raise ValueError('client_id must be a non-empty string')
        if not isinstance(issuer, str) or not issuer:
            raise ValueError('issuer must be a non-empty string')
        if not isinstance(leeway_seconds, (int, float)) or leeway_seconds < 0:
            raise ValueError('leeway_seconds must be non-negative')

        self.client_id = client_id
        self.issuer = issuer
        self.leeway_seconds = leeway_seconds

    def verify(self, id_token, expected_nonce, jwks):
        if not isinstance(expected_nonce, str) or not expected_nonce:
            raise AuthError('invalid_id_token')

        header = self._header(id_token)
        signing_key = self._signing_key(header['kid'], jwks)
        try:
            claims = jwt.decode(
                id_token,
                signing_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=self.issuer,
                leeway=self.leeway_seconds,
                options={'require': list(REQUIRED_CLAIMS)},
            )
        except (jwt.PyJWTError, TypeError, ValueError) as error:
            raise AuthError('invalid_id_token') from error

        self._validate_identity_claims(claims, expected_nonce)
        return claims

    @staticmethod
    def _header(id_token):
        try:
            header = jwt.get_unverified_header(id_token)
        except (jwt.PyJWTError, TypeError, ValueError) as error:
            raise AuthError('invalid_id_token') from error
        if header.get('alg') != 'RS256':
            raise AuthError('invalid_id_token')
        if not isinstance(header.get('kid'), str) or not header['kid']:
            raise AuthError('invalid_id_token')
        return header

    @staticmethod
    def _signing_key(key_id, jwks):
        if not isinstance(jwks, dict) or not isinstance(jwks.get('keys'), list):
            raise AuthError('invalid_id_token')
        matching_keys = [
            key for key in jwks['keys']
            if isinstance(key, dict) and key.get('kid') == key_id
        ]
        if len(matching_keys) != 1:
            raise AuthError('invalid_id_token')

        public_jwk = matching_keys[0]
        if (
            public_jwk.get('kty') != 'RSA'
            or public_jwk.get('use') != 'sig'
            or public_jwk.get('alg') != 'RS256'
        ):
            raise AuthError('invalid_id_token')
        try:
            signing_key = jwt.PyJWK.from_dict(public_jwk).key
        except (jwt.PyJWTError, TypeError, ValueError) as error:
            raise AuthError('invalid_id_token') from error
        if not isinstance(signing_key, RSAPublicKey):
            raise AuthError('invalid_id_token')
        return signing_key

    def _validate_identity_claims(self, claims, expected_nonce):
        subject = claims.get('sub')
        nonce = claims.get('nonce')
        if not isinstance(subject, str) or not subject:
            raise AuthError('invalid_id_token')
        if not isinstance(nonce, str) or not nonce:
            raise AuthError('invalid_id_token')
        if not hmac.compare_digest(nonce, expected_nonce):
            raise AuthError('invalid_id_token')

        authorized_party = claims.get('azp')
        if isinstance(claims.get('aud'), list) and len(claims['aud']) > 1:
            if authorized_party is None:
                raise AuthError('invalid_id_token')
        if authorized_party is not None:
            if not isinstance(authorized_party, str) or not authorized_party:
                raise AuthError('invalid_id_token')
            if not hmac.compare_digest(authorized_party, self.client_id):
                raise AuthError('invalid_id_token')
