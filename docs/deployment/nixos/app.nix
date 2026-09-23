# app host: core, frontend and Caddy (docker compose, ../compose/app), with
# the Airflow DAG folder mounted from the airflow host.
{ config, lib, pkgs, ... }:
{
  imports = [ ./common.nix ./compose-stack.nix ];

  fileSystems."/srv/scystream/airflow-dags" = {
    device = "airflow.internal:/srv/airflow/dags";
    fsType = "nfs";
    options = [ "nfsvers=4.2" "_netdev" "x-systemd.automount" "noauto" "nosuid" "nodev" "noexec" ];
  };

  scystream.composeStacks.app = {
    directory = ../compose/app;
    environmentFiles = {
      ".env" = "/run/secrets/scystream-app.env";
      "core.env" = "/run/secrets/scystream-core.env";
      "frontend.env" = "/run/secrets/scystream-frontend.env";
    };
    after = [ "srv-scystream-airflow\\x2ddags.mount" ];
  };

  networking.firewall.allowedTCPPorts = [ 80 443 ];
}
