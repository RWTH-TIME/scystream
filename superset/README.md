# Superset

[Apache Superset](https://superset.apache.org/) visualizes the data that compute
blocks write into `data-postgres`. This directory contains the Superset image
used by scystream (`Dockerfile`), its configuration (`pythonpath/`) and a test
stack for CI (`docker-compose.test.yml`).

## How it fits together

1. **Data.** After every successful workflow run, core looks up every table
   and view in the project's schemas of `data-postgres`. That is the project
   schema plus any schema configured on a database output of the project, so
   tables a step creates on its own are included too. Each one becomes a
   Superset dataset on the `scystream-data` database connection. Later runs
   refresh the datasets' columns.
2. **Dashboard.**
   - *With a visualization template* (a Superset dashboard export, `.zip` or
     `.tar.gz`, uploaded on the project page or inherited from a cloned
     project), the export is imported with only its references changed. Its
     datasets point to the project's datasets (matched by table name) and its
     database becomes `scystream-data`. Its charts and dashboard get
     project-specific UUIDs, so the same template can be used by many
     projects (`core/services/superset_service/template.py`).
   - *Without a template*, a standard dashboard is created with one table
     chart per dataset. Charts are only added for new tables, so changes made
     in Superset are kept.
3. **Access.** *Open dashboard* on the project page adds the logged-in
   scystream user as owner of the dashboard and its datasets. Core creates
   the Superset user if needed, with username = email, and the user then logs
   in to Superset with the same Keycloak account. Owners only see their
   dashboards and can query only their datasets.
4. **Templates.** *Download template* exports the project's dashboard in its
   current state from Superset, so it can be uploaded to other projects.
   Cloning a project uses the source project's visualization as the clone's
   template.

Syncing is triggered when the project status poll sees a new successful
run. It can also be triggered with *Sync now* (`POST
/project/{id}/superset/sync`).

### Superset hosted elsewhere

Core only talks to Superset over its API. Set:

| Variable (core)                   | Description                                                         |
| --------------------------------- | ------------------------------------------------------------------- |
| `SUPERSET_HOST`                   | Superset URL as reachable by core                                   |
| `SUPERSET_PUBLIC_URL`             | Superset URL as reachable by the browser (dashboard links)          |
| `SUPERSET_DATA_SQLALCHEMY_URI`    | How *Superset* reaches data-postgres, e.g. `postgresql+psycopg2://user:pass@db.example.org:5432/postgres`. Defaults to the `DEFAULT_CB_CONFIG_PG_*` connection |
| `SUPERSET_DATA_DATABASE_NAME`     | Name of the database connection in Superset (`scystream-data`)      |

The Superset instance needs `superset/pythonpath` (Keycloak login and
service account tokens), and `KEYCLOAK_INTERNAL_URL` must point to a Keycloak
URL that Superset can reach.

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

* `superset/tests`: unit tests of the Keycloak token validation
  (`pytest superset/tests`).
* `core/tests/superset`: unit tests of templates, the Superset client and the
  sync.
* `core/tests/integration/test_superset_e2e.py`: end to end tests with core's
  database, MinIO, data-postgres and Superset. They cover the whole flow: a
  project run → datasets and standard dashboard → sharing with a user, who
  can see and query only their data → template export → clone → the clone's
  run imports the template bound to the clone's data. They also cover
  uploaded `.tar.gz` templates and the HTTP endpoints:

  ```sh
  docker compose -f superset/docker-compose.test.yml up -d --build --wait
  cd core
  # environment: see the "Superset end to end" job in .github/workflows/superset.yaml
  alembic upgrade head
  SCYSTREAM_E2E=1 pytest tests/integration/test_superset_e2e.py
  ```

All of them run in the `Superset` GitHub workflow.
