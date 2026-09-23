"""Validation of Keycloak access tokens, kept free of Superset imports so it
can be unit tested on its own."""

import logging
from functools import cached_property

import jwt

logger = logging.getLogger(__name__)


class KeycloakTokenValidator:
    """Validates Keycloak issued access tokens of trusted service clients."""

    def __init__(self, jwks_url: str, service_clients: dict[str, dict]):
        self.jwks_url = jwks_url
        self.service_clients = service_clients

    @cached_property
    def _jwks_client(self) -> jwt.PyJWKClient:
        return jwt.PyJWKClient(self.jwks_url, cache_keys=True, lifespan=300)

    def service_client_for(self, token: str) -> dict | None:
        """Returns the service client config the token belongs to, or None if
        the token is invalid or was not issued to a trusted service client."""
        try:
            key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256", "RS384", "RS512", "ES256", "PS256"],
                options={"verify_aud": False, "require": ["exp", "azp"]},
            )
        except (jwt.PyJWTError, jwt.PyJWKClientError) as exc:
            logger.debug("Rejected bearer token: %s", exc)
            return None

        return self.service_clients.get(claims.get("azp"))


def bearer_token(authorization_header: str | None) -> str | None:
    scheme, _, token = (authorization_header or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token
