# Deploying scystream

This guide deploys scystream with every component on its **own instance**,
using either **Docker Compose** (any Linux host) or **NixOS**. Both variants
use the same configuration and the same environment variables, which are
listed in [env-reference.md](env-reference.md).

- `compose/<instance>/`: a `docker-compose.yml` and a `.env.example` for each instance
- `nixos/`: NixOS host modules for the same instances (`common.nix` is imported by all)

> Time to a first deployment is about an hour once DNS, TLS and the hosts exist.
> Follow the order in [Deployment order](#deployment-order).

## Architecture

```
                 browsers (HTTPS only)
   ┌───────────────┬──────────────┬───────────────┬──────────────┐
   ▼               ▼              ▼               ▼              │
 app host        auth host      superset host   s3 host          │
 app.example.org auth.example   superset.example s3.example.org  │
 ├ caddy (TLS)   ├ caddy (TLS)  ├ caddy (TLS)   ├ caddy (TLS)    │
 ├ frontend      └ keycloak     └ superset      └ minio          │
 └ core ──────────────┐                                          │
   │ writes DAGs (NFS)│ API                                      │
   ▼                  ▼                                          │
 airflow host (private network only)                             │
 ├ api-server, scheduler, dag-processor, triggerer               │
 ├ celery worker(s) ── docker ──► compute block containers ──────┤
 ├ redis                          (read/write data-postgres,     │
 └ registry cache (pull-through)   MinIO over the network)       │
                                                                 │
 db host (private network only)                                  │
 └ postgresql: core, airflow, keycloak, superset, data  ◄────────┘
```

| Instance | Runs                                              | Public?                       | Talks to                                           |
| -------- | ------------------------------------------------- | ----------------------------- | -------------------------------------------------- |
| app      | frontend, core (FastAPI), Caddy                   | 443                           | db, airflow API, keycloak, superset, minio, git hosts |
| airflow  | Airflow 3 (CeleryExecutor), Redis, registry cache | no                            | db, minio, image registries                        |
| superset | Superset 6 (`superset/`), Caddy                   | 443                           | db (superset + data), keycloak                     |
| auth     | Keycloak, Caddy                                   | 443                           | db                                                 |
| s3       | MinIO, Caddy                                      | 443 (S3 API), console private | –                                                  |
| db       | PostgreSQL 17                                     | no                            | –                                                  |

Hosts reach each other over a **private network** (VPC, WireGuard,
Tailscale, …). The examples use these names:

| Name                    | Resolves to                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `app.example.org`       | app host (public), frontend                                  |
| `api.example.org`       | app host (public), core API and websockets                   |
| `auth.example.org`      | auth host (public)                                           |
| `superset.example.org`  | superset host (public)                                       |
| `s3.example.org`        | s3 host (public, S3 API). Browsers download from it, compute blocks upload to it |
| `airflow.internal`      | airflow host (private)                                       |
| `db.internal`           | db host (private)                                            |

### Things that are specific to a multi-instance setup

1. **DAG files.** Core writes one Python file per project into
   `AIRFLOW_DAG_DIR`, and the Airflow dag-processor and workers read them.
   Export `/srv/airflow/dags` from the airflow host over NFS (read-write for
   uid 50000) and mount it on the app host at `/srv/scystream/airflow-dags`.
   The NixOS modules set this up. The files contain connection settings,
   including credentials, so keep the export restricted to the app host.
2. **Compute blocks** run as Docker containers on the Airflow workers
   (DockerOperator via the worker's Docker socket). They reach data-postgres
   and MinIO over the network:
   - Set `CB_NETWORK_MODE=bridge`.
   - Set `DEFAULT_CB_CONFIG_PG_HOST=db.internal` and
     `DEFAULT_CB_CONFIG_S3_HOST=https://s3.example.org`.
   - Anything with access to the worker's Docker socket is root on that host,
     so the airflow host must not run anything else.
3. **Compute block images** are pulled on every run
   (`CB_IMAGE_FORCE_PULL=true`), so updated tags are picked up. Pulls go
   through the registry cache on the airflow host
   (`CB_IMAGE_REGISTRY_MIRRORS={"ghcr.io":"localhost:5001"}`). A run then
   only checks the image manifest on the local cache, and layers are
   downloaded from GitHub once. Docker allows plain HTTP for `localhost`
   registries, so the cache needs no TLS. Every worker host runs its own
   cache.
4. **Presigned download URLs** are signed for `EXTERNAL_URL_DATA_S3`
   (`https://s3.example.org`). Caddy in front of MinIO must pass the
   `Host` header through unchanged, which the examples do.
5. **Superset reads the data** through `SUPERSET_DATA_SQLALCHEMY_URI`, with
   a read-only database role. Compute blocks and core write through
   `DEFAULT_CB_CONFIG_PG_*`.

## Deployment order

1. **db:** PostgreSQL with all databases and roles
   ([nixos/postgres.nix](nixos/postgres.nix) or
   [compose/postgres](compose/postgres)). Run `init-roles.sql` once; it
   sets up the least-privilege data roles.
2. **s3:** MinIO. Create the `data` bucket and a scystream user limited to
   it (see [compose/minio](compose/minio/README.md)).
3. **auth:** Keycloak with the `main` realm (`.keycloak-config/main-realm.json`).
   Then, in the admin console:
   - Set the redirect URIs and web origins of the `scystream` client to
     `https://app.example.org/*`.
   - Set those of the `superset` client to `https://superset.example.org/*`.
   - **Regenerate the secrets** of `scystream-core`, `superset` and
     `superset-service`. The file contains development secrets.
   - Delete the `test` user.
4. **airflow:** Airflow plus the registry cache, with the DAG folder
   exported over NFS.
5. **superset:** the Superset image from `superset/`.
6. **app:** core and frontend. Core migrates its database on start.

Then run the [verification](#verification) steps.

## Secrets

Generate every secret; never reuse the development defaults. Useful
commands:

```sh
openssl rand -hex 32                         # passwords (hex: safe inside DSNs and URLs)
openssl rand -base64 42                      # SUPERSET_SECRET_KEY, AIRFLOW__API__SECRET_KEY
openssl rand -base64 32                      # AIRFLOW__API_AUTH__JWT_SECRET
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # AIRFLOW__CORE__FERNET_KEY
```

- **Compose:** keep them in the instance's `.env`, mode `0600`, owned by
  root.
- **NixOS:** keep them outside the Nix store, in `/run/secrets/*.env` files
  (e.g. with sops-nix or agenix), which the modules pass as `EnvironmentFile`.
  Never put secrets into `.nix` files.

## Hardening checklist

- [ ] Only ports 22 (ideally only over the private network) and 443 on the
      public hosts are reachable; airflow and db accept connections from the
      private network only (the NixOS modules configure the firewall).
- [ ] TLS everywhere public (Caddy, automatic certificates); HSTS enabled.
- [ ] PostgreSQL: `scram-sha-256`, listens on the private interface only,
      `pg_hba` allows each database only from the host that uses it, one
      role per service, Superset reads the data database with a read-only
      role.
- [ ] MinIO: root credentials only used for administration; scystream
      uses a user restricted to the `data` bucket; bucket not public; console
      not exposed publicly.
- [ ] Keycloak: production mode (`start`, not `start-dev`), regenerated client
      secrets, redirect URIs restricted to the real domains, admin console only
      reachable from the private network, brute force detection on.
- [ ] Airflow: generated `FERNET_KEY`, `JWT_SECRET` and API `SECRET_KEY`
      (the same on all components), example DAGs off, admin password
      rotated, UI not exposed publicly.
- [ ] Superset: generated `SUPERSET_SECRET_KEY`, Keycloak login only
      (`SUPERSET_AUTH_TYPE=oauth`).
- [ ] Core and frontend containers run as non-root (default in the images),
      `no-new-privileges`, read-only root filesystem where possible (see the
      compose files).
- [ ] `DEVELOPMENT=false` on core (CORS is limited to `EXTERNAL_URL`).
- [ ] The DAG folder export is limited to the app host.
- [ ] Backups: `pg_dump` for all databases (NixOS: `services.postgresqlBackup`),
      MinIO bucket replication or snapshots.
- [ ] Images are pinned by version tag (or digest) and updated with Renovate.

## Verification

1. `https://auth.example.org/realms/main/.well-known/openid-configuration` answers.
2. Log in on `https://app.example.org`, create a project and add a compute block.
   Core logs show the repository clone.
3. Upload an input file, then open it via its link. This proves the
   presigned URL is signed for `s3.example.org`.
4. Start the workflow. On the airflow host, `docker ps` shows the compute block
   containers, and the image comes from `localhost:5001/...`.
5. After the run, the project page shows *Open dashboard*. It opens
   Superset, you are logged in via Keycloak, and the dashboard shows the
   tables of the run.
6. `curl -s http://localhost:5001/v2/_catalog` on the airflow host lists the
   cached images.

## Updating

- **Compose:** `docker compose pull && docker compose up -d` per instance.
  Core runs the database migrations on start.
- **NixOS:** bump the image tags in the host configuration and run
  `nixos-rebuild switch`.
- Update Airflow's image and `apache-airflow-client` in core together: the
  API client only works with the Airflow version it was generated for. CI
  checks this.
