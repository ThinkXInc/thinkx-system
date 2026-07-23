# auth/reference-client/web-server/oidc_client/provider.py
#
# Immutable, operator-trusted OpenID Provider endpoint configuration.

from dataclasses import dataclass


@dataclass(frozen=True)
class TrustedProvider:
    """Endpoints that may receive reference-client OIDC requests."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    logout_endpoint: str
