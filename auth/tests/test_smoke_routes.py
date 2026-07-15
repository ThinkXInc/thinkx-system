# Flask test client によるルートのスモーク。起動可能な足場が「リクエストを捌ける」ことの最小確認。
# 期待値は推測で書かない。初回実行で実測値を tests/golden/smoke_routes.json へ凍結し、
# 以後はそのゴールデンと突き合わせる (D-4: 機械オラクルが挙動判定の主体)。
# 挙動を変えたいときはゴールデンを意図的に更新する (ここでは行わない)。
#
# 対象 (PROTOCOL.md v1 の現挙動):
#   GET  /healthcheck                                    -> 200
#   GET  /authorize  未登録 service_id                    -> 403 (sso_error 画面。open redirect しない)
#   GET  /authorize  登録済 service_id + 不正 redirect_uri -> 400 (sso_error 画面)
#   POST /v1/token/exchange  Content-Type 不正            -> 415 系 (content_type_check_json)

import json
import os

import pytest

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), 'golden')
GOLDEN_PATH = os.path.join(GOLDEN_DIR, 'smoke_routes.json')


@pytest.fixture(scope='module')
def client():
    from main import app
    app.config.update(TESTING=True)
    return app.test_client()


def _observe(resp):
    """レスポンスから決定的な観測値だけを取り出す (HTML 本文は凍結しない)。"""
    return {
        'status': resp.status_code,
        'content_type': resp.headers.get('Content-Type', '').split(';')[0].strip(),
        'json': resp.get_json(silent=True),
    }


def _observe_all(client):
    return {
        'healthcheck': _observe(client.get('/healthcheck')),
        'authorize_unknown_service': _observe(client.get('/authorize', query_string={
            'service_id': 'no_such_service',
            'redirect_uri': 'https://quantz.example.com/auth/callback',
            'state': 'xyz',
        })),
        'authorize_registered_service_bad_redirect_uri': _observe(client.get('/authorize', query_string={
            'service_id': 'quantz',
            'redirect_uri': 'https://evil.example.com/x',
            'state': 'xyz',
        })),
        'token_exchange_bad_content_type': _observe(client.post(
            '/v1/token/exchange', data='auth_code=x', content_type='text/plain')),
    }


def test_smoke_routes_match_frozen_golden(client):
    observed = _observe_all(client)

    if not os.path.exists(GOLDEN_PATH):
        os.makedirs(GOLDEN_DIR, exist_ok=True)
        with open(GOLDEN_PATH, 'w') as f:
            json.dump(observed, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.write('\n')
        pytest.skip('golden frozen on first run; re-run to verify against it')

    with open(GOLDEN_PATH) as f:
        golden = json.load(f)
    assert observed == golden
