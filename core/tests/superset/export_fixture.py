import io
import tarfile
import zipfile

import yaml

SOURCE_SCHEMA = "s00000000000000000000000000000000"
DATABASE_UUID = "6f1e0b7c-4a8d-4e5f-9a1b-2c3d4e5f6a7b"
DATASET_UUID = "9b8a7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d"
VIRTUAL_DATASET_UUID = "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
CHART_UUID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
DASHBOARD_UUID = "d7a4c1f2-0b9e-4a39-9a63-1b1c5d7e8f90"


def export_files(schema: str = SOURCE_SCHEMA) -> dict[str, str]:
    """A Superset dashboard export (v1 format) with a physical and a
    virtual dataset, a chart and a dashboard with a native filter."""
    return {
        "metadata.yaml": yaml.safe_dump({
            "version": "1.0.0",
            "type": "Dashboard",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }),
        "databases/template_db.yaml": yaml.safe_dump({
            "database_name": "template_db",
            "sqlalchemy_uri":
                "postgresql+psycopg2://u:XXXXXXXXXX@old-host:5432/x",
            "extra": {"engine_params": {}},
            "uuid": DATABASE_UUID,
            "version": "1.0.0",
        }),
        "datasets/template_db/topics.yaml": yaml.safe_dump({
            "table_name": "topics",
            "schema": schema,
            "catalog": "x",
            "sql": None,
            "uuid": DATASET_UUID,
            "database_uuid": DATABASE_UUID,
            "columns": [{"column_name": "topic"}],
            "version": "1.0.0",
        }),
        "datasets/template_db/top_topics.yaml": yaml.safe_dump({
            "table_name": "top_topics",
            "schema": schema,
            "sql": f'SELECT * FROM "{schema}".topics JOIN {schema}.docs',
            "uuid": VIRTUAL_DATASET_UUID,
            "database_uuid": DATABASE_UUID,
            "version": "1.0.0",
        }),
        "charts/Topics_1.yaml": yaml.safe_dump({
            "slice_name": "Topics",
            "viz_type": "table",
            "params": {"datasource": "1__table", "viz_type": "table"},
            "uuid": CHART_UUID,
            "dataset_uuid": DATASET_UUID,
            "version": "1.0.0",
        }),
        "dashboards/Overview_1.yaml": yaml.safe_dump({
            "dashboard_title": "Overview",
            "slug": "overview",
            "uuid": DASHBOARD_UUID,
            "position": {
                "CHART-1": {
                    "type": "CHART",
                    "meta": {"chartId": 1, "uuid": CHART_UUID},
                },
            },
            "metadata": {
                "native_filter_configuration": [{
                    "targets": [{"datasetUuid": DATASET_UUID,
                                 "column": {"name": "topic"}}],
                }],
            },
            "version": "1.0.0",
        }),
    }


def build_export_zip(
    files: dict[str, str] | None = None,
    root: str = "dashboard_export_20260101T000000",
) -> bytes:
    files = export_files() if files is None else files
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for path, content in files.items():
            bundle.writestr(f"{root}/{path}" if root else path, content)
    return buffer.getvalue()


def build_export_tar_gz(
    files: dict[str, str] | None = None,
    root: str = "dashboard_export_20260101T000000",
) -> bytes:
    files = export_files() if files is None else files
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as bundle:
        for path, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(f"{root}/{path}" if root else path)
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def read_zip(raw: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        return {
            name.split("/", 1)[1]: bundle.read(name).decode()
            for name in bundle.namelist()
        }
