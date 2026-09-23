ARG SUPERSET_VERSION="6.1.0"

FROM apache/superset:${SUPERSET_VERSION}

USER root

# psycopg2: connect to data-postgres (and the superset metadata db)
# Authlib: Keycloak (OIDC) login for users
RUN uv pip install --no-cache --python /app/.venv/bin/python \
    psycopg2-binary==2.9.13 \
    Authlib==1.8.0

COPY --chown=superset:superset pythonpath/ /app/pythonpath/
COPY --chown=superset:superset --chmod=755 docker-init.sh /app/docker-init.sh

USER superset
