# auth host: native Keycloak (production mode) behind Caddy.
{ config, lib, pkgs, ... }:
let domain = "auth.example.org";
in
{
  imports = [ ./common.nix ];

  services.keycloak = {
    enable = true;
    database = {
      type = "postgresql";
      createLocally = false;
      host = "db.internal";
      port = 5432;
      name = "keycloak";
      username = "keycloak";
      passwordFile = "/run/secrets/keycloak-db-password";
      useSSL = false;
    };
    settings = {
      hostname = "https://${domain}";
      http-enabled = true;
      http-host = "127.0.0.1";
      http-port = 8080;
      proxy-headers = "xforwarded";
      health-enabled = true;
    };
    # imported on the first start; contains DEVELOPMENT secrets and localhost
    # redirect URIs, change both in the admin console afterwards
    realmFiles = [ ../../../.keycloak-config/main-realm.json ];
    # initial admin: KC_BOOTSTRAP_ADMIN_USERNAME / KC_BOOTSTRAP_ADMIN_PASSWORD
    # in /run/secrets/keycloak-admin.env
  };
  systemd.services.keycloak.serviceConfig.EnvironmentFile =
    "/run/secrets/keycloak-admin.env";

  services.caddy = {
    enable = true;
    virtualHosts.${domain}.extraConfig = ''
      @admin {
        path /admin*
        not remote_ip ${config.scystream.privateNetwork}
      }
      respond @admin 403
      reverse_proxy 127.0.0.1:8080
      header Strict-Transport-Security "max-age=31536000; includeSubDomains"
    '';
  };

  networking.firewall.allowedTCPPorts = [ 80 443 ];
}
