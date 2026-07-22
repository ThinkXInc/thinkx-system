# auth/web-server/oidc/stores.py
#
# Redis stores for authorization requests, authorization codes, and access tokens.

import base64
import hashlib
import hmac
import json
import secrets

from redis import WatchError


def sha256_hex(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def pkce_s256_challenge(code_verifier):
    hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(hashed).rstrip(b'=').decode('ascii')


def decode_json_record(raw):
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    return json.loads(raw)


class AuthorizationRequestStore:
    PREFIX = 'oidc:authorization_request:'

    def __init__(self, redis_client, ttl_seconds):
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    def create(self, record):
        request_handle = secrets.token_urlsafe(32)
        self.redis.setex(
            self.PREFIX + sha256_hex(request_handle),
            self.ttl_seconds,
            json.dumps(record),
        )
        return request_handle

    def get(self, request_handle):
        return decode_json_record(
            self.redis.get(self.PREFIX + sha256_hex(request_handle))
        )

    def delete(self, request_handle):
        self.redis.delete(self.PREFIX + sha256_hex(request_handle))


class SSOStore:
    CODE_PREFIX = 'oauth:code:'
    TOKEN_PREFIX = 'oauth:at:'

    def __init__(self, redis_client, code_ttl_seconds, token_ttl_seconds):
        self.redis = redis_client
        self.code_ttl_seconds = code_ttl_seconds
        self.token_ttl_seconds = token_ttl_seconds

    def issue_code(self, record):
        code = secrets.token_urlsafe(32)
        self.redis.setex(
            self.CODE_PREFIX + sha256_hex(code),
            self.code_ttl_seconds,
            json.dumps(record),
        )
        return code

    def begin_consume(self, *, code, client_id, redirect_uri, code_verifier):
        record = decode_json_record(
            self.redis.get(self.CODE_PREFIX + sha256_hex(code))
        )
        if not record:
            return None
        if record['client_id'] != client_id or record['redirect_uri'] != redirect_uri:
            return None
        if not hmac.compare_digest(
            record['code_challenge'], pkce_s256_challenge(code_verifier)
        ):
            return None
        return record

    def finish_consume_and_issue_access_token(self, *, code, record):
        code_key = self.CODE_PREFIX + sha256_hex(code)
        while True:
            pipeline = self.redis.pipeline()
            try:
                pipeline.watch(code_key)
                if pipeline.get(code_key) is None:
                    pipeline.unwatch()
                    return None
                access_token = secrets.token_urlsafe(32)
                token_record = {
                    'subject': record['subject'],
                    'client_id': record['client_id'],
                    'scope': record['scope'],
                    'auth_generation': record['auth_generation'],
                }
                pipeline.multi()
                pipeline.delete(code_key)
                pipeline.setex(
                    self.TOKEN_PREFIX + sha256_hex(access_token),
                    self.token_ttl_seconds,
                    json.dumps(token_record),
                )
                pipeline.execute()
                return access_token
            except WatchError:
                continue
            finally:
                pipeline.reset()

    def resolve_access_token(self, access_token):
        return decode_json_record(
            self.redis.get(self.TOKEN_PREFIX + sha256_hex(access_token))
        )
