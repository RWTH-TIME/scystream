import io
import zipfile
from uuid import UUID

import pytest
import yaml
from services.superset_service import export_adapter
from services.superset_service.dashboard_import_controller import (
    _extract_dashboard_uuids,
)
from services.superset_service.export_adapter import (
    ExportAdapterError,
    adapt_export_zip,
    validate_dashboard_export_zip,
)
from tests.superset.export_fixture import (
    DASHBOARD_UUID,
    SOURCE_SCHEMA,
    build_export_zip,
    read_zip,
)

PROJECT_UUID = UUID("0b6f3c0e-8a51-4d6c-9a57-6f1f8f0e2c11")
TARGET_SCHEMA = "s0b6f3c0e8a514d6c9a576f1f8f0e2c11"


@pytest.fixture
def adapted():
    raw, passwords = adapt_export_zip(build_export_zip(), PROJECT_UUID)
    return read_zip(raw), passwords


def test_schema_is_rewritten_everywhere(adapted):
    files, _ = adapted

    assert not any(SOURCE_SCHEMA in path for path in files)
    assert not any(SOURCE_SCHEMA in content for content in files.values())

    dataset = yaml.safe_load(
        files["datasets/data_postgres/topics.yaml"],
    )
    assert dataset["schema"] == TARGET_SCHEMA
    assert dataset["sql"] == (
        f'SELECT * FROM "{TARGET_SCHEMA}".topics JOIN {TARGET_SCHEMA}.docs'
    )


def test_database_points_to_data_postgres(adapted):
    files, passwords = adapted
    env = export_adapter.ENV

    database = yaml.safe_load(files["databases/data_postgres.yaml"])
    assert database["sqlalchemy_uri"] == (
        f"postgresql+psycopg2://{env.DEFAULT_CB_CONFIG_PG_USER}:"
        f"{env.DEFAULT_CB_CONFIG_PG_PASS}@{env.DEFAULT_CB_CONFIG_PG_HOST}:"
        f"{env.DEFAULT_CB_CONFIG_PG_PORT}/postgres"
    )
    assert "schema" not in database["extra"]
    assert passwords == {
        "databases/data_postgres.yaml": env.DEFAULT_CB_CONFIG_PG_PASS,
    }


def test_metadata_is_kept_and_bundle_has_single_root(adapted):
    raw, _ = adapt_export_zip(build_export_zip(), PROJECT_UUID)
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        roots = {name.split("/", 1)[0] for name in bundle.namelist()}
    assert roots == {"dashboard_export_adapted"}

    files, _ = adapted
    assert files["metadata.yaml"] == read_zip(build_export_zip())[
        "metadata.yaml"
    ]


def test_dashboard_uuids_are_extracted():
    raw, _ = adapt_export_zip(build_export_zip(), PROJECT_UUID)
    assert _extract_dashboard_uuids(raw) == [DASHBOARD_UUID]


def test_adapting_is_idempotent_for_target_schema():
    raw, _ = adapt_export_zip(build_export_zip(), PROJECT_UUID)
    raw_again, _ = adapt_export_zip(raw, PROJECT_UUID)
    assert read_zip(raw_again) == read_zip(raw)


def test_missing_metadata_is_rejected():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr("export/dashboards/x.yaml", "uuid: x")

    with pytest.raises(ExportAdapterError, match="metadata.yaml"):
        validate_dashboard_export_zip(buffer.getvalue())


def test_path_traversal_is_rejected():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr("../evil.yaml", "x")

    with pytest.raises(ExportAdapterError, match="Unsafe"):
        adapt_export_zip(buffer.getvalue(), PROJECT_UUID)


def test_multiple_schemas_are_rejected():
    raw = build_export_zip(
        extra_files={
            "datasets/data_postgres/other.yaml": yaml.safe_dump(
                {"table_name": "x", "schema": "other"},
            ),
        },
    )
    with pytest.raises(ExportAdapterError, match="multiple schemas"):
        adapt_export_zip(raw, PROJECT_UUID)


def test_export_without_datasets_is_rejected():
    raw = build_export_zip()
    files = {
        path: content
        for path, content in read_zip(raw).items()
        if not path.startswith("datasets/")
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for path, content in files.items():
            bundle.writestr(f"root/{path}", content)

    with pytest.raises(ExportAdapterError, match="No dataset schema"):
        adapt_export_zip(buffer.getvalue(), PROJECT_UUID)


def test_oversized_zip_is_rejected(monkeypatch):
    monkeypatch.setattr(export_adapter, "MAX_ZIP_SIZE_BYTES", 10)
    with pytest.raises(ExportAdapterError, match="maximum allowed size"):
        adapt_export_zip(build_export_zip(), PROJECT_UUID)
