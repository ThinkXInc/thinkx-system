# auth/reference-client/web-server/oidc_client/auth_client.py
#
# Bounded server-to-server HTTP client for trusted OIDC providers.

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import requests

from oidc_client.errors import AuthError, TransientAuthError
from oidc_client.provider import TrustedProvider


DEFAULT_RESPONSE_BYTE_LIMIT = 65_536
HTTP_TIMEOUT = (3.0, 10.0)
JSON_CONTENT_TYPE = 'application/json'


class AuthClient:
    """Calls only endpoints selected from immutable trusted configuration."""

    def __init__(
        self,
        *,
        providers: Mapping[str, TrustedProvider],
        client_id: str,
        client_secret: str,
        session: requests.Session | None = None,
        response_byte_limit: int = DEFAULT_RESPONSE_BYTE_LIMIT,
    ):
        if response_byte_limit < 1:
            raise ValueError('response_byte_limit must be positive')

        self._providers = dict(providers)
        if any(issuer != provider.issuer for issuer, provider in self._providers.items()):
            raise ValueError('trusted provider map key must match provider issuer')

        self._client_id = client_id
        self._client_secret = client_secret
        self._session = session if session is not None else requests.Session()
        self._response_byte_limit = response_byte_limit

    def provider(self, expected_issuer: str) -> TrustedProvider:
        """Returns an exact trusted issuer match without deriving any URL."""
        provider = self._providers.get(expected_issuer)
        if provider is None:
            raise AuthError('untrusted_issuer')
        return provider

    def exchange(
        self,
        *,
        code: str,
        redirect_uri: str,
        code_verifier: str,
        expected_issuer: str,
    ) -> dict[str, Any]:
        """Exchanges one authorization code without automatic retry."""
        provider = self.provider(expected_issuer)
        payload = self._request_json(
            'POST',
            provider.token_endpoint,
            auth=(self._client_id, self._client_secret),
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'code_verifier': code_verifier,
            },
            headers={'Accept': JSON_CONTENT_TYPE},
        )
        if (
            not isinstance(payload.get('access_token'), str)
            or not payload['access_token']
            or payload.get('token_type') != 'Bearer'
            or not isinstance(payload.get('expires_in'), int)
            or isinstance(payload.get('expires_in'), bool)
            or payload['expires_in'] <= 0
            or not isinstance(payload.get('id_token'), str)
            or not payload['id_token']
        ):
            raise AuthError('invalid_token_response')
        return payload

    def userinfo(
        self,
        *,
        access_token: str,
        expected_issuer: str,
    ) -> dict[str, Any]:
        """Fetches UserInfo with a bearer access token."""
        provider = self.provider(expected_issuer)
        payload = self._request_json(
            'GET',
            provider.userinfo_endpoint,
            headers={
                'Accept': JSON_CONTENT_TYPE,
                'Authorization': f'Bearer {access_token}',
            },
        )
        if not isinstance(payload.get('sub'), str) or not payload['sub']:
            raise AuthError('invalid_userinfo_response')
        return payload

    def fetch_jwks(self, *, expected_issuer: str) -> dict[str, Any]:
        """Fetches the trusted provider's bounded JWKS document."""
        provider = self.provider(expected_issuer)
        payload = self._request_json(
            'GET',
            provider.jwks_uri,
            headers={'Accept': JSON_CONTENT_TYPE},
        )
        if not isinstance(payload.get('keys'), list) or any(
            not isinstance(key, dict) for key in payload['keys']
        ):
            raise AuthError('invalid_jwks_response')
        return payload

    def _request_json(self, method: str, url: str, **arguments: Any) -> dict[str, Any]:
        response = None
        try:
            response = self._session.request(
                method,
                url,
                timeout=HTTP_TIMEOUT,
                allow_redirects=False,
                verify=True,
                stream=True,
                **arguments,
            )
            self._raise_for_status(response.status_code)
            self._require_json_content_type(response.headers)
            body = self._read_bounded_body(response)
        except (requests.Timeout, requests.ConnectionError):
            raise TransientAuthError('provider_unavailable') from None
        except requests.RequestException:
            raise AuthError('provider_request_failed') from None
        finally:
            if response is not None:
                response.close()

        try:
            payload = json.loads(body.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise AuthError('invalid_json_response') from None
        if not isinstance(payload, dict):
            raise AuthError('invalid_json_response')
        return payload

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code == 429 or status_code >= 500:
            raise TransientAuthError('provider_unavailable')
        if status_code < 200 or status_code >= 300:
            raise AuthError('provider_http_error')

    @staticmethod
    def _require_json_content_type(headers: Mapping[str, str]) -> None:
        content_type = headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
        if content_type != JSON_CONTENT_TYPE:
            raise AuthError('invalid_content_type')

    def _read_bounded_body(self, response: requests.Response) -> bytes:
        content_length = response.headers.get('Content-Length')
        if content_length is not None:
            try:
                parsed_content_length = int(content_length)
                if parsed_content_length < 0:
                    raise AuthError('invalid_content_length')
                if parsed_content_length > self._response_byte_limit:
                    raise AuthError('response_too_large')
            except ValueError:
                raise AuthError('invalid_content_length') from None

        body = bytearray()
        for chunk in response.iter_content(chunk_size=8_192):
            body.extend(chunk)
            if len(body) > self._response_byte_limit:
                raise AuthError('response_too_large')
        return bytes(body)
