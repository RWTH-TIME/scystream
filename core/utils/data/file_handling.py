import boto3
import logging
from collections import defaultdict
from uuid import UUID

from utils.config.environment import ENV
from services.workflow_service.models.input_output import InputOutput, DataType
from utils.config.defaults import (
    get_file_cfg_defaults_dict, extract_default_keys_from_io
)
from botocore.exceptions import (
    EndpointConnectionError,
    NoCredentialsError,
    BotoCoreError
)
from botocore.client import BaseClient


def get_s3_client(
    s3_url: str,
    access_key: str,
    secret_key: str
) -> BaseClient | None:
    try:
        return boto3.client(
            "s3",
            endpoint_url=s3_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    except EndpointConnectionError as e:
        logging.warning(f"Cannot reach S3 endpoint {s3_url}: {e}")
    except NoCredentialsError:
        logging.warning("Missing or invalid AWS credentials")
    except BotoCoreError as e:
        logging.warning(f"Boto3 core error while creating client: {e}")
    except Exception as e:
        logging.exception(f"Unexpected error creating S3 client: {e}")

    return None


def find_file_with_prefix(
    client,
    bucket_name: str,
    file_path: str,
    file_prefix: str
) -> str | None:
    try:
        response = client.list_objects_v2(
            Bucket=bucket_name, Prefix=file_path.strip("/"))

        if "Contents" not in response:
            return None

        for obj in response["Contents"]:
            filename = obj["Key"]

            if file_prefix in filename:
                # File_Prefix contains a uuid and is therefore unique
                return filename

        return None
    except Exception as e:
        logging.error(f"Error finding file with prefix {
                      file_prefix} on S3: {e}")
        return None


def generate_presigned_url(
    client,
    bucket_name: str,
    file_path: str,
    expiration: int = 86400  # 1 day
):
    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_path},
            ExpiresIn=expiration,
        )
        return url
    except Exception as e:
        logging.error(
            f"Error generating pre-signed URL for {file_path}: {e}")


def get_minio_url(
    s3_host: str,
    s3_port: int
):
    """
    If we are currently running in DEVELOPMENT mode, we cannot access minio
    using its Docker internal hostname. Therefore, if the Docker internal
    HOST & PORT are set, we replace them with values to ensure
    external accessability even if the core is not running as a container.
    """
    if not ENV.DEVELOPMENT:
        return f"{s3_host}:{str(s3_port)}"

    defaults = get_file_cfg_defaults_dict("placeholder")
    if (
        s3_host == defaults.get("S3_HOST") and
        s3_port == defaults.get("S3_PORT")
    ):
        return f"{ENV.EXTERNAL_URL_DATA_S3}"

    return f"{s3_host}:{str(s3_port)}"


REQUIRED_CONFIG_KEYS = {
    "S3_HOST",
    "S3_PORT",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
    "BUCKET_NAME",
}


def bulk_presigned_urls_from_ios(ios: list[InputOutput]) -> dict[UUID, str]:
    """
    Generates presigned URLs for FILE-type InputOutputs.
    Skips IOs with missing config values.
    Optimized by grouping IOs by S3 config to reuse clients.
    """
    result = {}
    io_groups = defaultdict(list)

    for io in ios:
        if io.data_type != DataType.FILE:
            continue

        config = extract_default_keys_from_io(io)
        if not config:
            continue

        # Skip if any required config is missing or empty
        if not REQUIRED_CONFIG_KEYS.issubset(config) or any(
            not config.get(k) for k in REQUIRED_CONFIG_KEYS
        ):
            logging.warning(
                f"Skipping IO {io.uuid} due to missing or empty config")
            continue

        group_key = (
            config["S3_HOST"],
            config["S3_PORT"],
            config["S3_ACCESS_KEY"],
            config["S3_SECRET_KEY"],
            config["BUCKET_NAME"],
        )
        io_groups[group_key].append((io, config))

    for (host, port, access, secret, bucket), group in io_groups.items():
        s3_url = get_minio_url(host, port)
        client = get_s3_client(s3_url, access, secret)
        if not client:
            logging.warning(f"Could not create S3 client for {host}:{port}")
            continue

        for io, cfg in group:
            full_file_path = find_file_with_prefix(
                client,
                bucket_name=cfg["BUCKET_NAME"],
                file_path=cfg["FILE_PATH"],
                file_prefix=cfg["FILE_NAME"]
            )
            if not full_file_path:
                logging.warning(f"No file found for IO {io.uuid}")
                continue

            presigned_url = generate_presigned_url(
                client,
                bucket_name=cfg["BUCKET_NAME"],
                file_path=full_file_path
            )
            if presigned_url:
                result[io.uuid] = presigned_url
            else:
                logging.warning(f"Failed to generate presigned URL for {
                                full_file_path}")

    return result


def get_presigned_post_url(
    client,
    bucket_name: str,
    file_name: str,
    expiration: int = 86400  # 1 day
) -> str:
    """
    This function generates and returns a put url for a file to be
    uploaded to our default minio bucket.
    """
    url = client.generate_presigned_post(
        bucket_name,
        file_name,
        ExpiresIn=expiration
    )
    return url
