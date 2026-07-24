# auth/reference-client/tests/test_client_transactions.py
#
# Contract tests for Redis-backed OIDC client transaction state.

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
from threading import Barrier

import fakeredis
import pytest


WEB_SERVER_ROOT = Path(__file__).resolve().parents[1] / 'web-server'
if str(WEB_SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_SERVER_ROOT))

from oidc_client.transactions import (  # noqa: E402
    ClientTransactionInvalid,
    ClientTransactionStore,
)


TTL_SECONDS = 300
BROWSER_CONTEXT_HASH = 'browser-context-hash'
EXPECTED_ISSUER = 'https://auth.example.test'


@pytest.fixture
def redis_client():
    return fakeredis.FakeStrictRedis()


@pytest.fixture
def store(redis_client):
    return ClientTransactionStore(redis_client, TTL_SECONDS)


def create_transaction(store, authorization_transaction_id):
    store.create(
        authorization_transaction_id,
        browser_context_hash=BROWSER_CONTEXT_HASH,
        return_to='/workspace',
        code_verifier='code-verifier-with-at-least-forty-three-characters',
        nonce='nonce-value-with-sufficient-entropy',
        expected_issuer=EXPECTED_ISSUER,
    )


def test_same_browser_can_hold_two_independent_transactions(store):
    create_transaction(store, 'first-authorization-transaction')
    create_transaction(store, 'second-authorization-transaction')

    first = store.claim_for_callback(
        'first-authorization-transaction',
        browser_context_hash=BROWSER_CONTEXT_HASH,
        returned_issuer=EXPECTED_ISSUER,
    )
    second = store.claim_for_callback(
        'second-authorization-transaction',
        browser_context_hash=BROWSER_CONTEXT_HASH,
        returned_issuer=EXPECTED_ISSUER,
    )

    assert (
        first.authorization_transaction_id == 'first-authorization-transaction'
    )
    assert (
        second.authorization_transaction_id == 'second-authorization-transaction'
    )
    assert first.claim_token != second.claim_token


def test_wrong_context_and_issuer_leave_pending_transaction_unchanged(
    store, redis_client
):
    authorization_transaction_id = 'bound-authorization-transaction'
    create_transaction(store, authorization_transaction_id)
    key = redis_client.keys('oidc:client_transaction:*')[0]
    pending_record = redis_client.get(key)

    with pytest.raises(ClientTransactionInvalid, match='browser context'):
        store.claim_for_callback(
            authorization_transaction_id,
            browser_context_hash='different-browser-context-hash',
            returned_issuer=EXPECTED_ISSUER,
        )
    assert redis_client.get(key) == pending_record

    with pytest.raises(ClientTransactionInvalid, match='issuer'):
        store.claim_for_callback(
            authorization_transaction_id,
            browser_context_hash=BROWSER_CONTEXT_HASH,
            returned_issuer='https://wrong-issuer.example.test',
        )
    assert redis_client.get(key) == pending_record

    claim = store.claim_for_callback(
        authorization_transaction_id,
        browser_context_hash=BROWSER_CONTEXT_HASH,
        returned_issuer=EXPECTED_ISSUER,
    )
    assert claim.return_to == '/workspace'


def test_only_one_concurrent_callback_can_claim_transaction(store):
    authorization_transaction_id = 'concurrent-authorization-transaction'
    create_transaction(store, authorization_transaction_id)
    start = Barrier(2)

    def claim():
        start.wait()
        try:
            return store.claim_for_callback(
                authorization_transaction_id,
                browser_context_hash=BROWSER_CONTEXT_HASH,
                returned_issuer=EXPECTED_ISSUER,
            )
        except ClientTransactionInvalid:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        claims = list(executor.map(lambda _index: claim(), range(2)))

    assert len([claim for claim in claims if claim is not None]) == 1


def test_processing_transaction_is_non_destructive_and_release_allows_reclaim(
    store, redis_client
):
    authorization_transaction_id = 'retryable-authorization-transaction'
    create_transaction(store, authorization_transaction_id)
    first_claim = store.claim_for_callback(
        authorization_transaction_id,
        browser_context_hash=BROWSER_CONTEXT_HASH,
        returned_issuer=EXPECTED_ISSUER,
    )
    key = redis_client.keys('oidc:client_transaction:*')[0]
    processing_record = redis_client.get(key)

    with pytest.raises(ClientTransactionInvalid, match='not pending'):
        store.claim_for_callback(
            authorization_transaction_id,
            browser_context_hash=BROWSER_CONTEXT_HASH,
            returned_issuer=EXPECTED_ISSUER,
        )
    assert redis_client.get(key) == processing_record

    store.release(authorization_transaction_id, first_claim.claim_token)
    released_record = json.loads(redis_client.get(key))
    assert released_record['status'] == 'pending'
    assert 'claim_token' not in released_record

    second_claim = store.claim_for_callback(
        authorization_transaction_id,
        browser_context_hash=BROWSER_CONTEXT_HASH,
        returned_issuer=EXPECTED_ISSUER,
    )
    assert second_claim.claim_token != first_claim.claim_token
    store.complete(authorization_transaction_id, second_claim.claim_token)
    assert redis_client.get(key) is None


def test_wrong_claim_token_does_not_release_or_complete(store, redis_client):
    authorization_transaction_id = 'owned-authorization-transaction'
    create_transaction(store, authorization_transaction_id)
    claim = store.claim_for_callback(
        authorization_transaction_id,
        browser_context_hash=BROWSER_CONTEXT_HASH,
        returned_issuer=EXPECTED_ISSUER,
    )
    key = redis_client.keys('oidc:client_transaction:*')[0]
    processing_record = redis_client.get(key)

    with pytest.raises(ClientTransactionInvalid, match='claim'):
        store.release(authorization_transaction_id, 'wrong-claim-token')
    assert redis_client.get(key) == processing_record

    with pytest.raises(ClientTransactionInvalid, match='claim'):
        store.complete(authorization_transaction_id, 'wrong-claim-token')
    assert redis_client.get(key) == processing_record

    store.release(authorization_transaction_id, claim.claim_token)
    assert json.loads(redis_client.get(key))['status'] == 'pending'


def test_raw_state_is_replaced_by_fixed_digest_key_and_record_has_ttl(
    store, redis_client
):
    authorization_transaction_id = 'raw-state-for-key-test'
    create_transaction(store, authorization_transaction_id)
    expected_key = (
        b'oidc:client_transaction:'
        b'28251ecc3135002499cacb3ab4ff4e2e7abf65ce5173371474f789c2f0caa754'
    )

    assert redis_client.keys('oidc:client_transaction:*') == [expected_key]
    assert authorization_transaction_id.encode('utf-8') not in expected_key
    assert json.loads(redis_client.get(expected_key))['status'] == 'pending'
    assert 0 < redis_client.ttl(expected_key) <= TTL_SECONDS
