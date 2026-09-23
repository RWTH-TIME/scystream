# airflow host: Airflow (docker compose, ../compose/airflow) with the
# registry cache, the DAG folder exported to the app host via NFS.
# Nothing else should run here: the worker controls the docker daemon.
{ config, lib, pkgs, ... }:
{
  imports = [ ./common.nix ./compose-stack.nix ];

  systemd.tmpfiles.rules = [ "d /srv/airflow/dags 0770 50000 root -" ];

  services.nfs.server = {
    enable = true;
    exports = ''
      /srv/airflow/dags ${config.scystream.hosts.app}(rw,sync,no_subtree_check,root_squash)
    '';
  };

  scystream.composeStacks.airflow = {
    directory = ../compose/airflow;
    # PRIVATE_IP, DB_HOST, AIRFLOW_DB_PASSWORD, DOCKER_GID, FERNET/JWT/SECRET
    # keys, admin user, GHCR token (see ../compose/airflow/.env.example)
    environmentFiles.".env" = "/run/secrets/scystream-airflow.env";
  };

  networking.firewall.interfaces.${config.scystream.privateInterface}.allowedTCPPorts = [
    8080 # Airflow API for core
    2049 # NFS for the app host
  ];
}
