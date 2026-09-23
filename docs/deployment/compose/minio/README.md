# MinIO setup

After the first start, create the bucket and a user that can only use it
(with the MinIO client `mc`, e.g. `docker compose exec minio sh`):

```sh
mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb local/data
cat > /tmp/scystream.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow",
     "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
     "Resource": ["arn:aws:s3:::data"]},
    {"Effect": "Allow",
     "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
     "Resource": ["arn:aws:s3:::data/*"]}
  ]
}
JSON
mc admin policy create local scystream /tmp/scystream.json
mc admin user add local scystream "<secret>"
mc admin policy attach local scystream --user scystream
mc anonymous set none local/data
```

Use `scystream` / `<secret>` as `DEFAULT_CB_CONFIG_S3_ACCESS_KEY` /
`DEFAULT_CB_CONFIG_S3_SECRET_KEY` for core; compute blocks get them from
core. The browser downloads from `https://s3.example.org` with presigned
URLs; if the frontend fetches files with JavaScript, allow its origin with
`mc admin config set local api cors_allow_origin=https://app.example.org`.
