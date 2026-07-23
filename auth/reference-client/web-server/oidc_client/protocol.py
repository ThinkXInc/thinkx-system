# auth/reference-client/web-server/oidc_client/protocol.py
#
# Small protocol helpers for PKCE, safe local redirects, and canonical JSON.

import base64
import hashlib
import json
from urllib.parse import urlsplit


def sha256_hex(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def pkce_s256(code_verifier):
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


def safe_return_to(value, default='/'):
    if not isinstance(value, str) or not value.startswith('/'):
        return default
    if value.startswith('//') or '\\' in value or any(ord(char) < 32 for char in value):
        return default
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        return default
    return value


def canonical_json(payload):
    return json.dumps(payload, separators=(',', ':'), sort_keys=True)
