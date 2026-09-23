#!/usr/bin/env bash
# Creates the databases and roles of all scystream services. Runs once on
# the first start of the container (docker-entrypoint-initdb.d); on NixOS
# run it manually: sudo -u postgres ./init-roles.sh
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER:-postgres}" \
  -v core_pw="$CORE_DB_PASSWORD" \
  -v airflow_pw="$AIRFLOW_DB_PASSWORD" \
  -v keycloak_pw="$KEYCLOAK_DB_PASSWORD" \
  -v superset_pw="$SUPERSET_DB_PASSWORD" \
  -v data_pw="$DATA_DB_PASSWORD" \
  -v reader_pw="$DATA_READER_PASSWORD" <<'SQL'
-- one role and database per service
CREATE ROLE core LOGIN PASSWORD :'core_pw';
CREATE DATABASE core OWNER core;
CREATE ROLE airflow LOGIN PASSWORD :'airflow_pw';
CREATE DATABASE airflow OWNER airflow;
CREATE ROLE keycloak LOGIN PASSWORD :'keycloak_pw';
CREATE DATABASE keycloak OWNER keycloak;
CREATE ROLE superset LOGIN PASSWORD :'superset_pw';
CREATE DATABASE superset OWNER superset;
-- only the owners may connect (pg_hba additionally restricts by host)
REVOKE CONNECT ON DATABASE core, airflow, keycloak, superset FROM PUBLIC;

-- data written by the workflows: core creates one schema per project with
-- scystream_data, compute blocks write with it, superset only reads
CREATE ROLE scystream_data LOGIN PASSWORD :'data_pw';
CREATE ROLE superset_reader LOGIN PASSWORD :'reader_pw';
CREATE DATABASE data OWNER scystream_data;
\connect data
REVOKE CONNECT ON DATABASE data FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE data TO superset_reader;
-- everything scystream_data creates later is readable by superset_reader
ALTER DEFAULT PRIVILEGES FOR ROLE scystream_data
  GRANT USAGE ON SCHEMAS TO superset_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE scystream_data
  GRANT SELECT ON TABLES TO superset_reader;
SQL
