"""End to end test of the Superset integration of projects.

Runs core's project code against real services: core-postgres (project
state), MinIO (visualization templates), data-postgres (data written by the
workflow steps) and Superset. Only the workflow runs themselves are
simulated by writing tables into the project schemas.

    docker compose -f superset/docker-compose.test.yml up -d --build --wait
    cd core && alembic upgrade head
    SCYSTREAM_E2E=1 pytest tests/integration/test_superset_e2e.py

with the environment of the "e2e" step of .github/workflows/superset.yaml.
"""

import json
import os
from uuid import UUID, uuid4

import boto3
import psycopg2
import pytest
import requests
from fastapi import HTTPException
from services.superset_service import project_sync
from services.superset_service import sync as sync_module
from services.superset_service.superset_client import SupersetClient
from services.superset_service.template import TemplateError, read_bundle
from services.workflow_service.controllers import project_controller
from services.workflow_service.models.block import Block, block_dependencies
from services.workflow_service.models.entrypoint import Entrypoint
from services.workflow_service.models.input_output import (
    DataType,
    InputOutput,
    InputOutputType,
)
from services.workflow_service.models.project import Project
from services.workflow_service.models.superset_import_status import (
    SupersetImportStatus,
)
from utils.config.defaults import data_pg_dsn_for_core, project_schema
from utils.config.environment import ENV
from utils.database.session_injector import get_database

from tests.superset.export_fixture import build_export_tar_gz

pytestmark = pytest.mark.skipif(
    not os.environ.get("SCYSTREAM_E2E"),
    reason="SCYSTREAM_E2E is not set",
)

SUPERSET_URL = ENV.SUPERSET_HOST.rstrip("/")
ADMIN = ("admin", "admin")


def _login(username: str, password: str) -> str:
    resp = requests.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={"username": username, "password": password,
              "provider": "db", "refresh": False},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def admin():
    return SupersetClient(base_url=SUPERSET_URL, access_token=_login(*ADMIN))


@pytest.fixture(scope="module", autouse=True)
def environment(admin):
    """Superset runs with its own user database in the test stack, core
    therefore uses an admin token instead of a Keycloak service token."""
    mp = pytest.MonkeyPatch()
    mp.setattr(project_sync, "SupersetSync",
               lambda client=None: sync_module.SupersetSync(admin))

    s3 = boto3.client(
        "s3",
        endpoint_url=ENV.EXTERNAL_URL_DATA_S3,
        aws_access_key_id=ENV.DEFAULT_CB_CONFIG_S3_ACCESS_KEY,
        aws_secret_access_key=ENV.DEFAULT_CB_CONFIG_S3_SECRET_KEY,
    )
    try:
        s3.create_bucket(Bucket=ENV.DEFAULT_CB_CONFIG_S3_BUCKET_NAME)
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass
    yield
    mp.undo()


def _db():
    return next(get_database())


def _write_run_output(project_uuid: UUID, topics: list[str]) -> None:
    """What a workflow run leaves in the data postgres: the table of a
    database output and a table a step created on its own."""
    schema = project_schema(project_uuid)
    conn = psycopg2.connect(data_pg_dsn_for_core())
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        cur.execute(f'DROP TABLE IF EXISTS "{schema}".topics_lda')
        cur.execute(
            f'CREATE TABLE "{schema}".topics_lda (topic TEXT, weight FLOAT)',
        )
        for topic in topics:
            cur.execute(
                f'INSERT INTO "{schema}".topics_lda VALUES (%s, %s)',
                (topic, 1.0),
            )
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS "{schema}".step_log (line TEXT)',
        )
    conn.close()


def _create_project(name: str, owner: str) -> UUID:
    """A project with two connected compute blocks, like one created in the
    workbench: a crawler writing a file and a topic model reading it and
    writing a database table."""
    db = _db()
    with db.begin():
        project_uuid = project_controller.create_project(
            db, name, uuid4(), owner_email=owner,
        )
        db.flush()
        schema = project_schema(project_uuid)

        def block(custom_name, ios):
            entry = Entrypoint(name="main", description="", envs={"N": "5"})
            db.add(entry)
            db.flush()
            for io in ios:
                io.entrypoint_uuid = entry.uuid
                db.add(io)
            b = Block(name=custom_name, custom_name=custom_name,
                      project_uuid=project_uuid, docker_image="img",
                      cbc_url="https://example.org/cb.git",
                      selected_entrypoint_uuid=entry.uuid, x_pos=0, y_pos=0)
            db.add(b)
            db.flush()
            return b

        file_out = InputOutput(
            type=InputOutputType.OUTPUT, name="papers",
            data_type=DataType.FILE,
            config={"PAPERS_FILE_NAME": "file_papers_1",
                    "PAPERS_BUCKET_NAME": "data"},
        )
        file_in = InputOutput(
            type=InputOutputType.INPUT, name="papers",
            data_type=DataType.FILE,
            config={"PAPERS_FILE_NAME": "file_papers_1",
                    "PAPERS_BUCKET_NAME": "data"},
        )
        db_out = InputOutput(
            type=InputOutputType.OUTPUT, name="topics",
            data_type=DataType.DBTABLE,
            config={"TOPICS_DB_SCHEMA": schema,
                    "TOPICS_DB_TABLE": "topics_lda"},
        )
        crawler = block("crawler", [file_out])
        model = block("topic_model", [file_in, db_out])
        db.execute(block_dependencies.insert().values(
            upstream_block_uuid=crawler.uuid,
            upstream_output_uuid=file_out.uuid,
            downstream_block_uuid=model.uuid,
            downstream_input_uuid=file_in.uuid,
        ))
    db.close()
    return project_uuid


def _project(project_uuid: UUID) -> Project:
    return project_sync.read(project_uuid)


def _user_session(admin: SupersetClient, email: str) -> requests.Session:
    """Logs in as the Superset user core created for the email (users of the
    test stack log in with a password instead of Keycloak)."""
    user_id = admin.find_user_id_by_email(email)
    password = uuid4().hex
    resp = admin.session.put(
        f"{admin.base_url}/api/v1/security/users/{user_id}",
        json={"password": password},
    )
    assert resp.ok, resp.text
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {_login(email, password)}"
    return session


def _query(session, dataset_id: int) -> set[str]:
    resp = session.post(
        f"{SUPERSET_URL}/api/v1/chart/data",
        json={
            "datasource": {"id": dataset_id, "type": "table"},
            "queries": [{"columns": ["topic"], "metrics": [],
                         "row_limit": 100}],
            "result_format": "json",
            "result_type": "full",
        },
    )
    assert resp.ok, resp.text
    return {row["topic"] for row in resp.json()["result"][0]["data"]}


def _chart_datasets(admin: SupersetClient, dashboard_id: int) -> dict:
    return {
        chart["slice_name"]: int(
            chart["form_data"]["datasource"].split("__")[0],
        )
        for chart in admin.list_charts_for_dashboard(dashboard_id)
    }


def _dataset_id(admin: SupersetClient, project_uuid: UUID,
                table: str) -> int:
    """The dataset of a project table, there must be exactly one (a template
    import must reuse the synced dataset, not create a second one)."""
    query = {
        "filters": [
            {"col": "schema", "opr": "eq",
             "value": project_schema(project_uuid)},
            {"col": "table_name", "opr": "eq", "value": table},
        ],
        "columns": ["id"],
    }
    resp = admin.session.get(
        f"{admin.base_url}/api/v1/dataset/",
        params={"q": json.dumps(query)},
    )
    resp.raise_for_status()
    datasets = resp.json()["result"]
    assert len(datasets) == 1, datasets
    return datasets[0]["id"]


def test_project_visualization_lifecycle(admin):
    suffix = uuid4().hex[:8]
    owner = f"owner-{suffix}@example.com"
    viewer = f"viewer-{suffix}@example.com"

    # 1. a project without visualization template, before its first run
    source = _create_project(f"source {suffix}", owner)
    assert _project(source).superset_import_status == (
        SupersetImportStatus.NONE.value
    )

    # 2. the first successful run creates datasets for everything the
    #    steps wrote and a standard dashboard
    _write_run_output(source, ["ai", "climate"])
    project_sync.sync_finished_runs({str(source): "run-1"})

    project = _project(source)
    assert project.superset_import_status == (
        SupersetImportStatus.IMPORTED.value
    ), project.superset_import_error
    assert project.superset_synced_run_id == "run-1"
    assert project.superset_dashboard_url.startswith(ENV.superset_public_url)
    dashboard_id = project.superset_dashboard_id
    charts = _chart_datasets(admin, dashboard_id)
    assert set(charts) == {"topics_lda", "step_log"}

    # the same run is not synced again
    project_sync.sync_finished_runs({str(source): "run-1"})
    assert _chart_datasets(admin, dashboard_id) == charts

    # 3. the dashboard link is shared with the requesting user, who sees
    #    this dashboard (and only dashboards shared with them) and its data
    url = project_sync.dashboard_url_for_user(source, viewer)
    assert url == project.superset_dashboard_url
    viewer_session = _user_session(admin, viewer)
    visible = viewer_session.get(f"{SUPERSET_URL}/api/v1/dashboard/").json()
    assert [d["id"] for d in visible["result"]] == [dashboard_id]
    assert _query(viewer_session, charts["topics_lda"]) == {"ai", "climate"}

    # 4. the visualization is exported as template ...
    template = project_sync.export_template(source)
    read_bundle(template)

    # 5. ... and cloning copies the project and its visualization
    clone = project_controller.clone_project(
        source, f"clone {suffix}", uuid4(), owner_email=owner,
    )
    clone_project = _project(clone)
    assert clone_project.has_superset_template
    assert clone_project.superset_import_status == (
        SupersetImportStatus.PENDING.value
    )

    db = _db()
    blocks = db.query(Block).filter_by(project_uuid=clone).all()
    assert sorted(b.custom_name for b in blocks) == ["crawler", "topic_model"]
    configs = {
        (io.type, io.name, io.data_type): io.config
        for b in blocks for io in b.selected_entrypoint.input_outputs
    }
    file_out = configs[(InputOutputType.OUTPUT, "papers", DataType.FILE)]
    file_in = configs[(InputOutputType.INPUT, "papers", DataType.FILE)]
    db_out = configs[(InputOutputType.OUTPUT, "topics", DataType.DBTABLE)]
    assert file_out["PAPERS_FILE_NAME"] != "file_papers_1"
    assert file_in["PAPERS_FILE_NAME"] == file_out["PAPERS_FILE_NAME"]
    assert db_out["TOPICS_DB_SCHEMA"] == project_schema(clone)
    edges = db.execute(block_dependencies.select().where(
        block_dependencies.c.upstream_block_uuid.in_([b.uuid for b in blocks]),
    )).fetchall()
    assert len(edges) == 1
    db.close()

    # 6. the clone's first run imports the template bound to its own data
    _write_run_output(clone, ["clone-topic"])
    project_sync.sync_finished_runs({str(clone): "run-1"})
    clone_project = _project(clone)
    assert clone_project.superset_import_status == (
        SupersetImportStatus.IMPORTED.value
    ), clone_project.superset_import_error
    clone_dashboard = clone_project.superset_dashboard_id
    assert clone_dashboard != dashboard_id
    clone_charts = _chart_datasets(admin, clone_dashboard)
    assert clone_charts == {
        "topics_lda": _dataset_id(admin, clone, "topics_lda"),
        "step_log": _dataset_id(admin, clone, "step_log"),
    }
    assert _query(admin.session, clone_charts["topics_lda"]) == {
        "clone-topic",
    }

    # the source project is untouched
    assert _chart_datasets(admin, dashboard_id) == charts
    assert _project(source).superset_dashboard_id == dashboard_id

    # 7. the owner of the clone gets access, the viewer of the source not
    project_sync.dashboard_url_for_user(clone, owner)
    visible = viewer_session.get(f"{SUPERSET_URL}/api/v1/dashboard/").json()
    assert clone_dashboard not in [d["id"] for d in visible["result"]]


def test_uploaded_template(admin):
    suffix = uuid4().hex[:8]
    owner = f"owner-{suffix}@example.com"
    project_uuid = _create_project(f"upload {suffix}", owner)

    # invalid uploads are rejected
    with pytest.raises(TemplateError):
        project_sync.upload_template(project_uuid, b"not a template")

    # a template uploaded before the first run is applied after the run
    files = {
        "metadata.yaml": "version: 1.0.0\ntype: Dashboard\n",
    }
    template = _template_for_table("topics_lda", files)
    project = project_sync.upload_template(project_uuid, template)
    assert project.superset_import_status == (
        SupersetImportStatus.PENDING.value
    )
    assert project.superset_dashboard_id is None

    _write_run_output(project_uuid, ["uploaded"])
    project_sync.sync_finished_runs({str(project_uuid): "run-7"})
    project = _project(project_uuid)
    assert project.superset_import_status == (
        SupersetImportStatus.IMPORTED.value
    ), project.superset_import_error
    dashboard = admin.get_dashboard(project.superset_dashboard_id)
    assert dashboard["dashboard_title"] == "Uploaded template"
    charts = _chart_datasets(admin, project.superset_dashboard_id)
    assert charts == {
        "Topic table": _dataset_id(admin, project_uuid, "topics_lda"),
    }
    assert _query(admin.session, charts["Topic table"]) == {"uploaded"}

    # uploading again to a project with data syncs right away
    project = project_sync.upload_template(
        project_uuid, _template_for_table("topics_lda", files, "Second"),
    )
    assert project.superset_import_status == (
        SupersetImportStatus.IMPORTED.value
    )
    second = admin.get_dashboard(project.superset_dashboard_id)
    assert second["dashboard_title"] == "Second"


def _template_for_table(table: str, files: dict,
                        title: str = "Uploaded template") -> bytes:
    """A hand written template (.tar.gz) with a table chart."""
    import yaml

    dataset_uuid = str(uuid4())
    chart_uuid = str(uuid4())
    files = {
        **files,
        "databases/somewhere.yaml": yaml.safe_dump({
            "database_name": "somewhere",
            "sqlalchemy_uri": "postgresql+psycopg2://x:XXXXXXXXXX@h/db",
            "uuid": str(uuid4()),
            "version": "1.0.0",
        }),
        f"datasets/somewhere/{table}.yaml": yaml.safe_dump({
            "table_name": table,
            "schema": "whatever",
            "uuid": dataset_uuid,
            "database_uuid": "00000000-0000-4000-8000-000000000000",
            "columns": [{"column_name": "topic", "type": "TEXT"},
                        {"column_name": "weight", "type": "FLOAT"}],
            "metrics": [{"metric_name": "count",
                         "expression": "COUNT(*)"}],
            "version": "1.0.0",
        }),
        "charts/topic_table.yaml": yaml.safe_dump({
            "slice_name": "Topic table",
            "viz_type": "table",
            "params": {"viz_type": "table", "query_mode": "raw",
                       "all_columns": ["topic", "weight"]},
            "uuid": chart_uuid,
            "dataset_uuid": dataset_uuid,
            "version": "1.0.0",
        }),
        "dashboards/uploaded.yaml": yaml.safe_dump({
            "dashboard_title": title,
            "uuid": str(uuid4()),
            "position": {
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID",
                            "children": ["GRID_ID"]},
                "GRID_ID": {"type": "GRID", "id": "GRID_ID",
                            "children": ["ROW-1"], "parents": ["ROOT_ID"]},
                "ROW-1": {"type": "ROW", "id": "ROW-1",
                          "children": ["CHART-1"],
                          "parents": ["ROOT_ID", "GRID_ID"],
                          "meta": {"background": "BACKGROUND_TRANSPARENT"}},
                "CHART-1": {"type": "CHART", "id": "CHART-1",
                            "children": [],
                            "parents": ["ROOT_ID", "GRID_ID", "ROW-1"],
                            "meta": {"chartId": 1, "uuid": chart_uuid,
                                     "width": 6, "height": 50}},
            },
            "metadata": {},
            "version": "1.0.0",
        }),
    }
    return build_export_tar_gz(files)


def test_dashboard_link_needs_a_dashboard():
    project_uuid = _create_project(f"empty {uuid4().hex[:8]}", "x@y.de")
    with pytest.raises(HTTPException) as exc:
        project_sync.dashboard_url_for_user(project_uuid, "x@y.de")
    assert exc.value.status_code == 409


def test_http_api(admin):
    """The project endpoints the frontend uses, with a logged in user."""
    from fastapi.testclient import TestClient
    from main import app
    from utils.security.token import User, get_user

    suffix = uuid4().hex[:8]
    user = User(uuid=uuid4(), username=f"u{suffix}",
                email=f"api-{suffix}@example.com", email_verified=True)
    app.dependency_overrides[get_user] = lambda: user
    try:
        client = TestClient(app)
        project_uuid = _create_project(f"api {suffix}", user.email)

        # no dashboard before the first run
        resp = client.get(f"/project/{project_uuid}/superset/dashboard")
        assert resp.status_code == 409
        resp = client.get(f"/project/{project_uuid}/superset/template")
        assert resp.status_code == 404

        # wrong file types are rejected
        resp = client.put(
            f"/project/{project_uuid}/dashboard_export",
            files={"dashboard_export": ("x.txt", b"x", "text/plain")},
        )
        assert resp.status_code == 422
        resp = client.put(
            f"/project/{project_uuid}/dashboard_export",
            files={"dashboard_export": ("x.zip", b"not a zip",
                                        "application/zip")},
        )
        assert resp.status_code == 422

        # after a run: sync, open, download
        _write_run_output(project_uuid, ["api"])
        resp = client.post(f"/project/{project_uuid}/superset/sync")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["superset_import_status"] == "imported"
        assert body["has_superset_template"] is False

        resp = client.get(f"/project/{project_uuid}/superset/dashboard")
        assert resp.status_code == 200
        assert resp.json()["url"] == body["superset_dashboard_url"]
        dashboard_id = _project(project_uuid).superset_dashboard_id
        user_id = admin.find_user_id_by_email(user.email)
        owners = [o["id"] for o in admin.get_dashboard(dashboard_id)["owners"]]
        assert user_id in owners

        resp = client.get(f"/project/{project_uuid}/superset/template")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        read_bundle(resp.content)

        # the downloaded template as .tar.gz upload to the same project
        files = dict(
            (p, c.decode()) for p, c in read_bundle(resp.content).items()
        )
        resp = client.put(
            f"/project/{project_uuid}/dashboard_export",
            files={"dashboard_export": ("t.tar.gz",
                                        build_export_tar_gz(files),
                                        "application/gzip")},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["has_superset_template"] is True
        assert resp.json()["superset_import_status"] == "imported"

        # clone
        resp = client.post(f"/project/{project_uuid}/clone",
                           data={"name": f"api clone {suffix}"})
        assert resp.status_code == 200, resp.text
        clone = UUID(resp.json()["project_uuid"])
        resp = client.get(f"/project/{clone}")
        assert resp.json()["has_superset_template"] is True
        assert resp.json()["superset_import_status"] == "pending"
    finally:
        app.dependency_overrides.clear()


def test_project_as_shared_template(admin):
    from services.workflow_service.controllers import (
        shared_template_controller as shared,
        template_controller,
    )

    suffix = uuid4().hex[:8]
    project_uuid = _create_project(f"tpl {suffix}", "t@example.com")
    db = _db()
    entry = (
        db.query(Block).filter_by(project_uuid=project_uuid,
                                  custom_name="crawler").one()
        .selected_entrypoint
    )
    entry.envs = {"N": "5", "API_TOKEN": "secret", "EMPTY": ""}
    db.commit()
    db.close()
    _write_run_output(project_uuid, ["tpl"])
    project_sync.sync_project(project_uuid)

    creator = uuid4()
    record = shared.create_shared_template(
        project_uuid, f"Topic pipeline {suffix}", "LDA on papers",
        ["nlp"], creator, "t@example.com",
    )
    blocks = {b["name"]: b for b in record.definition["blocks"]}
    assert blocks["crawler"]["settings"] == {"N": "5"}  # no secrets
    assert blocks["crawler"]["outputs"] == [{"identifier": "papers"}]
    model = blocks["topic_model"]
    assert model["inputs"] == [{
        "identifier": "papers",
        "depends_on": {"block": "crawler", "output": "papers"},
    }]
    # generated locations are not part of the template
    assert model["outputs"] == [{"identifier": "topics"}]
    assert record.superset_template_s3_key  # visualization snapshot
    read_bundle(shared.superset_template(shared.shared_identifier(
        record.uuid)))

    # visible to everybody next to the repository templates
    identifier = shared.shared_identifier(record.uuid)
    listed = [t.file_identifier
              for t in template_controller.get_workflow_templates()]
    assert identifier in listed
    template = template_controller.get_workflow_template_by_identifier(
        identifier,
    )
    assert template.pipeline.tags == ["nlp"]
    assert "depends_on" in shared.template_yaml(identifier)

    # only the creator may delete it
    with pytest.raises(HTTPException) as exc:
        shared.delete_shared_template(identifier, uuid4())
    assert exc.value.status_code == 403
    shared.delete_shared_template(identifier, creator)
    with pytest.raises(HTTPException):
        shared.get_shared_template(identifier)
