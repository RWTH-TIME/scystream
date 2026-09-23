# s3 host: native MinIO behind Caddy. Bucket and least privilege user: see
# ../compose/minio/README.md.
{ config, lib, pkgs, ... }:
let domain = "s3.example.org";
in
{
  imports = [ ./common.nix ];

  services.minio = {
    enable = true;
    listenAddress = "127.0.0.1:9000";
    consoleAddress = "${config.scystream.hosts.s3}:9001"; # private only
    # MINIO_ROOT_USER=... / MINIO_ROOT_PASSWORD=... (mode 0600, not in the store)
    rootCredentialsFile = "/run/secrets/minio-root.env";
    dataDir = [ "/var/lib/minio/data" ];
  };
  systemd.services.minio.environment.MINIO_SERVER_URL = "https://${domain}";

  services.caddy = {
    enable = true;
    virtualHosts.${domain}.extraConfig = ''
      # presigned URLs are signed for this host: keep the Host header
      reverse_proxy 127.0.0.1:9000 {
        header_up Host {host}
      }
      request_body {
        max_size 5GB
      }
      header Strict-Transport-Security "max-age=31536000; includeSubDomains"
    '';
  };

  networking.firewall.allowedTCPPorts = [ 80 443 ];
  networking.firewall.interfaces.${config.scystream.privateInterface}.allowedTCPPorts = [ 9001 ];
}
