# Imported by every scystream host. Hardened defaults: key-only SSH,
# firewall, automatic security updates, no password login.
{ config, lib, pkgs, ... }:
{
  options.scystream = {
    privateInterface = lib.mkOption {
      type = lib.types.str;
      default = "ens10";
      description = "Interface of the private network between the hosts.";
    };
    privateNetwork = lib.mkOption {
      type = lib.types.str;
      default = "10.0.0.0/24";
      description = "Private network of the scystream hosts.";
    };
    hosts = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      description = "Private addresses of the hosts.";
      default = {
        app = "10.0.0.4";
        db = "10.0.0.5";
        s3 = "10.0.0.6";
        airflow = "10.0.0.7";
        superset = "10.0.0.8";
        auth = "10.0.0.9";
      };
    };
  };

  config = {
    networking.hosts = {
      ${config.scystream.hosts.db} = [ "db.internal" ];
      ${config.scystream.hosts.airflow} = [ "airflow.internal" ];
    };

    services.openssh = {
      enable = true;
      openFirewall = false; # only via the private network, see below
      settings = {
        PasswordAuthentication = false;
        KbdInteractiveAuthentication = false;
        PermitRootLogin = "prohibit-password";
      };
    };
    services.fail2ban.enable = true;

    networking.firewall = {
      enable = true;
      interfaces.${config.scystream.privateInterface}.allowedTCPPorts = [ 22 ];
    };

    security.sudo.wheelNeedsPassword = true;
    nix.settings.allowed-users = [ "@wheel" ];

    system.autoUpgrade = {
      enable = true;
      allowReboot = true;
      rebootWindow = { lower = "03:00"; upper = "05:00"; };
    };
    nix.gc = { automatic = true; options = "--delete-older-than 14d"; };

    services.journald.extraConfig = "SystemMaxUse=2G";
    time.timeZone = "UTC";
  };
}
