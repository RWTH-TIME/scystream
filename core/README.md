## Development

Make sure that the core-postgres container is running.

For local development create an `.env` file inside the `/core` directory.
As an example see `core/.env.example`

Make sure you are in the `../core` directory

You can now start the uvicorn server locally with

```sh
uvicorn main:app --reload --port <port>
```

### Migrations

We are using [alembic](https://alembic.sqlalchemy.org/en/latest/) as our migration tool.

> [!IMPORTANT]
> When creating a new models, don't forget store them in `services/<YOUR_SERVICE>/models/<YOUR_MODEL>.py`

To create a migration, run

```sh
alembic revision --autogenerate -m "accurate description of what happens"
```

After creating the revision, please check `src/alembic/versions/{accurate-description}.py`
if the migration is correct, and does what it should do.

To migrate now run

```sh
alembic upgrade head
```

### Environment Variables

| NAME                              | DEFAULT VALUE             | DESCRIPTION                               |
| ----------------------------------| --------------------------| ------------------------------------------|
| DEVELOPMENT                       | False                     | Sets Development Mode. Set it to True when running core locally, NEVER use when running core in a docker container |
| DATABASE_HOST                     | core-postgres             | PostgresDB host                           |
| DATABASE_NAME                     | core                      | PostgresDB name                           |
| DATABASE_USER                     | core                      | PostgresDB user                           |
| DATABASE_PASSWORD                 | core                      | PostgresDB password                       |
| DATABASE_PORT                     | 5432                      | PostgreDB port                            |
| LOG_LEVEL                         | INFO                      | log-level                                 |
| EMAIL_DOMAIN_WHITELIST            | ["time.rwth-aachen.de"]   | only these domains are allowed to sign up |
| JWT_ALGORITHM                     | HS256                     | algorithm for jwt token generation        |
| JWT_SECRET                        | secret                    | secret for jwt token generation           |
| JWT_ACCES_TOKEN_EXPIRE_MIN        | 15                        | access token expire time in minutes       |
| JWT_REFRESH_TOKEN_EXPIRE_DAYS     | 30                        | refresh token expire time in days         |
| EXTERNAL_URL_DATA_S3              | http://localhost:9000     | Externally reachable URL with Port of Minio provided for compute block storage. Make sure that this reaches the same Minio provided by the following config defaults. |

#### File Output Defaults

The following Environment Variables define the defaults that the Compute Blocks Outputs of type `File` & `DB` will be populated with.

It is very important that the given configs are reachable from the airflow containers. They dont need to be
externally reachable.

| NAME                              | DEFAULT VALUE             | DESCRIPTION                               |
| ----------------------------------| --------------------------| ------------------------------------------|
| DEFAULT_CB_CONFIG_S3_HOST         | http://data-minio         | Default Host of the data Minio.         |
| DEFAULT_CB_CONFIG_S3_PORT         | 9000                      | Default Port of the data Minio.         |
| DEFAULT_CB_CONFIG_S3_ACCESS_KEY   | minioadmin                | Access Key of the data Minio.         |
| DEFAULT_CB_CONFIG_S3_SECRET_KEY   | minioadmin                | Secret Key of the data Minio.         |
| DEFAULT_CB_CONFIG_S3_BUCKET_NAME  | data                      | Default Bucket value of the data Minio.         |
| DEFAULT_CB_CONFIG_S3_FILE_PATH    | /                         | Default File Path of the data Minio.         |
| DEFAULT_CB_CONFIG_PG_USER         | postgres         | User of the data postgres.         |
| DEFAULT_CB_CONFIG_PG_PASS         | postgres                      | Password for the data postgres.         |
| DEFAULT_CB_CONFIG_PG_HOST         | data-postgres | Host of the data postgres.         |
| DEFAULT_CB_CONFIG_PG_PORT         | 5432 | Port of the data postgres.         |
