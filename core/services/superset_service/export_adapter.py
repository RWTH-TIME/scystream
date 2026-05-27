import io
import logging
import re
import zipfile
from pathlib import PurePosixPath
from urllib.parse import quote_plus
from uuid import UUID

import yaml

from utils.config.defaults import _normalize_uuid
from utils.config.environment import ENV

logger = logging.getLogger(__name__)

METADATA_FILE_NAME = "metadata.yaml"
MAX_ZIP_SIZE_BYTES = 50 * 1024 * 1024


class ExportAdapterError(Exception):
    pass


def _is_safe_zip_member(name: str) -> bool:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        return False
    return True


def _read_zip_contents(raw_zip: bytes) -> dict[str, bytes]:
    if len(raw_zip) > MAX_ZIP_SIZE_BYTES:
        raise ExportAdapterError("Export zip exceeds maximum allowed size")

    contents: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as bundle:
        for name in bundle.namelist():
            if not _is_safe_zip_member(name):
                raise ExportAdapterError(f"Unsafe zip entry: {name}")
            if name.endswith("/"):
                continue
            contents[name] = bundle.read(name)
    return contents


def _strip_zip_root(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) <= 1:
        return path
    return str(PurePosixPath(*parts[1:]))


def _normalize_zip_paths(contents: dict[str, bytes]) -> dict[str, bytes]:
    normalized: dict[str, bytes] = {}
    for path, data in contents.items():
        normalized[_strip_zip_root(path)] = data
    return normalized


def _validate_export_zip(contents: dict[str, bytes]) -> None:
    if METADATA_FILE_NAME not in contents:
        raise ExportAdapterError(
            f"Invalid Superset export: missing {METADATA_FILE_NAME}"
        )


def _load_yaml_text(text: str) -> dict:
    loaded = yaml.safe_load(text)
    return loaded if isinstance(loaded, dict) else {}


def _dump_yaml_text(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False)


def _detect_source_schemas(contents: dict[str, bytes]) -> set[str]:
    schemas: set[str] = set()
    for path, data in contents.items():
        if (
            not path.startswith("datasets/")
            or not path.endswith((".yaml", ".yml"))
        ):
            continue
        config = _load_yaml_text(data.decode())
        schema = config.get("schema")
        if schema:
            schemas.add(str(schema))
    if not schemas:
        raise ExportAdapterError("No dataset schema found in export zip")
    if len(schemas) > 1:
        raise ExportAdapterError(
            f"Export contains multiple schemas: {sorted(schemas)}"
        )
    return schemas


def _build_pg_sqlalchemy_uri() -> str:
    user = quote_plus(ENV.DEFAULT_CB_CONFIG_PG_USER)
    password = quote_plus(ENV.DEFAULT_CB_CONFIG_PG_PASS)
    host = ENV.DEFAULT_CB_CONFIG_PG_HOST
    port = ENV.DEFAULT_CB_CONFIG_PG_PORT
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/postgres"


def _replace_schema_in_text(
    text: str,
    source_schema: str,
    target_schema: str,
) -> str:
    patterns = [
        (rf'"{re.escape(source_schema)}"\.', f'"{target_schema}".'),
        (rf"'{re.escape(source_schema)}'\.", f"'{target_schema}'."),
        (rf"\b{re.escape(source_schema)}\.", f"{target_schema}."),
    ]
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    return result


def _rewrite_database_yaml(config: dict, target_schema: str) -> dict:
    config["sqlalchemy_uri"] = _build_pg_sqlalchemy_uri()
    extra = config.get("extra")
    if isinstance(extra, str):
        try:
            extra = yaml.safe_load(extra) or {}
        except yaml.YAMLError:
            extra = {}
    if not isinstance(extra, dict):
        extra = {}
    extra["schema"] = target_schema
    config["extra"] = extra
    return config


def _rewrite_yaml_content(
    text: str,
    source_schema: str,
    target_schema: str,
    prefix: str,
) -> str:
    config = _load_yaml_text(text)
    if prefix == "datasets/" and "schema" in config:
        config["schema"] = target_schema
    if prefix == "databases/":
        config = _rewrite_database_yaml(config, target_schema)
    for key in ("sql", "select_sql", "where"):
        if key in config and isinstance(config[key], str):
            config[key] = _replace_schema_in_text(
                config[key], source_schema, target_schema
            )
    dumped = _dump_yaml_text(config)
    return _replace_schema_in_text(dumped, source_schema, target_schema)


def _rename_path_if_contains_schema(
    path: str,
    source_schema: str,
    target_schema: str,
) -> str:
    parts = list(PurePosixPath(path).parts)
    renamed = [
        target_schema if part == source_schema else part
        for part in parts
    ]
    return str(PurePosixPath(*renamed))


def adapt_export_zip(
    raw_zip: bytes,
    project_uuid: UUID,
) -> tuple[bytes, dict[str, str]]:
    contents = _normalize_zip_paths(_read_zip_contents(raw_zip))
    _validate_export_zip(contents)

    source_schemas = _detect_source_schemas(contents)
    source_schema = next(iter(source_schemas))
    target_schema = _normalize_uuid(project_uuid)

    adapted: dict[str, bytes] = {}
    for path, data in contents.items():
        if path == METADATA_FILE_NAME:
            adapted[path] = data
            continue

        prefix = path.split("/")[0] + "/" if "/" in path else ""
        text = data.decode()
        if (
            prefix in {"datasets/", "databases/", "charts/", "dashboards/"}
            and path.endswith((".yaml", ".yml"))
        ):
            text = _rewrite_yaml_content(
                text,
                source_schema,
                target_schema,
                prefix,
            )
        else:
            text = _replace_schema_in_text(text, source_schema, target_schema)

        new_path = _rename_path_if_contains_schema(
            path,
            source_schema,
            target_schema,
        )
        adapted[new_path] = text.encode()

    passwords: dict[str, str] = {}
    for path in adapted:
        if path.startswith("databases/") and path.endswith((".yaml", ".yml")):
            passwords[path] = ENV.DEFAULT_CB_CONFIG_PG_PASS

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as bundle:
        root = "dashboard_export_adapted"
        for path, data in adapted.items():
            bundle.writestr(f"{root}/{path}", data)

    return buffer.getvalue(), passwords


def validate_dashboard_export_zip(raw_zip: bytes) -> None:
    contents = _normalize_zip_paths(_read_zip_contents(raw_zip))
    _validate_export_zip(contents)
