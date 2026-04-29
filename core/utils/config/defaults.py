import re
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn, make_dsn

from uuid import UUID, uuid4
from utils.config.environment import ENV

from services.workflow_service.models.input_output import InputOutput, DataType
from scystream.sdk.env.settings import DatabaseSettings, FileSettings


SETTINGS_CLASS = {
    DataType.FILE: FileSettings,
    DataType.DBTABLE: DatabaseSettings,
}


def _normalize_uuid(value: UUID | str) -> str:
    if isinstance(value, str):
        value = UUID(value)  # validates + parses

    hex_value = value.hex  # always 32 chars, no hyphens
    return f"s{hex_value}"


def _normalize_identifier(value: str) -> str:
    value = value.lower()

    # replace spaces and hyphens with underscore
    value = re.sub(r"[ \-]+", "_", value)

    # remove invalid characters (keep a-z, 0-9, _)
    value = re.sub(r"[^a-z0-9_]", "", value)

    # collapse multiple underscores
    value = re.sub(r"_+", "_", value)

    # strip leading/trailing underscores
    value = value.strip("_")

    # ensure it doesn't start with a digit
    if value and value[0].isdigit():
        value = f"t_{value}"

    return value


def _normalize_table_name(io_name: str, compute_block_custom_name: str) -> str:
    max_length = 63

    io_name = _normalize_identifier(io_name)
    compute_block_custom_name = _normalize_identifier(
        compute_block_custom_name
    )

    sep_count = 1
    remaining = max_length - sep_count

    io_len = remaining - len(compute_block_custom_name)
    if io_len < 0:
        io_len = 0

    io_part = io_name[:io_len]

    return f"{io_part}_{compute_block_custom_name}"


def get_file_cfg_defaults_dict(io_name: str) -> dict:
    file_name = f"file_{io_name}_{uuid4()}"
    return {
        "S3_HOST": ENV.DEFAULT_CB_CONFIG_S3_HOST,
        "S3_PORT": ENV.DEFAULT_CB_CONFIG_S3_PORT,
        "S3_ACCESS_KEY": ENV.DEFAULT_CB_CONFIG_S3_ACCESS_KEY,
        "S3_SECRET_KEY": ENV.DEFAULT_CB_CONFIG_S3_SECRET_KEY,
        "BUCKET_NAME": ENV.DEFAULT_CB_CONFIG_S3_BUCKET_NAME,
        "FILE_PATH": ENV.DEFAULT_CB_CONFIG_S3_FILE_PATH,
        "FILE_NAME": file_name,
    }


def _build_pg_dsn() -> str:
    return f"postgresql://{ENV.DEFAULT_CB_CONFIG_PG_USER}:{
        ENV.DEFAULT_CB_CONFIG_PG_PASS
    }@{ENV.DEFAULT_CB_CONFIG_PG_HOST}:{ENV.DEFAULT_CB_CONFIG_PG_PORT}/postgres"


def ensure_schema_exists(dsn: str, schema: str) -> None:
    conn = psycopg2.connect(dsn)
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(schema)
                )
            )
    finally:
        conn.close()


def _to_localhost_dsn(dsn: str) -> str:
    params = parse_dsn(dsn)
    params["host"] = ENV.DEFAULT_CB_CONFIG_PG_HOST_DEV
    params["port"] = ENV.DEFAULT_CB_CONFIG_PG_PORT_DEV
    return make_dsn(**params)


def get_pg_cfg_defaults_dict_with_setup(
    project_uuid: UUID, io_name: str, compute_block_custom_name: str
) -> dict:
    dsn = _build_pg_dsn()
    schema = _normalize_uuid(project_uuid)

    # use local DSN only for setup in dev
    setup_dsn = _to_localhost_dsn(dsn) if ENV.DEVELOPMENT else dsn

    ensure_schema_exists(setup_dsn, schema)

    return {
        "DB_DSN": dsn,
        "DB_TABLE": _normalize_table_name(io_name, compute_block_custom_name),
        "DB_SCHEMA": schema,
    }


def extract_default_keys_from_io(io: InputOutput):
    """
    This class returns a dict that maps the previously prefixed
    default keys values to their default keys.

    e.g.
    d = {
        prefix_S3_HOST: test
    }

    to:

    p = {
        S3_HOST: test
    }
    """
    settings_class = SETTINGS_CLASS.get(io.data_type)
    default_keys = set(settings_class.__annotations__.keys())
    return {
        dk: value
        for key, value in io.config.items()
        if (dk := next((d for d in default_keys if d in key), None))
    }
