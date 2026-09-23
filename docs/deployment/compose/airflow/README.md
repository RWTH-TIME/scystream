# Airflow host

1. Create the DAG folder and export it to the app host (NFS):

   ```sh
   install -d -o 50000 -g 0 -m 0770 /srv/airflow/dags
   echo "/srv/airflow/dags 10.0.0.4(rw,sync,no_subtree_check,root_squash)" >> /etc/exports
   exportfs -ra
   ```

   `10.0.0.4` is the app host's private address.
2. `docker compose up -d`
3. Create the user core logs in with (`AIRFLOW_USER`/`AIRFLOW_PASS` on core):

   ```sh
   docker compose exec airflow-apiserver airflow users create \
     --username scystream --password '<secret>' --role Op \
     --firstname scystream --lastname core --email core@example.org
   ```

4. The worker needs to reach `db.internal` and `s3.example.org`, and so do the
   compute block containers it starts (`CB_NETWORK_MODE=bridge`).

Compute block images are pulled through `registry-cache`:
`CB_IMAGE_REGISTRY_MIRRORS={"ghcr.io":"localhost:5001"}` on core turns
`ghcr.io/org/block:tag` into `localhost:5001/org/block:tag`. The first pull
fills the cache; later runs only compare the manifest (`CB_IMAGE_FORCE_PULL`),
so updated tags are used immediately. `docker image prune -a --filter
"until=168h"` in a daily timer keeps the worker's disk clean.
