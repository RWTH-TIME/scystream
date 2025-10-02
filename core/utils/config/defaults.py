from uuid import uuid4
from utils.config.environment import ENV

from services.workflow_service.models.input_output import InputOutput, DataType
from scystream.sdk.env.settings import PostgresSettings, FileSettings


SETTINGS_CLASS = {
    DataType.FILE: FileSettings,
    DataType.PGTABLE: PostgresSettings
}


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


def get_pg_cfg_defaults_dict(io_name: str) -> dict:
    return {
        "PG_USER": ENV.DEFAULT_CB_CONFIG_PG_USER,
        "PG_PASS": ENV.DEFAULT_CB_CONFIG_PG_PASS,
        "PG_HOST": ENV.DEFAULT_CB_CONFIG_PG_HOST,
        "PG_PORT": ENV.DEFAULT_CB_CONFIG_PG_PORT,
        "DB_TABLE": f"table_{io_name}_{uuid4()}",
    }


def extract_default_keys_from_io(
    io: InputOutput
):
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
    default_keys = set(
        settings_class.__annotations__.keys()
    )
    return {
        dk: value for key, value in io.config.items()
        if (dk := next((d for d in default_keys if d in key), None))
    }
