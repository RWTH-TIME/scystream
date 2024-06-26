## Development

Make sure that the core-postgres container is running.

For local development create an `.env` file inside the `/src` directory.
As an example see `src/.env.example`

You can now start the uvicorn server locally with

```sh
uvicorn src.main:app --reload --port <port>
```

### Migrations

We are using [alembic](https://alembic.sqlalchemy.org/en/latest/) as our migration tool.

> [!IMPORTANT]
> When creating a new models directory, be aware to make it a package by creating an `__init__.py`
> and don't forget to import the models in `src/alembic/env.py`

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

| NAME              | DEFAULT VALUE | DESCRIPTION         |
| ----------------- | ------------- | ------------------- |
| DATABASE_HOST     | core-postgres | PostgresDB host     |
| DATABASE_NAME     | core          | PostgresDB name     |
| DATABASE_USER     | core          | PostgresDB user     |
| DATABASE_PASSWORD | core          | PostgresDB password |
| DATABASE_PORT     | 5432          | PostgreDB port      |
| LOG_LEVEL         | INFO          | log-level           |

