# auth/reference-client/tests/test_auth_client.py
#
# Contract tests for bounded trusted-provider OIDC HTTP calls.

from pathlib import Path
import json
import sys

import pytest
import requests


WEB_SERVER_ROOT = Path(__file__).resolve().parents[1] / 'web-server'
if str(WEB_SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_SERVER_ROOT))

from oidc_client.auth_client import AuthClient  # noqa: E402
from oidc_client.errors import AuthError, TransientAuthError  # noqa: E402
from oidc_client.provider import TrustedProvider  # noqa: E402


ISSUER = 'https://auth.example'
CLIENT_SECRET = 'client-secret-that-must-never-appear-in-errors'


class FakeResponse:
    def __init__(
        self,
        payload=None,
        *,
        status_code=200,
        content_type='application/json',
        chunks=None,
        extra_headers=None,
    ):
        encoded_payload = json.dumps(payload).encode() if chunks is None else b''
        self.status_code = status_code
        self.headers = {'Content-Type': content_type}
        self.headers.update(extra_headers or {})
        self.chunks = list(chunks) if chunks is not None else [encoded_payload]
        self.closed = False

    def iter_content(self, chunk_size):
        assert chunk_size == 8_192
        yield from self.chunks

    def close(self):
        self.closed = True


class RecordingSession:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def request(self, method, url, **arguments):
        self.calls.append((method, url, arguments))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture
def provider():
    return TrustedProvider(
        issuer=ISSUER,
        authorization_endpoint=f'{ISSUER}/oauth/authorize',
        token_endpoint=f'{ISSUER}/oauth/token',
        userinfo_endpoint=f'{ISSUER}/oauth/userinfo',
        jwks_uri=f'{ISSUER}/oauth/jwks',
        logout_endpoint=f'{ISSUER}/oauth/logout',
    )


def make_client(provider, session, *, response_byte_limit=65_536):
    return AuthClient(
        providers={ISSUER: provider},
        client_id='reference',
        client_secret=CLIENT_SECRET,
        session=session,
        response_byte_limit=response_byte_limit,
    )


def assert_common_http_boundaries(arguments):
    assert arguments['timeout'] == (3.0, 10.0)
    assert arguments['allow_redirects'] is False
    assert arguments['verify'] is True
    assert arguments['stream'] is True


def test_token_exchange_uses_fixed_url_http_basic_and_form_body(provider):
    response = FakeResponse({
        'access_token': 'access-token',
        'token_type': 'Bearer',
        'expires_in': 300,
        'id_token': 'signed-id-token',
    })
    session = RecordingSession(response)
    client = make_client(provider, session)

    result = client.exchange(
        code='one-time-code',
        redirect_uri='https://client.example/auth/callback',
        code_verifier='verifier',
        expected_issuer=ISSUER,
    )

    assert result['id_token'] == 'signed-id-token'
    assert len(session.calls) == 1
    method, url, arguments = session.calls[0]
    assert method == 'POST'
    assert url == provider.token_endpoint
    assert arguments['auth'] == ('reference', CLIENT_SECRET)
    assert arguments['data'] == {
        'grant_type': 'authorization_code',
        'code': 'one-time-code',
        'redirect_uri': 'https://client.example/auth/callback',
        'code_verifier': 'verifier',
    }
    assert arguments['headers'] == {'Accept': 'application/json'}
    assert 'json' not in arguments
    assert_common_http_boundaries(arguments)
    assert response.closed is True


def test_untrusted_issuer_never_sends_a_request(provider):
    session = RecordingSession()
    client = make_client(provider, session)

    with pytest.raises(AuthError, match='untrusted_issuer'):
        client.exchange(
            code='code',
            redirect_uri='https://client.example/auth/callback',
            code_verifier='verifier',
            expected_issuer='https://attacker.example',
        )

    assert session.calls == []


def test_userinfo_and_jwks_use_only_trusted_get_endpoints(provider):
    userinfo_response = FakeResponse({'sub': 'subject', 'email': 'user@example.com'})
    jwks_response = FakeResponse({'keys': [{'kid': 'active-key', 'kty': 'RSA'}]})
    session = RecordingSession(userinfo_response, jwks_response)
    client = make_client(provider, session)

    assert client.userinfo(
        access_token='access-token', expected_issuer=ISSUER
    )['sub'] == 'subject'
    assert client.fetch_jwks(expected_issuer=ISSUER)['keys'][0]['kid'] == 'active-key'

    userinfo_call, jwks_call = session.calls
    assert userinfo_call[0:2] == ('GET', provider.userinfo_endpoint)
    assert userinfo_call[2]['headers'] == {
        'Accept': 'application/json',
        'Authorization': 'Bearer access-token',
    }
    assert_common_http_boundaries(userinfo_call[2])
    assert jwks_call[0:2] == ('GET', provider.jwks_uri)
    assert jwks_call[2]['headers'] == {'Accept': 'application/json'}
    assert_common_http_boundaries(jwks_call[2])


@pytest.mark.parametrize(
    'network_error',
    [requests.Timeout('secret timeout detail'), requests.ConnectionError('secret detail')],
)
def test_network_failure_is_transient_and_is_not_retried_or_leaked(
    provider, network_error
):
    session = RecordingSession(network_error)
    client = make_client(provider, session)

    with pytest.raises(TransientAuthError) as raised:
        client.fetch_jwks(expected_issuer=ISSUER)

    assert len(session.calls) == 1
    assert 'secret detail' not in str(raised.value)
    assert raised.value.__cause__ is None


@pytest.mark.parametrize('status_code', [429, 500, 503])
def test_rate_limit_and_server_failures_are_transient(provider, status_code):
    session = RecordingSession(FakeResponse({}, status_code=status_code))
    client = make_client(provider, session)

    with pytest.raises(TransientAuthError):
        client.fetch_jwks(expected_issuer=ISSUER)

    assert len(session.calls) == 1


@pytest.mark.parametrize(
    'response,response_byte_limit',
    [
        (FakeResponse({}, status_code=302), 65_536),
        (FakeResponse({}, content_type='text/html'), 65_536),
        (FakeResponse(chunks=[b'12345']), 4),
        (
            FakeResponse(
                {}, extra_headers={'Content-Length': '65537'}
            ),
            65_536,
        ),
    ],
)
def test_redirect_non_json_and_oversize_responses_are_permanent(
    provider, response, response_byte_limit
):
    session = RecordingSession(response)
    client = make_client(
        provider, session, response_byte_limit=response_byte_limit
    )

    with pytest.raises(AuthError):
        client.fetch_jwks(expected_issuer=ISSUER)

    assert len(session.calls) == 1
    assert response.closed is True


@pytest.mark.parametrize(
    'response',
    [
        FakeResponse({}, status_code=400),
        FakeResponse(['not-an-object']),
        FakeResponse({'access_token': 'missing-other-fields'}),
    ],
)
def test_http_and_response_shape_errors_are_permanent(provider, response):
    session = RecordingSession(response)
    client = make_client(provider, session)

    with pytest.raises(AuthError):
        client.exchange(
            code='code',
            redirect_uri='https://client.example/auth/callback',
            code_verifier='verifier',
            expected_issuer=ISSUER,
        )

    assert len(session.calls) == 1
