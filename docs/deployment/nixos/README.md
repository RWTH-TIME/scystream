# NixOS hosts

One module per instance. Each imports `common.nix` (hardening, private
network, host names), and the containerized ones also import
`compose-stack.nix` (runs a `../compose/<name>` stack as a systemd unit).

| Host     | Module          | Native services                   | Containers                 |
| -------- | --------------- | --------------------------------- | -------------------------- |
| db       | `postgres.nix`  | PostgreSQL 17, nightly backups    | –                          |
| s3       | `minio.nix`     | MinIO, Caddy                      | –                          |
| auth     | `keycloak.nix`  | Keycloak, Caddy                   | –                          |
| airflow  | `airflow.nix`   | NFS server, Docker                | Airflow, Redis, registry cache |
| superset | `superset.nix`  | Docker                            | Superset, Caddy            |
| app      | `app.nix`       | NFS client, Docker                | core, frontend, Caddy      |

Usage, e.g. in the app host's `configuration.nix` (with this repository
checked out or added as a flake input):

```nix
{
  imports = [ ./hardware-configuration.nix /opt/scystream/docs/deployment/nixos/app.nix ];
  scystream.privateInterface = "ens10";
  scystream.hosts = { app = "10.0.0.4"; db = "10.0.0.5"; s3 = "10.0.0.6";
                      airflow = "10.0.0.7"; superset = "10.0.0.8"; auth = "10.0.0.9"; };
  users.users.admin = { isNormalUser = true; extraGroups = [ "wheel" ];
                        openssh.authorizedKeys.keys = [ "ssh-ed25519 ..." ]; };
}
```

Secrets are files under `/run/secrets` (e.g. managed with
[sops-nix](https://github.com/Mic92/sops-nix) or
[agenix](https://github.com/ryantm/agenix)); their content matches the
`.env.example` files of `../compose/<name>`. Replace the example domains
(`*.example.org`) in the modules.
