#!/usr/bin/env bash
# Initializes the Superset metadata database. Safe to run on every start.
set -euo pipefail

superset db upgrade

if [ "${SUPERSET_AUTH_TYPE:-oauth}" = "db" ]; then
  # Local admin, only available when Superset uses its own user database
  superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
    --firstname Superset \
    --lastname Admin \
    --email "${SUPERSET_ADMIN_EMAIL:-admin@superset.local}" \
    --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || true
fi

superset init

# User that scystream-core acts as when it calls the API with a token of the
# Keycloak service account client (see pythonpath/scystream_security.py).
# It never logs in with a password.
superset fab create-user \
  --role "${SUPERSET_SERVICE_ROLE:-Admin}" \
  --username "${SUPERSET_SERVICE_USERNAME:-scystream-core}" \
  --firstname scystream \
  --lastname core \
  --email "${SUPERSET_SERVICE_USERNAME:-scystream-core}@scystream.local" \
  --password "$(head -c 32 /dev/urandom | base64)" || true
