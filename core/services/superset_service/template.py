"""Superset dashboard exports used as visualization templates.

A template is a Superset dashboard export bundle (``.zip`` as downloaded
from Superset, or the same content as ``.tar.gz``). To apply it to a
project, only the references of the bundle are changed:

* datasets of the bundle point to the project's datasets (matched by table
  name), or to the project schema if the project has no such table yet
* the database of the bundle is replaced by the scystream data-postgres
  connection
* charts and dashboards get project specific uuids (and slugs), so the same
  template can be used by many projects without them overwriting each other

Superset itself resolves the numeric ids (chart ids in the dashboard layout,
``datasource`` of charts) from these uuids on import.
"""

import io
import re
import tarfile
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from uuid import UUID, uuid5

import yaml

METADATA_FILE_NAME = "metadata.yaml"
BUNDLE_ROOT = "scystream_dashboard"
MAX_BUNDLE_SIZE_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_SIZE_BYTES = 200 * 1024 * 1024
MAX_MEMBERS = 5000

_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
)


class TemplateError(Exception):
    pass


@dataclass
class DatasetRef:
    uuid: str
    schema: str


@dataclass
class TemplateTarget:
    """What a template is applied to."""

    project_uuid: UUID
    schema: str
    database_uuid: str
    database_name: str
    # sqlalchemy uri with the password masked (XXXXXXXXXX), the password is
    # passed to Superset separately
    masked_sqlalchemy_uri: str
    password: str
    datasets: dict[str, DatasetRef] = field(default_factory=dict)


# reading & writing bundles

def _is_safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def _check_member(name: str, total_size: int) -> None:
    if not _is_safe_member(name):
        raise TemplateError(f"Unsafe entry in template: {name}")
    if total_size > MAX_UNCOMPRESSED_SIZE_BYTES:
        raise TemplateError("Template is too large when extracted")


def _read_zip(raw: bytes) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    total = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        infos = bundle.infolist()
        if len(infos) > MAX_MEMBERS:
            raise TemplateError("Template contains too many files")
        for info in infos:
            total += info.file_size
            _check_member(info.filename, total)
            if info.is_dir():
                continue
            files[info.filename] = bundle.read(info)
    return files


def _read_tar(raw: bytes) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as bundle:
        members = bundle.getmembers()
        if len(members) > MAX_MEMBERS:
            raise TemplateError("Template contains too many files")
        for member in members:
            if member.isdir():
                continue
            if not member.isfile():
                raise TemplateError(
                    f"Unsupported entry in template: {member.name}",
                )
            total += member.size
            _check_member(member.name, total)
            extracted = bundle.extractfile(member)
            files[member.name] = extracted.read() if extracted else b""
    return files


def _strip_root(files: dict[str, bytes]) -> dict[str, bytes]:
    """Exports contain a single root folder, which is optional here."""
    if METADATA_FILE_NAME in files:
        return files
    stripped = {}
    for path, data in files.items():
        parts = PurePosixPath(path).parts
        if len(parts) > 1:
            stripped[str(PurePosixPath(*parts[1:]))] = data
    return stripped


def read_bundle(raw: bytes) -> dict[str, bytes]:
    """Reads a template (zip or tar.gz) into {relative path: content}."""
    if not raw:
        raise TemplateError("Template is empty")
    if len(raw) > MAX_BUNDLE_SIZE_BYTES:
        raise TemplateError("Template exceeds the maximum allowed size")

    try:
        if raw[:4] == b"PK\x03\x04":
            files = _read_zip(raw)
        elif raw[:2] == b"\x1f\x8b" or tarfile.is_tarfile(io.BytesIO(raw)):
            files = _read_tar(raw)
        else:
            raise TemplateError(
                "Template must be a Superset export (.zip or .tar.gz)",
            )
    except (zipfile.BadZipFile, tarfile.TarError, EOFError, OSError) as e:
        raise TemplateError(f"Template can not be read: {e}") from e

    files = _strip_root(files)
    validate_files(files)
    return files


def validate_files(files: dict[str, bytes]) -> None:
    if METADATA_FILE_NAME not in files:
        raise TemplateError(
            f"Invalid Superset export: missing {METADATA_FILE_NAME}",
        )
    metadata = _load_yaml(files[METADATA_FILE_NAME])
    if metadata.get("type") != "Dashboard":
        raise TemplateError("The Superset export must contain a dashboard")
    if not any(path.startswith("dashboards/") for path in files):
        raise TemplateError("The Superset export contains no dashboard")


def validate_template(raw: bytes) -> None:
    read_bundle(raw)


def write_bundle(files: dict[str, bytes], root: str = BUNDLE_ROOT) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path, data in sorted(files.items()):
            bundle.writestr(f"{root}/{path}", data)
    return buffer.getvalue()


def normalize_template(raw: bytes) -> bytes:
    """Validates a template and returns it as zip, the format Superset
    imports and exports."""
    return write_bundle(read_bundle(raw))


# applying templates

def _load_yaml(data: bytes) -> dict:
    loaded = yaml.safe_load(data.decode())
    return loaded if isinstance(loaded, dict) else {}


def _dump_yaml(data: dict) -> bytes:
    return yaml.safe_dump(data, sort_keys=False).encode()


def _yaml_files(files: dict[str, bytes], prefix: str):
    for path, data in files.items():
        if path.startswith(prefix) and path.endswith((".yaml", ".yml")):
            yield path, _load_yaml(data)


def _safe_file_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "item"


def _replace_schema(text: str, source: str, target: str) -> str:
    """Replaces schema qualified references in SQL of virtual datasets."""
    if not source or source == target:
        return text
    for quote in ('"', "'"):
        text = text.replace(f"{quote}{source}{quote}.",
                            f"{quote}{target}{quote}.")
    return re.sub(rf"\b{re.escape(source)}\.", f"{target}.", text)


def dashboard_uuids(files: dict[str, bytes]) -> list[str]:
    return [
        str(config["uuid"])
        for _, config in _yaml_files(files, "dashboards/")
        if config.get("uuid")
    ]


def database_yaml(target: TemplateTarget) -> dict:
    return {
        "database_name": target.database_name,
        "sqlalchemy_uri": target.masked_sqlalchemy_uri,
        "cache_timeout": None,
        "expose_in_sqllab": True,
        "allow_run_async": False,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_dml": False,
        "allow_file_upload": False,
        "extra": {},
        "uuid": target.database_uuid,
        "version": "1.0.0",
    }


def apply_template(
    raw: bytes,
    target: TemplateTarget,
) -> tuple[bytes, dict[str, str], list[str]]:
    """Adapts a template to a project.

    Returns the bundle to import, the database passwords for the import and
    the uuids of the dashboards in the bundle.
    """
    files = read_bundle(raw)

    def project_uuid(old: str) -> str:
        return str(uuid5(target.project_uuid, old))

    uuid_map: dict[str, str] = {}
    adapted: dict[str, bytes] = {
        METADATA_FILE_NAME: files[METADATA_FILE_NAME],
    }

    # database -> the scystream data-postgres connection
    for _, config in _yaml_files(files, "databases/"):
        if config.get("uuid"):
            uuid_map[str(config["uuid"])] = target.database_uuid
    database_path = (
        f"databases/{_safe_file_name(target.database_name)}.yaml"
    )
    adapted[database_path] = _dump_yaml(database_yaml(target))

    # datasets -> the project's datasets
    for path, config in _yaml_files(files, "datasets/"):
        old_uuid = str(config.get("uuid", ""))
        source_schema = config.get("schema")
        existing = target.datasets.get(config.get("table_name"))
        if existing:
            new_uuid, schema = existing.uuid, existing.schema
        else:
            new_uuid, schema = project_uuid(old_uuid), target.schema
        if old_uuid:
            uuid_map[old_uuid] = new_uuid

        config["uuid"] = new_uuid
        config["schema"] = schema
        config["database_uuid"] = target.database_uuid
        config.pop("catalog", None)
        if isinstance(config.get("sql"), str):
            config["sql"] = _replace_schema(
                config["sql"], source_schema, schema,
            )
        name = _safe_file_name(f"{schema}.{config.get('table_name')}")
        adapted[f"datasets/{_safe_file_name(target.database_name)}/"
                f"{name}.yaml"] = _dump_yaml(config)

    # charts & dashboards -> project specific copies
    for prefix in ("charts/", "dashboards/"):
        for path, config in _yaml_files(files, prefix):
            if config.get("uuid"):
                uuid_map[str(config["uuid"])] = project_uuid(
                    str(config["uuid"]),
                )
            if prefix == "dashboards/" and config.get("slug"):
                config["slug"] = (
                    f"{config['slug']}-{target.project_uuid.hex[:8]}"
                )
            adapted[path] = _dump_yaml(config)

    # rewrite every reference (dataset_uuid of charts, chart uuids in the
    # dashboard layout, dataset uuids of native filters, ...)
    def remap(match: re.Match) -> str:
        return uuid_map.get(match.group(0), match.group(0))

    for path in list(adapted):
        if path == METADATA_FILE_NAME or path.startswith("databases/"):
            continue
        adapted[path] = _UUID_RE.sub(remap, adapted[path].decode()).encode()

    # Superset strips the bundle root from the paths passwords refer to
    passwords = {database_path: target.password}
    return write_bundle(adapted), passwords, dashboard_uuids(adapted)
