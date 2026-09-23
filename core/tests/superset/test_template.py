import io
import tarfile
import zipfile
from uuid import UUID, uuid5

import pytest
import yaml
from services.superset_service import template as tpl
from tests.superset.export_fixture import (
    CHART_UUID,
    DASHBOARD_UUID,
    DATABASE_UUID,
    DATASET_UUID,
    SOURCE_SCHEMA,
    VIRTUAL_DATASET_UUID,
    build_export_tar_gz,
    build_export_zip,
    export_files,
    read_zip,
)

PROJECT = UUID("0b6f3c0e-8a51-4d6c-9a57-6f1f8f0e2c11")
PROJECT_SCHEMA = "s0b6f3c0e8a514d6c9a576f1f8f0e2c11"
TARGET_DATABASE_UUID = "11111111-2222-4333-8444-555555555555"
TARGET_DATASET_UUID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"


def _target(project=PROJECT, schema=PROJECT_SCHEMA, datasets=None):
    return tpl.TemplateTarget(
        project_uuid=project,
        schema=schema,
        database_uuid=TARGET_DATABASE_UUID,
        database_name="scystream-data",
        masked_sqlalchemy_uri=(
            "postgresql+psycopg2://postgres:XXXXXXXXXX@data-postgres:5432/"
            "postgres"
        ),
        password="secret",
        datasets={"topics": tpl.DatasetRef(TARGET_DATASET_UUID, schema)}
        if datasets is None else datasets,
    )


def _apply(raw=None, target=None):
    bundle, passwords, dashboards = tpl.apply_template(
        raw or build_export_zip(), target or _target(),
    )
    files = {
        path: yaml.safe_load(content)
        for path, content in read_zip(bundle).items()
    }
    return files, passwords, dashboards


def _by_prefix(files, prefix):
    return [c for p, c in files.items() if p.startswith(prefix)]


# reading bundles

@pytest.mark.parametrize("builder", [build_export_zip, build_export_tar_gz])
@pytest.mark.parametrize("root", ["dashboard_export_1", ""])
def test_bundles_are_read_with_and_without_root(builder, root):
    files = tpl.read_bundle(builder(root=root))
    assert set(files) == set(export_files())


def test_normalized_template_is_a_zip_with_single_root():
    raw = tpl.normalize_template(build_export_tar_gz())
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        roots = {name.split("/", 1)[0] for name in bundle.namelist()}
    assert roots == {tpl.BUNDLE_ROOT}
    assert set(tpl.read_bundle(raw)) == set(export_files())


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"", "empty"),
        (b"no archive at all", "must be a Superset export"),
        (b"PK\x03\x04broken", "can not be read"),
    ],
)
def test_invalid_archives_are_rejected(raw, message):
    with pytest.raises(tpl.TemplateError, match=message):
        tpl.read_bundle(raw)


def test_missing_metadata_is_rejected():
    files = export_files()
    del files["metadata.yaml"]
    with pytest.raises(tpl.TemplateError, match="metadata.yaml"):
        tpl.read_bundle(build_export_zip(files))


def test_non_dashboard_exports_are_rejected():
    files = export_files()
    files["metadata.yaml"] = yaml.safe_dump({"type": "Chart"})
    with pytest.raises(tpl.TemplateError, match="dashboard"):
        tpl.read_bundle(build_export_zip(files))


def test_export_without_dashboard_is_rejected():
    files = {
        p: c for p, c in export_files().items()
        if not p.startswith("dashboards/")
    }
    with pytest.raises(tpl.TemplateError, match="no dashboard"):
        tpl.read_bundle(build_export_zip(files))


def test_path_traversal_is_rejected():
    files = export_files()
    files["../evil.yaml"] = "x"
    with pytest.raises(tpl.TemplateError, match="Unsafe"):
        tpl.read_bundle(build_export_zip(files, root=""))


def test_tar_links_are_rejected():
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as bundle:
        link = tarfile.TarInfo("x/metadata.yaml")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/passwd"
        bundle.addfile(link)
    with pytest.raises(tpl.TemplateError, match="Unsupported"):
        tpl.read_bundle(buffer.getvalue())


def test_oversized_templates_are_rejected(monkeypatch):
    monkeypatch.setattr(tpl, "MAX_BUNDLE_SIZE_BYTES", 10)
    with pytest.raises(tpl.TemplateError, match="maximum allowed size"):
        tpl.read_bundle(build_export_zip())


def test_zip_bombs_are_rejected(monkeypatch):
    monkeypatch.setattr(tpl, "MAX_UNCOMPRESSED_SIZE_BYTES", 100)
    with pytest.raises(tpl.TemplateError, match="too large"):
        tpl.read_bundle(build_export_zip())


# applying templates

def test_database_is_replaced_by_the_data_postgres_connection():
    files, passwords, _ = _apply()

    databases = _by_prefix(files, "databases/")
    assert databases == [{
        **tpl.database_yaml(_target()),
    }]
    assert passwords == {"databases/scystream-data.yaml": "secret"}
    assert all(
        d["database_uuid"] == TARGET_DATABASE_UUID
        for d in _by_prefix(files, "datasets/")
    )
    assert not any(
        DATABASE_UUID in yaml.safe_dump(c) for c in files.values()
    )


def test_datasets_point_to_the_project_datasets():
    files, _, _ = _apply()
    datasets = {d["table_name"]: d for d in _by_prefix(files, "datasets/")}

    assert datasets["topics"]["uuid"] == TARGET_DATASET_UUID
    assert datasets["topics"]["schema"] == PROJECT_SCHEMA
    assert "catalog" not in datasets["topics"]
    # columns & metrics of the template are kept
    assert datasets["topics"]["columns"] == [{"column_name": "topic"}]


def test_unknown_datasets_get_project_uuids_and_schema():
    files, _, _ = _apply()
    virtual = next(
        d for d in _by_prefix(files, "datasets/")
        if d["table_name"] == "top_topics"
    )
    assert virtual["uuid"] == str(uuid5(PROJECT, VIRTUAL_DATASET_UUID))
    assert virtual["schema"] == PROJECT_SCHEMA
    assert virtual["sql"] == (
        f'SELECT * FROM "{PROJECT_SCHEMA}".topics JOIN {PROJECT_SCHEMA}.docs'
    )


def test_references_are_remapped():
    files, _, dashboards = _apply()
    chart = _by_prefix(files, "charts/")[0]
    dashboard = _by_prefix(files, "dashboards/")[0]

    new_chart_uuid = str(uuid5(PROJECT, CHART_UUID))
    new_dashboard_uuid = str(uuid5(PROJECT, DASHBOARD_UUID))
    assert chart["uuid"] == new_chart_uuid
    assert chart["dataset_uuid"] == TARGET_DATASET_UUID
    assert dashboard["uuid"] == new_dashboard_uuid
    assert dashboards == [new_dashboard_uuid]
    assert dashboard["position"]["CHART-1"]["meta"]["uuid"] == new_chart_uuid
    target = dashboard["metadata"]["native_filter_configuration"][0][
        "targets"][0]
    assert target["datasetUuid"] == TARGET_DATASET_UUID
    assert dashboard["slug"] == f"overview-{PROJECT.hex[:8]}"

    # no reference to an object of the source project is left
    everything = yaml.safe_dump(files)
    for old in (DATASET_UUID, CHART_UUID, DASHBOARD_UUID, SOURCE_SCHEMA):
        assert old not in everything


def test_projects_get_distinct_copies():
    other = UUID("99999999-8888-4777-8666-555555555555")
    _, _, first = _apply()
    _, _, again = _apply()
    _, _, second = _apply(target=_target(project=other, datasets={}))

    assert first == again  # re-importing updates the same dashboard
    assert first != second


def test_dataset_of_another_schema_is_used():
    target = _target(datasets={
        "topics": tpl.DatasetRef(TARGET_DATASET_UUID, "custom_schema"),
    })
    files, _, _ = _apply(target=target)
    topics = next(
        d for d in _by_prefix(files, "datasets/")
        if d["table_name"] == "topics"
    )
    assert topics["schema"] == "custom_schema"


def test_tar_gz_templates_are_applied():
    zip_files, _, _ = _apply(build_export_zip())
    tar_files, _, _ = _apply(build_export_tar_gz())
    assert zip_files == tar_files
