# Runs one of the docs/deployment/compose/<name> stacks as a systemd
# service. The compose files are copied to /etc/scystream/<name>, secrets
# come from an environment file outside the Nix store (sops-nix, agenix or
# manually created with mode 0600).
{ config, lib, pkgs, ... }:
let
  cfg = config.scystream.composeStacks;
in
{
  options.scystream.composeStacks = lib.mkOption {
    default = { };
    type = lib.types.attrsOf (lib.types.submodule {
      options = {
        directory = lib.mkOption {
          type = lib.types.path;
          description = "Directory with docker-compose.yml (and Caddyfile).";
        };
        environmentFiles = lib.mkOption {
          type = lib.types.attrsOf lib.types.str;
          default = { };
          example = { ".env" = "/run/secrets/scystream-app.env"; };
          description = ''
            Secret files copied next to the compose file before start:
            target name (.env, core.env, ...) -> path outside the Nix store.
          '';
        };
        after = lib.mkOption {
          type = lib.types.listOf lib.types.str;
          default = [ ];
        };
      };
    });
  };

  config = lib.mkIf (cfg != { }) {
    virtualisation.docker = {
      enable = true;
      autoPrune = { enable = true; dates = "daily"; flags = [ "--all" "--filter" "until=168h" ]; };
      daemon.settings = {
        live-restore = true;
        no-new-privileges = true;
        log-driver = "journald";
        userland-proxy = false;
      };
    };

    environment.etc = lib.mapAttrs' (name: stack:
      lib.nameValuePair "scystream/${name}" { source = stack.directory; }) cfg;

    systemd.services = lib.mapAttrs' (name: stack:
      lib.nameValuePair "scystream-${name}" {
        description = "scystream ${name} (docker compose)";
        wantedBy = [ "multi-user.target" ];
        after = [ "docker.service" "network-online.target" ] ++ stack.after;
        requires = [ "docker.service" ];
        wants = [ "network-online.target" ];
        path = [ pkgs.docker pkgs.docker-compose pkgs.coreutils ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          RuntimeDirectory = "scystream-${name}";
          RuntimeDirectoryMode = "0700";
          ExecStartPre = pkgs.writeShellScript "scystream-${name}-prepare" ''
            set -eu
            cp -rL /etc/scystream/${name}/. "$RUNTIME_DIRECTORY/"
            ${lib.concatStringsSep "\n" (lib.mapAttrsToList (target: source:
              ''install -m 0600 ${source} "$RUNTIME_DIRECTORY/${target}"'') stack.environmentFiles)}
          '';
          ExecStart = pkgs.writeShellScript "scystream-${name}-up" ''
            cd "$RUNTIME_DIRECTORY"
            docker compose pull --quiet
            docker compose up -d --remove-orphans --wait
          '';
          ExecStop = pkgs.writeShellScript "scystream-${name}-down" ''
            cd "$RUNTIME_DIRECTORY" && docker compose down
          '';
          TimeoutStartSec = "15min";
        };
      }) cfg;
  };
}
