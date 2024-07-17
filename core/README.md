## Development

Make sure that the core-postgres container is running.

For local development create an `.env` file inside the `/src` directory.
As an example see `src/.env.example`

You can now start the uvicorn server locally with

```sh
uvicorn main:app --reload --port <port>
```

### Migrations

We are using [alembic](https://alembic.sqlalchemy.org/en/latest/) as our migration tool.

> [!IMPORTANT]
> When creating a new models, don't forget to import them in `src/alembic/env.py` 

To create a migration, run

```sh
alembic revision --autogenerate -m {accurate description of what happens}
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
