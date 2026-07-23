# auth/reference-client/web-server/oidc_client/errors.py
#
# Stable client-side authentication error categories used by routes and tests.


class AuthError(Exception):
    """A permanent authentication failure that must consume the transaction."""


class TransientAuthError(Exception):
    """A temporary provider or network failure that permits callback retry."""
