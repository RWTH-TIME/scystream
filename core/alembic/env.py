from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from utils.database.connection import SQLALCHEMY_DATABASE_URL, Base

"""
Import all your models here.
We need to load all models or alembic will not recognize table changes,
Keep in mind to ignore the linting in this case, we do not use these models
"""
import sys
from pathlib import Path

START_DIRECTORY = "services"
MODELS_DIRECTORY = "models"

services_path = Path(START_DIRECTORY).resolve()
sys.path.insert(0, str(services_path.parent))


for models_dir in services_path.rglob(MODELS_DIRECTORY):
    if models_dir.is_dir():
        package_parts = models_dir.relative_to(services_path.parent).parts
        base_package = ".".join(package_parts)

        for py_file in models_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            module_name = py_file.stem
            full_module = f"{base_package}.{module_name}"

            __import__(full_module)

"""
END OF DYNAMIC IMPORT LOGIC
"""


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# set sqlalchemy db url from configuration
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


####
# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.metadata
####
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
