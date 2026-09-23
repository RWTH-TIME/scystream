"""Keycloak integration for Superset.

* Users log in via Keycloak (OIDC). Their Superset username is their email,
  so scystream-core can provision users before their first login and match
  users between the two systems.
* scystream-core calls the Superset API with a Keycloak access token obtained
  through the client credentials grant of a service account client. Those
  bearer tokens are validated against the realm's JWKS and mapped to a
  Superset service user.
"""

import logging
from functools import cached_property

import jwt
from flask import current_app
from keycloak_token import KeycloakTokenValidator, bearer_token
from superset.security import SupersetSecurityManager

logger = logging.getLogger(__name__)


class ScystreamSecurityManager(SupersetSecurityManager):
    @cached_property
    def _keycloak_validator(self) -> KeycloakTokenValidator:
        config = current_app.config
        return KeycloakTokenValidator(
            config["KEYCLOAK_JWKS_URL"],
            config.get("SCYSTREAM_SERVICE_CLIENTS", {}),
        )

    def request_loader(self, request):
        user = super().request_loader(request)
        if user is not None:
            return user

        token = bearer_token(request.headers.get("Authorization"))
        if not token:
            return None

        # Superset's own JWTs (e.g. from /api/v1/security/login) are signed
        # with HS256 and handled by flask-jwt-extended.
        try:
            algorithm = jwt.get_unverified_header(token).get("alg", "")
        except jwt.PyJWTError:
            return None
        if algorithm.startswith("HS"):
            return None

        service_client = self._keycloak_validator.service_client_for(token)
        if service_client is None:
            return None

        # The service user is provisioned by docker-init.sh
        user = self.find_user(username=service_client["username"])
        if user is None or not user.is_active:
            logger.warning(
                "Superset service user %s does not exist or is inactive",
                service_client["username"],
            )
            return None
        return user

    def oauth_user_info(self, provider, response=None):
        if provider != "keycloak":
            return super().oauth_user_info(provider, response)

        # Authlib already validated the ID token and put its claims into the
        # token response. Only ask the userinfo endpoint if they are missing.
        me = (response or {}).get("userinfo")
        if not me:
            remote = self.appbuilder.sm.oauth_remotes[provider]
            me = remote.get("userinfo").json()
        email = me.get("email")
        return {
            # username == email, see module docstring
            "username": email or me.get("preferred_username"),
            "email": email,
            "first_name": me.get("given_name", ""),
            "last_name": me.get("family_name", ""),
        }
