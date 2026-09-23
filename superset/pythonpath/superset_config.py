"""Superset configuration for scystream.

Superset is used to visualize the data compute blocks write into the
data-postgres. Dashboards are imported by scystream-core, which talks to the
Superset API using a Keycloak service account token (see
scystream_security.py). Users log in to Superset via Keycloak as well.

All values can be configured via environment variables.
"""

import os

from flask_appbuilder.security.manager import AUTH_DB, AUTH_OAUTH
from scystream_security import ScystreamSecurityManager


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


SECRET_KEY = _env("SUPERSET_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SUPERSET_SECRET_KEY must be set")

SQLALCHEMY_DATABASE_URI = _env(
    "SUPERSET_DATABASE_URI",
    "postgresql+psycopg2://superset:superset@superset-postgres:5432/superset",
)

# Behind the scystream reverse proxy / on localhost
ENABLE_PROXY_FIX = True
WTF_CSRF_ENABLED = True
# Exposes /api/v1/security/users & roles, used by core to provision users
FAB_ADD_SECURITY_API = True

CUSTOM_SECURITY_MANAGER = ScystreamSecurityManager

# The role new users get. Users only see dashboards and datasets they own,
# ownership is granted by scystream-core when a dashboard is imported.
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = _env("SUPERSET_USER_ROLE", "Gamma")
AUTH_ROLES_SYNC_AT_LOGIN = False

KEYCLOAK_REALM = _env("KEYCLOAK_REALM", "main")
# URL the browser uses to reach Keycloak
KEYCLOAK_PUBLIC_URL = _env("KEYCLOAK_PUBLIC_URL", "http://localhost:8090")
# URL Superset itself uses to reach Keycloak (inside the docker network)
KEYCLOAK_INTERNAL_URL = _env("KEYCLOAK_INTERNAL_URL", "http://keycloak:8080")

_oidc_public = (
    f"{KEYCLOAK_PUBLIC_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}"
    "/protocol/openid-connect"
)
_oidc_internal = (
    f"{KEYCLOAK_INTERNAL_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}"
    "/protocol/openid-connect"
)

KEYCLOAK_JWKS_URL = f"{_oidc_internal}/certs"
# Keycloak clients whose (service account) tokens may call the Superset API,
# mapped to the Superset user they act as (created by docker-init.sh).
SCYSTREAM_SERVICE_CLIENTS = {
    _env("SUPERSET_SERVICE_CLIENT_ID", "superset-service"): {
        "username": _env("SUPERSET_SERVICE_USERNAME", "scystream-core"),
    },
}

AUTH_TYPE = AUTH_DB if _env("SUPERSET_AUTH_TYPE", "oauth") == "db" else (
    AUTH_OAUTH
)

OAUTH_PROVIDERS = [
    {
        "name": "keycloak",
        "icon": "fa-key",
        "token_key": "access_token",
        "remote_app": {
            "client_id": _env("SUPERSET_OAUTH_CLIENT_ID", "superset"),
            "client_secret": _env("SUPERSET_OAUTH_CLIENT_SECRET", ""),
            "client_kwargs": {"scope": "openid email profile"},
            "authorize_url": f"{_oidc_public}/auth",
            "access_token_url": f"{_oidc_internal}/token",
            "api_base_url": f"{_oidc_internal}/",
            "jwks_uri": KEYCLOAK_JWKS_URL,
        },
    },
]
