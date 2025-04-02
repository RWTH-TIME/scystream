from uuid import uuid4
from utils.config.environment import ENV


def get_file_cfg_defaults_dict(io_name: str) -> dict:
    return {
        "S3_HOST": ENV.DEFAULT_CB_CONFIG_S3_HOST,
        "S3_PORT": ENV.DEFAULT_CB_CONFIG_S3_PORT,
        "S3_ACCESS_KEY": ENV.DEFAULT_CB_CONFIG_S3_ACCESS_KEY,
        "S3_SECRET_KEY": ENV.DEFAULT_CB_CONFIG_S3_SECRET_KEY,
        "BUCKET_NAME": ENV.DEFAULT_CB_CONFIG_S3_BUCKET_NAME,
        "FILE_PATH": ENV.DEFAULT_CB_CONFIG_S3_FILE_PATH,
        "FILE_NAME": f"file_{io_name}_{uuid4()}",
    }


def get_pg_cfg_defaults_dict(io_name: str) -> dict:
    return {
        "PG_USER": ENV.DEFAULT_CB_CONFIG_PG_USER,
        "PG_PASS": ENV.DEFAULT_CB_CONFIG_PG_PASS,
        "PG_HOST": ENV.DEFAULT_CB_CONFIG_S3_HOST,
        "PG_PORT": ENV.DEFAULT_CB_CONFIG_PG_PORT,
        "DB_TABLE": f"table_{io_name}_{uuid4()}",
    }
