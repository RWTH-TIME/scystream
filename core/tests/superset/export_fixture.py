import io
import zipfile

import yaml

SOURCE_SCHEMA = "s00000000000000000000000000000000"
DASHBOARD_UUID = "d7a4c1f2-0b9e-4a39-9a63-1b1c5d7e8f90"


def build_export_zip(
    schema: str = SOURCE_SCHEMA,
    extra_files: dict[str, str] | None = None,
    root: str = "dashboard_export_20260101T000000",
) -> bytes:
    """Builds a minimal Superset dashboard export bundle (v1 format)."""
    files = {
        "metadata.yaml": yaml.safe_dump({
            "version": "1.0.0",
            "type": "Dashboard",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }),
        "databases/data_postgres.yaml": yaml.safe_dump({
            "database_name": "data_postgres",
            "sqlalchemy_uri": "postgresql+psycopg2://u:XXXXXXXXXX@old:5432/x",
            "extra": '{"schema": "' + schema + '"}',
            "uuid": "6f1e0b7c-4a8d-4e5f-9a1b-2c3d4e5f6a7b",
            "version": "1.0.0",
        }),
        "datasets/data_postgres/topics.yaml": yaml.safe_dump({
            "table_name": "topics",
            "schema": schema,
            "sql": f'SELECT * FROM "{schema}".topics JOIN {schema}.docs',
            "uuid": "9b8a7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d",
            "database_uuid": "6f1e0b7c-4a8d-4e5f-9a1b-2c3d4e5f6a7b",
            "version": "1.0.0",
        }),
        "charts/topics_1.yaml": yaml.safe_dump({
            "slice_name": "Topics",
            "viz_type": "table",
            "params": {"adhoc_filters": []},
            "query_context": None,
            "uuid": "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
            "dataset_uuid": "9b8a7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d",
            "version": "1.0.0",
        }),
        "dashboards/overview_1.yaml": yaml.safe_dump({
            "dashboard_title": "Overview",
            "uuid": DASHBOARD_UUID,
            "position": {},
            "metadata": {},
            "version": "1.0.0",
        }),
    }
    files.update(extra_files or {})

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for path, content in files.items():
            bundle.writestr(f"{root}/{path}" if root else path, content)
    return buffer.getvalue()


def read_zip(raw: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        return {
            name.split("/", 1)[1]: bundle.read(name).decode()
            for name in bundle.namelist()
        }
