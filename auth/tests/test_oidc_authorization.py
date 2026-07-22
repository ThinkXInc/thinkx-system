# auth/tests/test_oidc_authorization.py
#
# A-3 HTTP contract tests for authorize, signin resumption, and token exchange.

import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import re
from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import pytest
import pytz

from main import app
from models.data.auth_service import AuthService
from models.data.connected_service import ConnectedService
from models.data.signing_key import SigningKey
from models.data.user import User, password_hasher
from oidc.endpoints import redis_client
from oidc.stores import pkce_s256_challenge


CLIENT_ID = 'reference'
CLIENT_SECRET = 'reference-client-secret-with-at-least-32-bytes'
REDIRECT_URI = 'https://client.example/auth/callback'
CODE_VERIFIER = 'code-verifier-value-with-more-than-forty-three-characters'


def basic_authorization():
    value = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()
    return {'Authorization': f'Basic {value}'}


def create_signing_key():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    SigningKey(
        kid='active-key',
        private_key=private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode(),
        public_key=private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode(),
        status='active',
    ).save()


def create_verified_user():
    now = datetime.now(pytz.utc)
    return User(
        email='verified@example.com',
        verified_emails=[{
            'email': 'verified@example.com',
            'method': 'seed',
            'verified_at': now,
        }],
        password=password_hasher.hash('StrongPass1'),
        last_auth_time=now,
    ).save()


def authorization_query():
    return {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid email',
        'state': 'state-value-with-enough-entropy',
        'nonce': 'nonce-value-with-enough-entropy',
        'code_challenge': pkce_s256_challenge(CODE_VERIFIER),
        'code_challenge_method': 'S256',
    }


@pytest.fixture(autouse=True)
def clear_state():
    for model in (User, AuthService, ConnectedService, SigningKey):
        model.drop_collection()
    redis_client.flushdb()
    AuthService.provision(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uris=[REDIRECT_URI],
        allowed_scopes=['openid', 'email'],
        trusted_first_party=True,
    )
    create_signing_key()


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def exchange_code(client, code, code_verifier=CODE_VERIFIER):
    return client.post(
        '/oauth/token',
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'code_verifier': code_verifier,
        },
        headers=basic_authorization(),
    )


def test_logged_in_authorize_and_token_exchange_happy_path(client, monkeypatch):
    user = create_verified_user()
    monkeypatch.setattr('oidc.endpoints.Session.user_id', lambda: str(user.id))
    monkeypatch.setattr(
        'oidc.endpoints.Session.browser_context_id', lambda: 'browser-context'
    )

    authorization = client.get('/oauth/authorize', query_string=authorization_query())

    assert authorization.status_code == 302
    callback = urlparse(authorization.headers['Location'])
    callback_values = parse_qs(callback.query)
    assert f'{callback.scheme}://{callback.netloc}{callback.path}' == REDIRECT_URI
    assert callback_values['state'] == ['state-value-with-enough-entropy']
    assert callback_values['iss'] == ['http://127.0.0.1:8020']

    token_response = exchange_code(client, callback_values['code'][0])

    assert token_response.status_code == 200
    body = token_response.get_json()
    assert body['token_type'] == 'Bearer'
    assert body['expires_in'] == 3600
    claims = jwt.decode(
        body['id_token'],
        SigningKey.get_active().public_key,
        algorithms=['RS256'],
        audience=CLIENT_ID,
        issuer='http://127.0.0.1:8020',
    )
    assert claims['sub'] == user.subject_id
    assert claims['nonce'] == 'nonce-value-with-enough-entropy'
    assert ConnectedService.objects(
        subject=user.subject_id, client_id=CLIENT_ID
    ).count() == 1
    assert exchange_code(client, callback_values['code'][0]).status_code == 400


def test_wrong_verifier_does_not_consume_code(client, monkeypatch):
    user = create_verified_user()
    monkeypatch.setattr('oidc.endpoints.Session.user_id', lambda: str(user.id))

    authorization = client.get('/oauth/authorize', query_string=authorization_query())
    code = parse_qs(urlparse(authorization.headers['Location']).query)['code'][0]

    wrong = exchange_code(client, code, 'wrong-verifier-with-enough-characters')
    correct = exchange_code(client, code)

    assert wrong.status_code == 400
    assert wrong.get_json() == {'error': 'invalid_grant'}
    assert correct.status_code == 200


def test_unauthenticated_authorization_resumes_after_signin(client):
    create_verified_user()

    authorization = client.get('/oauth/authorize', query_string=authorization_query())
    assert authorization.status_code == 302
    signin_location = authorization.headers['Location']
    assert signin_location.startswith('/signin?request_handle=')
    request_handle = parse_qs(urlparse(signin_location).query)['request_handle'][0]
    assert client.get(signin_location).status_code == 200
    signin_page = client.get(signin_location)
    csrf_token = re.search(
        r'id="csrf_token" value="([^"]+)"', signin_page.get_data(as_text=True)
    ).group(1)

    signin_response = client.post(
        '/v1/users/signin',
        json={
            'email': 'verified@example.com',
            'password': 'StrongPass1',
            'request_handle': request_handle,
            'csrf_token': csrf_token,
        },
        headers={'Origin': 'http://127.0.0.1:8020'},
    )
    assert signin_response.status_code == 200
    resume_location = signin_response.get_json()['next']

    callback_response = client.get(resume_location)
    assert callback_response.status_code == 302
    code = parse_qs(
        urlparse(callback_response.headers['Location']).query
    )['code'][0]
    assert exchange_code(client, code).status_code == 200


def test_signin_resume_rejects_missing_csrf_and_wrong_origin(client):
    create_verified_user()
    authorization = client.get('/oauth/authorize', query_string=authorization_query())
    signin_location = authorization.headers['Location']
    request_handle = parse_qs(urlparse(signin_location).query)['request_handle'][0]
    signin_page = client.get(signin_location)
    csrf_token = re.search(
        r'id="csrf_token" value="([^"]+)"', signin_page.get_data(as_text=True)
    ).group(1)
    payload = {
        'email': 'verified@example.com',
        'password': 'StrongPass1',
        'request_handle': request_handle,
    }

    missing = client.post('/v1/users/signin', json=payload)
    wrong_origin = client.post(
        '/v1/users/signin',
        json={**payload, 'csrf_token': csrf_token},
        headers={'Origin': 'https://evil.example'},
    )

    assert missing.status_code == 403
    assert wrong_origin.status_code == 403


def test_authorize_rejects_duplicate_and_unregistered_redirect_without_redirecting(
    client,
):
    duplicate_query = list(authorization_query().items())
    duplicate_query.append(('client_id', CLIENT_ID))
    duplicate = client.get('/oauth/authorize', query_string=duplicate_query)
    unregistered = client.get(
        '/oauth/authorize',
        query_string={
            **authorization_query(),
            'redirect_uri': 'https://evil.example/callback',
        },
    )

    assert duplicate.status_code == 400
    assert duplicate.get_json() == {'error': 'invalid_request'}
    assert unregistered.status_code == 400
    assert unregistered.get_json() == {'error': 'invalid_redirect_uri'}
    assert 'Location' not in unregistered.headers


def test_authorize_error_uses_registered_redirect_with_state_and_issuer(client):
    response = client.get(
        '/oauth/authorize',
        query_string={
            **authorization_query(),
            'code_challenge_method': 'plain',
        },
    )

    assert response.status_code == 302
    callback = urlparse(response.headers['Location'])
    values = parse_qs(callback.query)
    assert f'{callback.scheme}://{callback.netloc}{callback.path}' == REDIRECT_URI
    assert values == {
        'error': ['invalid_request'],
        'state': ['state-value-with-enough-entropy'],
        'iss': ['http://127.0.0.1:8020'],
    }


def test_authorize_rejects_missing_parameter_and_disallowed_scope(client):
    missing_query = authorization_query()
    del missing_query['nonce']
    missing = client.get('/oauth/authorize', query_string=missing_query)
    disallowed = client.get(
        '/oauth/authorize',
        query_string={**authorization_query(), 'scope': 'openid profile'},
    )

    assert missing.status_code == 400
    assert missing.get_json() == {'error': 'invalid_request'}
    assert parse_qs(urlparse(disallowed.headers['Location']).query) == {
        'error': ['invalid_scope'],
        'state': ['state-value-with-enough-entropy'],
        'iss': ['http://127.0.0.1:8020'],
    }


def test_two_browser_bound_requests_survive_wrong_browser_and_each_resume(
    client, monkeypatch
):
    user = create_verified_user()
    browser_context = {'value': 'browser-one'}
    current_user_id = {'value': None}
    monkeypatch.setattr(
        'oidc.endpoints.Session.browser_context_id',
        lambda: browser_context['value'],
    )
    monkeypatch.setattr(
        'oidc.endpoints.Session.user_id', lambda: current_user_id['value']
    )
    first = client.get('/oauth/authorize', query_string=authorization_query())
    second_query = {
        **authorization_query(),
        'state': 'second-state-with-enough-entropy',
        'nonce': 'second-nonce-with-enough-entropy',
    }
    second = client.get('/oauth/authorize', query_string=second_query)
    first_handle = parse_qs(urlparse(first.headers['Location']).query)[
        'request_handle'
    ][0]
    second_handle = parse_qs(urlparse(second.headers['Location']).query)[
        'request_handle'
    ][0]

    browser_context['value'] = 'browser-two'
    rejected = client.get(
        '/oauth/authorize', query_string={'request_handle': first_handle}
    )
    browser_context['value'] = 'browser-one'
    current_user_id['value'] = str(user.id)
    first_resume = client.get(
        '/oauth/authorize', query_string={'request_handle': first_handle}
    )
    second_resume = client.get(
        '/oauth/authorize', query_string={'request_handle': second_handle}
    )

    assert rejected.status_code == 400
    assert first_resume.status_code == 302
    assert second_resume.status_code == 302
    assert parse_qs(urlparse(first_resume.headers['Location']).query)['state'] == [
        'state-value-with-enough-entropy'
    ]
    assert parse_qs(urlparse(second_resume.headers['Location']).query)['state'] == [
        'second-state-with-enough-entropy'
    ]


def test_generation_change_rejects_previously_issued_code(client, monkeypatch):
    user = create_verified_user()
    monkeypatch.setattr('oidc.endpoints.Session.user_id', lambda: str(user.id))
    authorization = client.get('/oauth/authorize', query_string=authorization_query())
    code = parse_qs(urlparse(authorization.headers['Location']).query)['code'][0]
    User.objects(id=user.id).update_one(inc__auth_generation=1)

    response = exchange_code(client, code)

    assert response.status_code == 400
    assert response.get_json() == {'error': 'invalid_grant'}


def test_concurrent_code_exchange_has_exactly_one_success(client, monkeypatch):
    user = create_verified_user()
    monkeypatch.setattr('oidc.endpoints.Session.user_id', lambda: str(user.id))
    authorization = client.get('/oauth/authorize', query_string=authorization_query())
    code = parse_qs(urlparse(authorization.headers['Location']).query)['code'][0]

    def exchange_once():
        with app.test_client() as concurrent_client:
            return exchange_code(concurrent_client, code).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _index: exchange_once(), range(2)))

    assert sorted(statuses) == [200, 400]
