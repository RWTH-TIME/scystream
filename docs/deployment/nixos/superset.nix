# superset host: Superset (docker compose, ../compose/superset) with Caddy.
{ config, lib, pkgs, ... }:
{
  imports = [ ./common.nix ./compose-stack.nix ];

  scystream.composeStacks.superset = {
    directory = ../compose/superset;
    environmentFiles.".env" = "/run/secrets/scystream-superset.env";
  };

  networking.firewall.allowedTCPPorts = [ 80 443 ];
}
