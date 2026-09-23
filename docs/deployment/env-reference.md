# Environment variables

All values below are examples for the host names used in the
[deployment guide](README.md). **Bold** variables must be set in
production; the others have sensible defaults.

## core (app host)

| Variable | Example | Description |
| -------- | ------- | ----------- |
| **`DEVELOPMENT`** | `false` | Never `true` in production (opens CORS, rewrites hosts for local development). |
| **`EXTERNAL_URL`** | `https://app.example.org` | Frontend URL, the only CORS origin. |
| `LOG_LEVEL` | `INFO` | |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1` | Proxies whose `X-Forwarded-*` headers are trusted (Caddy on the same host). |
| **`DATABASE_HOST`** | `db.internal` | Core database. |
| `DATABASE_PORT` | `5432` | |
| `DATABASE_NAME` | `core` | |
| **`DATABASE_USER`** | `core` | |
| **`DATABASE_PASSWORD`** | *secret* | |
| **`KEYCLOAK_SERVER_URL`** | `https://auth.example.org` | |
| `KEYCLOAK_REALM` | `main` | |
| `KEYCLOAK_CLIENT_ID` | `scystream-core` | |
| **`KEYCLOAK_CLIENT_SECRET`** | *secret* | Secret of the `scystream-core` client. |
| `KEYCLOAK_REDIRECT_URL` | `https://api.example.org/callback` | Only needed if the callback URL can not be derived from the request. |
| **`AIRFLOW_HOST`** | `http://airflow.internal:8080` | Airflow API server, **without** `/api/v2`. |
| `AIRFLOW_USER` | `scystream` | Airflow user core uses (role `Op` or `Admin`). |
| **`AIRFLOW_PASS`** | *secret* | |
| `AIRFLOW_DAG_DIR` | `/airflow-dags` | Where core writes DAG files (NFS mount of the Airflow DAG folder). |
| `AIRFLOW_TOKEN_TTL_SECONDS` | `300` | How long an Airflow token is reused. |
| **`WORKFLOW_TEMPLATE_REPO`** | `https://git.example.org/org/pipeline-templates.git` | Repository with the pipeline templates. |
| `REPO_CACHE_DIR` | `repos` | Clones of compute block and template repositories. |
| **`CB_NETWORK_MODE`** | `bridge` | Docker network of compute block containers on the workers. |
| `CB_IMAGE_FORCE_PULL` | `true` | Pull compute block images on every run. |
| `CB_IMAGE_REGISTRY_MIRRORS` | `{"ghcr.io":"localhost:5001"}` | JSON mapping registry → pull-through cache, seen from the workers. |
| **`DEFAULT_CB_CONFIG_PG_HOST`** | `db.internal` | Data postgres as reachable by compute blocks and core. |
| `DEFAULT_CB_CONFIG_PG_PORT` | `5432` | |
| **`DEFAULT_CB_CONFIG_PG_USER`** | `scystream_data` | Role that owns the project schemas (see `init-roles.sql`). |
| **`DEFAULT_CB_CONFIG_PG_PASS`** | *secret* | |
| **`DEFAULT_CB_CONFIG_S3_HOST`** | `https://s3.example.org` | MinIO, scheme included, as reachable by compute blocks and core. |
| **`DEFAULT_CB_CONFIG_S3_PORT`** | `443` | |
| **`DEFAULT_CB_CONFIG_S3_ACCESS_KEY`** | `scystream` | MinIO user limited to the bucket (not root). |
| **`DEFAULT_CB_CONFIG_S3_SECRET_KEY`** | *secret* | |
| `DEFAULT_CB_CONFIG_S3_BUCKET_NAME` | `data` | Created at startup if missing and allowed. |
| `DEFAULT_CB_CONFIG_S3_FILE_PATH` | `/` | |
| **`EXTERNAL_URL_DATA_S3`** | `https://s3.example.org` | MinIO as reachable by browsers; presigned URLs are signed for it. |
| `S3_REGION` | `us-east-1` | Must match `MINIO_REGION` if that is set. |
| `MAX_UPLOAD_SIZE_MB` | `100` | Upload limit (also set the proxy's body size limit). |
| **`SUPERSET_HOST`** | `https://superset.example.org` | Superset API as reachable by core. |
| `SUPERSET_PUBLIC_URL` | `https://superset.example.org` | Superset as reachable by browsers (dashboard links). |
| `SUPERSET_KEYCLOAK_CLIENT_ID` | `superset-service` | |
| **`SUPERSET_KEYCLOAK_CLIENT_SECRET`** | *secret* | Secret of the `superset-service` client. |
| **`SUPERSET_DATA_SQLALCHEMY_URI`** | `postgresql+psycopg2://superset_reader:…@db.internal:5432/data` | How Superset reads the data database (read-only role). |
| `SUPERSET_DATA_DATABASE_NAME` | `scystream-data` | Name of that connection in Superset. |
| `SUPERSET_USER_ROLE` | `Gamma` | Role of users core creates in Superset. |
| `SUPERSET_EXPORT_S3_PREFIX` | `projects` | Prefix of visualization templates in the bucket. |

Core clones compute block repositories. For private repositories over SSH,
mount a deploy key read-only at `/home/core/.ssh/id_ed25519` (owner uid
50000, mode `0400`). Host keys are accepted on first use and pinned
afterwards; mount a `known_hosts` file to pin them up front.

## frontend (app host)

Read at runtime; no rebuild needed.

| Variable | Example |
| -------- | ------- |
| **`NEXT_PUBLIC_API_URL`** | `https://api.example.org/` |
| **`NEXT_PUBLIC_WS_URL`** | `wss://api.example.org/` |
| **`NEXT_PUBLIC_OIDC_PROVIDER`** | `https://auth.example.org/realms/main` |
| `NEXT_PUBLIC_CLIENT_ID` | `scystream` |
| **`NEXT_PUBLIC_REDIRECT_URI`** | `https://app.example.org` |
| **`NEXT_PUBLIC_POST_LOGOUT_REDIRECT_URI`** | `https://app.example.org` |

## superset (superset host)

| Variable | Example | Description |
| -------- | ------- | ----------- |
| **`SUPERSET_SECRET_KEY`** | *secret* | Never change it after the first start (encrypts stored passwords). |
| **`SUPERSET_DATABASE_URI`** | `postgresql+psycopg2://superset:…@db.internal:5432/superset` | Superset's own metadata database. |
| `SUPERSET_AUTH_TYPE` | `oauth` | `oauth` (Keycloak). `db` only for tests. |
| `KEYCLOAK_REALM` | `main` | |
| **`KEYCLOAK_PUBLIC_URL`** | `https://auth.example.org` | Keycloak as reachable by browsers. |
| **`KEYCLOAK_INTERNAL_URL`** | `https://auth.example.org` | Keycloak as reachable by Superset (token, userinfo, JWKS). |
| `SUPERSET_OAUTH_CLIENT_ID` | `superset` | |
| **`SUPERSET_OAUTH_CLIENT_SECRET`** | *secret* | Secret of the `superset` client. |
| `SUPERSET_SERVICE_CLIENT_ID` | `superset-service` | Tokens of this client act as the service user. |
| `SUPERSET_SERVICE_USERNAME` | `scystream-core` | Created by `docker-init.sh`. |
| `SUPERSET_SERVICE_ROLE` | `Admin` | Needed to manage databases, datasets, users. |
| `SUPERSET_USER_ROLE` | `Gamma` | Role of users registering via Keycloak. |

## airflow (airflow host)

Set the same values on **all** Airflow components.

| Variable | Example |
| -------- | ------- |
| **`AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`** | `postgresql+psycopg2://airflow:…@db.internal:5432/airflow` |
| **`AIRFLOW__CELERY__RESULT_BACKEND`** | `db+postgresql://airflow:…@db.internal:5432/airflow` |
| `AIRFLOW__CELERY__BROKER_URL` | `redis://redis:6379/0` |
| **`AIRFLOW__CORE__FERNET_KEY`** | *secret* (encrypts connections and variables) |
| **`AIRFLOW__API_AUTH__JWT_SECRET`** | *secret* (tokens between components) |
| **`AIRFLOW__API__SECRET_KEY`** | *secret* |
| `AIRFLOW__CORE__EXECUTION_API_SERVER_URL` | `http://airflow-apiserver:8080/execution/` |
| `AIRFLOW__CORE__AUTH_MANAGER` | `airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager` |
| `AIRFLOW__CORE__LOAD_EXAMPLES` | `false` |
| `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION` | `true` |
| **`_AIRFLOW_WWW_USER_USERNAME`** / **`_AIRFLOW_WWW_USER_PASSWORD`** | admin created on first start; create a separate user for core |

## keycloak (auth host)

| Variable | Example |
| -------- | ------- |
| **`KC_HOSTNAME`** | `https://auth.example.org` |
| `KC_HTTP_ENABLED` | `true` (TLS is terminated by Caddy on the same host) |
| `KC_PROXY_HEADERS` | `xforwarded` |
| **`KC_DB_URL`** | `jdbc:postgresql://db.internal:5432/keycloak` |
| **`KC_DB_USERNAME`** / **`KC_DB_PASSWORD`** | `keycloak` / *secret* |
| **`KC_BOOTSTRAP_ADMIN_USERNAME`** / **`KC_BOOTSTRAP_ADMIN_PASSWORD`** | first admin, change after first login |

## minio (s3 host)

| Variable | Example |
| -------- | ------- |
| **`MINIO_ROOT_USER`** / **`MINIO_ROOT_PASSWORD`** | administration only |
| `MINIO_SERVER_URL` | `https://s3.example.org` |
| `MINIO_BROWSER_REDIRECT_URL` | `https://s3-console.internal` (console stays private) |
