# Superset

[Apache Superset](https://superset.apache.org/) visualizes the data that compute
blocks write into `data-postgres`. This directory contains the Superset image
used by scystream (`Dockerfile`), its configuration (`pythonpath/`) and a test
stack for CI (`docker-compose.test.yml`).

## How it fits together

1. A user uploads a Superset dashboard export (`.zip`) for a project in the
   scystream frontend. Core stores it in the data MinIO.
2. After the project's workflow finished successfully, core
   - rewrites the export to the project's schema in `data-postgres`
     (`core/services/superset_service/export_adapter.py`),
   - imports it into Superset,
   - creates the project owner in Superset if needed (username = email) and
     makes them owner of the dashboard and its datasets.
3. The frontend links to the imported dashboard. The user logs in to Superset
   via Keycloak and only sees the dashboards and datasets they own.

Authentication (`pythonpath/scystream_security.py`):

* **Users** log in via Keycloak (OIDC, client `superset`). Their Superset
  username is their email address, so users created by core are matched on
  their first login.
* **Core** calls the Superset API with a Keycloak access token of the service
  account client `superset-service` (client credentials grant). Superset
  validates the token against the realm's JWKS and acts as the Superset user
  `scystream-core` (created by `docker-init.sh`, role `Admin`). Tokens of any
  other Keycloak client are rejected.

## Keycloak clients

The realm in `.keycloak-config/main-realm.json` contains the two confidential
OpenID Connect clients Superset needs. They are imported when Keycloak starts
with `--import-realm`:

| Client ID          | Settings                                                                  | Development secret            | Secret goes to                            |
| ------------------ | ------------------------------------------------------------------------- | ----------------------------- | ----------------------------------------- |
| `superset`         | Standard flow on, redirect URI `http://localhost:8088/*`                  | `superset-dev-secret`         | `SUPERSET_OAUTH_CLIENT_SECRET` (superset) |
| `superset-service` | Standard flow off, service accounts on (client credentials grant)        | `superset-service-dev-secret` | `SUPERSET_KEYCLOAK_CLIENT_SECRET` (core)  |

The compose files use these secrets by default. **Regenerate both secrets in
the Keycloak admin console for any deployment that is not a local development
setup** and pass the new values via the environment variables above.

## Configuration

| Variable                        | Default                                                       | Description                                                   |
| ------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------- |
| `SUPERSET_SECRET_KEY`           | –                                                             | **Required.** Long random string                              |
| `SUPERSET_DATABASE_URI`         | `postgresql+psycopg2://superset:superset@superset-postgres/superset` | Superset metadata database                             |
| `SUPERSET_AUTH_TYPE`            | `oauth`                                                       | `oauth` (Keycloak) or `db` (local users, used in CI)          |
| `KEYCLOAK_REALM`                | `main`                                                        | Keycloak realm                                                |
| `KEYCLOAK_PUBLIC_URL`           | `http://localhost:8090`                                       | Keycloak URL as reachable by the browser                      |
| `KEYCLOAK_INTERNAL_URL`         | `http://keycloak:8080`                                        | Keycloak URL as reachable by the Superset container           |
| `SUPERSET_OAUTH_CLIENT_ID`      | `superset`                                                    | Keycloak client for user logins                               |
| `SUPERSET_OAUTH_CLIENT_SECRET`  | –                                                             | Its secret                                                    |
| `SUPERSET_SERVICE_CLIENT_ID`    | `superset-service`                                            | Keycloak client core uses for API calls                       |
| `SUPERSET_SERVICE_USERNAME`     | `scystream-core`                                              | Superset user core acts as                                    |
| `SUPERSET_SERVICE_ROLE`         | `Admin`                                                       | Role of that user                                             |
| `SUPERSET_USER_ROLE`            | `Gamma`                                                       | Role of users logging in via Keycloak                         |

## Tests

* `superset/tests` — unit tests of the Keycloak token validation
  (`pytest superset/tests`).
* `core/tests/integration/test_superset_import.py` — creates a dashboard in a
  real Superset, exports it, adapts and re-imports it the way core does and
  checks ownership and that the imported dataset can query the project schema:

  ```sh
  docker compose -f superset/docker-compose.test.yml up -d --build --wait
  cd core && SUPERSET_INTEGRATION_URL=http://localhost:8088 pytest tests/integration
  ```

Both run in the `Superset` GitHub workflow.
