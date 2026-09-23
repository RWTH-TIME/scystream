# db host: native PostgreSQL 17 for all services, reachable only from the
# hosts that use each database. Create the roles once with
#   sudo -u postgres env CORE_DB_PASSWORD=... (all *_PASSWORD vars) \
#     ../compose/postgres/init-roles.sh
{ config, lib, pkgs, ... }:
let
  h = config.scystream.hosts;
  allow = db: user: host: "host ${db} ${user} ${host}/32 scram-sha-256";
in
{
  imports = [ ./common.nix ];

  services.postgresql = {
    enable = true;
    package = pkgs.postgresql_17;
    enableTCPIP = true;
    settings = {
      listen_addresses = lib.mkForce "localhost,${h.db}";
      password_encryption = "scram-sha-256";
      max_connections = 300;
      ssl = false; # private network; enable with a certificate if it is shared
      log_connections = true;
      log_disconnections = true;
    };
    authentication = lib.mkForce (lib.concatStringsSep "\n" [
      "local all postgres peer"
      "local all all scram-sha-256"
      (allow "core" "core" h.app)
      (allow "data" "scystream_data" h.app)
      (allow "data" "scystream_data" h.airflow)   # compute blocks
      (allow "data" "superset_reader" h.superset)
      (allow "airflow" "airflow" h.airflow)
      (allow "keycloak" "keycloak" h.auth)
      (allow "superset" "superset" h.superset)
    ]);
  };

  services.postgresqlBackup = {
    enable = true;
    databases = [ "core" "airflow" "keycloak" "superset" "data" ];
    compression = "zstd";
    startAt = "*-*-* 02:00:00";
  };

  networking.firewall.interfaces.${config.scystream.privateInterface}.allowedTCPPorts = [ 5432 ];
}
