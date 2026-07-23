# auth/reference-client/web-server/oidc_client/transactions.py
#
# Redis-backed client transaction state for the OIDC callback flow.

from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets

from redis.exceptions import WatchError


CLIENT_TRANSACTION_KEY_PREFIX = 'oidc:client_transaction:'


class ClientTransactionError(Exception):
    """Base error for client transaction operations."""


class ClientTransactionExists(ClientTransactionError):
    """The authorization transaction identifier is already in use."""


class ClientTransactionInvalid(ClientTransactionError):
    """The transaction is missing, mismatched, or not in the required state."""


@dataclass(frozen=True)
class ClientTransactionClaim:
    authorization_transaction_id: str
    return_to: str
    code_verifier: str
    nonce: str
    expected_issuer: str
    claim_token: str


class ClientTransactionStore:
    def __init__(self, redis_client, ttl_seconds):
        if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool):
            raise ValueError('ttl_seconds must be an integer')
        if ttl_seconds <= 0:
            raise ValueError('ttl_seconds must be positive')
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _key(authorization_transaction_id):
        if not isinstance(authorization_transaction_id, str):
            raise ClientTransactionInvalid('transaction identifier must be text')
        if not authorization_transaction_id:
            raise ClientTransactionInvalid('transaction identifier is empty')
        identifier_digest = hashlib.sha256(
            authorization_transaction_id.encode('utf-8')
        ).hexdigest()
        return f'{CLIENT_TRANSACTION_KEY_PREFIX}{identifier_digest}'

    @staticmethod
    def _encode(record):
        return json.dumps(record, separators=(',', ':'), sort_keys=True)

    @staticmethod
    def _decode(encoded_record):
        try:
            record = json.loads(encoded_record)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ClientTransactionInvalid(
                'transaction record is invalid'
            ) from error
        if not isinstance(record, dict):
            raise ClientTransactionInvalid('transaction record is invalid')
        return record

    @staticmethod
    def _required_text(record, name):
        value = record.get(name)
        if not isinstance(value, str) or not value:
            raise ClientTransactionInvalid('transaction record is invalid')
        return value

    @classmethod
    def _processing_record(cls, record, claim_token):
        if record.get('status') != 'processing':
            raise ClientTransactionInvalid('transaction is not processing')
        stored_claim_token = cls._required_text(record, 'claim_token')
        if not isinstance(claim_token, str) or not hmac.compare_digest(
            stored_claim_token, claim_token
        ):
            raise ClientTransactionInvalid('transaction claim does not match')
        return record

    def create(
        self,
        authorization_transaction_id,
        *,
        browser_context_hash,
        return_to,
        code_verifier,
        nonce,
        expected_issuer,
    ):
        record = {
            'browser_context_hash': browser_context_hash,
            'return_to': return_to,
            'code_verifier': code_verifier,
            'nonce': nonce,
            'expected_issuer': expected_issuer,
            'status': 'pending',
        }
        for name in (
            'browser_context_hash',
            'return_to',
            'code_verifier',
            'nonce',
            'expected_issuer',
        ):
            self._required_text(record, name)
        created = self._redis.set(
            self._key(authorization_transaction_id),
            self._encode(record),
            ex=self._ttl_seconds,
            nx=True,
        )
        if not created:
            raise ClientTransactionExists('transaction identifier already exists')

    def claim_for_callback(
        self,
        authorization_transaction_id,
        *,
        browser_context_hash,
        returned_issuer,
    ):
        key = self._key(authorization_transaction_id)
        while True:
            try:
                with self._redis.pipeline() as pipeline:
                    pipeline.watch(key)
                    encoded_record = pipeline.get(key)
                    if encoded_record is None:
                        raise ClientTransactionInvalid('transaction does not exist')
                    record = self._decode(encoded_record)
                    stored_browser_context_hash = self._required_text(
                        record, 'browser_context_hash'
                    )
                    expected_issuer = self._required_text(record, 'expected_issuer')
                    if (
                        not isinstance(browser_context_hash, str)
                        or not hmac.compare_digest(
                            stored_browser_context_hash, browser_context_hash
                        )
                    ):
                        raise ClientTransactionInvalid('browser context does not match')
                    if (
                        not isinstance(returned_issuer, str)
                        or not hmac.compare_digest(expected_issuer, returned_issuer)
                    ):
                        raise ClientTransactionInvalid('issuer does not match')
                    if record.get('status') != 'pending':
                        raise ClientTransactionInvalid('transaction is not pending')

                    return_to = self._required_text(record, 'return_to')
                    code_verifier = self._required_text(record, 'code_verifier')
                    nonce = self._required_text(record, 'nonce')
                    claim_token = secrets.token_urlsafe(32)
                    record['status'] = 'processing'
                    record['claim_token'] = claim_token
                    pipeline.multi()
                    pipeline.set(key, self._encode(record), keepttl=True)
                    pipeline.execute()
                    return ClientTransactionClaim(
                        authorization_transaction_id=authorization_transaction_id,
                        return_to=return_to,
                        code_verifier=code_verifier,
                        nonce=nonce,
                        expected_issuer=expected_issuer,
                        claim_token=claim_token,
                    )
            except WatchError:
                continue

    def complete(self, authorization_transaction_id, claim_token):
        key = self._key(authorization_transaction_id)
        while True:
            try:
                with self._redis.pipeline() as pipeline:
                    pipeline.watch(key)
                    encoded_record = pipeline.get(key)
                    if encoded_record is None:
                        raise ClientTransactionInvalid('transaction does not exist')
                    self._processing_record(
                        self._decode(encoded_record), claim_token
                    )
                    pipeline.multi()
                    pipeline.delete(key)
                    pipeline.execute()
                    return
            except WatchError:
                continue

    def release(self, authorization_transaction_id, claim_token):
        key = self._key(authorization_transaction_id)
        while True:
            try:
                with self._redis.pipeline() as pipeline:
                    pipeline.watch(key)
                    encoded_record = pipeline.get(key)
                    if encoded_record is None:
                        raise ClientTransactionInvalid('transaction does not exist')
                    record = self._processing_record(
                        self._decode(encoded_record), claim_token
                    )
                    record['status'] = 'pending'
                    del record['claim_token']
                    pipeline.multi()
                    pipeline.set(key, self._encode(record), keepttl=True)
                    pipeline.execute()
                    return
            except WatchError:
                continue
