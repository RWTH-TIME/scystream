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

The Keycloak realm needs two confidential OpenID Connect clients. They are
not part of `.keycloak-config/main-realm.json`, create them in the Keycloak
admin console (realm `main`):

| Client ID          | Settings                                                                                      | Secret goes to                                                     |
| ------------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `superset`         | Client authentication on, *Standard flow* on, redirect URI `http://localhost:8088/*`         | `SUPERSET_OAUTH_CLIENT_SECRET` (superset)                          |
| `superset-service` | Client authentication on, *Standard flow* off, *Service accounts roles* on                   | `SUPERSET_KEYCLOAK_CLIENT_SECRET` (core)                           |

Or with `kcadm.sh` inside the keycloak container:

```sh
kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password admin
kcadm.sh create clients -r main -s clientId=superset -s publicClient=false \
  -s standardFlowEnabled=true -s 'redirectUris=["http://localhost:8088/*"]'
kcadm.sh create clients -r main -s clientId=superset-service -s publicClient=false \
  -s standardFlowEnabled=false -s serviceAccountsEnabled=true
```

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
