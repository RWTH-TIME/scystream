"""Round trip of a dashboard through a real Superset.

A dashboard is created in Superset on top of a "template" schema, exported,
adapted to a project schema by the export adapter and imported again by the
SupersetClient, exactly like scystream-core does after a pipeline finished.

Requires the stack from superset/docker-compose.test.yml, the tests are
skipped unless SUPERSET_INTEGRATION_URL is set:

    docker compose -f superset/docker-compose.test.yml up -d --build --wait
    SUPERSET_INTEGRATION_URL=http://localhost:8088 pytest tests/integration
"""

import json
import os
from uuid import uuid4

import psycopg2
import pytest
import requests
import yaml
from services.superset_service import export_adapter
from services.superset_service.dashboard_import_controller import (
    _extract_dashboard_uuids,
)
from services.superset_service.superset_client import SupersetClient
from tests.superset.export_fixture import read_zip
from utils.config.defaults import _normalize_uuid

SUPERSET_URL = os.environ.get("SUPERSET_INTEGRATION_URL")
# data-postgres as seen from the test runner and from Superset
DATA_PG_DSN = os.environ.get(
    "DATA_PG_INTEGRATION_DSN",
    "postgresql://postgres:postgres@localhost:5433/postgres",
)
DATA_PG_HOST_IN_SUPERSET = "data-postgres"
# second name of the same postgres, used by the "template" dashboard, so the
# test can verify that the adapter points the import to data-postgres
TEMPLATE_PG_HOST_IN_SUPERSET = "template-postgres"

pytestmark = pytest.mark.skipif(
    not SUPERSET_URL,
    reason="SUPERSET_INTEGRATION_URL is not set",
)


def _admin_token() -> str:
    resp = requests.post(
        f"{SUPERSET_URL}/api/v1/security/login",
        json={
            "username": os.environ.get("SUPERSET_ADMIN_USERNAME", "admin"),
            "password": os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin"),
            "provider": "db",
            "refresh": False,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _create_schema_with_table(
    schema: str,
    topics: tuple[str, ...] = ("template",),
) -> None:
    conn = psycopg2.connect(DATA_PG_DSN)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS "{schema}".topics '
            "(topic TEXT, weight DOUBLE PRECISION)",
        )
        for topic in topics:
            cur.execute(
                f'INSERT INTO "{schema}".topics VALUES (%s, %s)',
                (topic, 1.0 / len(topics)),
            )
    conn.close()


@pytest.fixture
def client():
    return SupersetClient(base_url=SUPERSET_URL, access_token=_admin_token())


@pytest.fixture
def data_postgres_env(monkeypatch):
    env = export_adapter.ENV
    monkeypatch.setattr(
        env, "DEFAULT_CB_CONFIG_PG_HOST", DATA_PG_HOST_IN_SUPERSET,
    )
    monkeypatch.setattr(env, "DEFAULT_CB_CONFIG_PG_PORT", 5432)
    monkeypatch.setattr(env, "DEFAULT_CB_CONFIG_PG_USER", "postgres")
    monkeypatch.setattr(env, "DEFAULT_CB_CONFIG_PG_PASS", "postgres")


def _post(client, path, payload) -> int:
    resp = client.session.post(f"{client.base_url}{path}", json=payload)
    assert resp.ok, resp.text
    return resp.json()["id"]


def _delete(client, path) -> None:
    resp = client.session.delete(f"{client.base_url}{path}")
    assert resp.ok, resp.text


def _create_template_dashboard(client, schema: str) -> bytes:
    """Creates database, dataset, chart & dashboard, exports the dashboard
    and deletes all of it again, returns the export zip."""
    suffix = uuid4().hex[:8]
    database_id = _post(client, "/api/v1/database/", {
        "database_name": f"template_{suffix}",
        "sqlalchemy_uri": (
            f"postgresql+psycopg2://postgres:postgres@"
            f"{TEMPLATE_PG_HOST_IN_SUPERSET}:5432/postgres"
        ),
    })
    dataset_id = _post(client, "/api/v1/dataset/", {
        "database": database_id,
        "schema": schema,
        "table_name": "topics",
    })
    dashboard_id = _post(client, "/api/v1/dashboard/", {
        "dashboard_title": f"Topics {suffix}",
        "published": True,
    })
    chart_id = _post(client, "/api/v1/chart/", {
        "slice_name": f"Topics {suffix}",
        "viz_type": "table",
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "dashboards": [dashboard_id],
        "params": json.dumps({
            "datasource": f"{dataset_id}__table",
            "viz_type": "table",
            "query_mode": "raw",
            "all_columns": ["topic", "weight"],
        }),
    })

    resp = client.session.get(
        f"{client.base_url}/api/v1/dashboard/export/",
        params={"q": f"!({dashboard_id})"},
    )
    assert resp.ok, resp.text
    export = resp.content

    _delete(client, f"/api/v1/chart/{chart_id}")
    _delete(client, f"/api/v1/dashboard/{dashboard_id}")
    _delete(client, f"/api/v1/dataset/{dataset_id}")
    _delete(client, f"/api/v1/database/{database_id}")
    return export


def test_dashboard_export_roundtrip(client, data_postgres_env):
    template_schema = f"template_{uuid4().hex[:8]}"
    project_uuid = uuid4()
    project_schema = _normalize_uuid(project_uuid)
    _create_schema_with_table(template_schema)
    _create_schema_with_table(project_schema, topics=("ai", "climate"))

    raw_export = _create_template_dashboard(client, template_schema)
    export_adapter.validate_dashboard_export_zip(raw_export)

    adapted, passwords = export_adapter.adapt_export_zip(
        raw_export, project_uuid,
    )
    assert not any(
        template_schema in content for content in read_zip(adapted).values()
    )

    client.import_dashboard_zip(adapted, passwords)

    dashboard_id = client.find_dashboard_id_by_uuid(
        _extract_dashboard_uuids(adapted),
    )
    assert dashboard_id

    owner_email = f"owner-{uuid4().hex[:8]}@example.com"
    owner_id = client.ensure_user(owner_email)
    assert client.ensure_user(owner_email) == owner_id

    client.grant_dashboard_access(dashboard_id, owner_id)

    dashboard = client.get_dashboard(dashboard_id)
    assert [o["id"] for o in dashboard["owners"]] == [owner_id]
    assert dashboard["url"]

    datasets = client.list_datasets_for_dashboard(dashboard_id)
    assert len(datasets) == 1
    dataset = datasets[0]
    assert dataset["schema"] == project_schema
    assert [o["id"] for o in dataset["owners"]] == [owner_id]

    connection = client.session.get(
        f"{client.base_url}/api/v1/database/"
        f"{dataset['database']['id']}/connection",
    ).json()["result"]
    assert connection["parameters"]["host"] == DATA_PG_HOST_IN_SUPERSET

    # The imported dataset queries the project's schema through the imported
    # database connection (host and password were rewritten by the adapter)
    resp = client.session.post(
        f"{client.base_url}/api/v1/chart/data",
        json={
            "datasource": {"id": dataset["id"], "type": "table"},
            "queries": [
                {"columns": ["topic"], "metrics": [], "row_limit": 10},
            ],
            "result_format": "json",
            "result_type": "full",
        },
    )
    assert resp.ok, resp.text
    rows = resp.json()["result"][0]["data"]
    assert {row["topic"] for row in rows} == {"ai", "climate"}


def test_reimport_overwrites_dashboard(client, data_postgres_env):
    template_schema = f"template_{uuid4().hex[:8]}"
    project_uuid = uuid4()
    _create_schema_with_table(template_schema)
    _create_schema_with_table(_normalize_uuid(project_uuid))

    adapted, passwords = export_adapter.adapt_export_zip(
        _create_template_dashboard(client, template_schema), project_uuid,
    )
    uuids = _extract_dashboard_uuids(adapted)

    client.import_dashboard_zip(adapted, passwords)
    first_id = client.find_dashboard_id_by_uuid(uuids)
    client.import_dashboard_zip(adapted, passwords)

    assert client.find_dashboard_id_by_uuid(uuids) == first_id


def test_metadata_yaml_is_superset_v1(client):
    """Guards the adapter's assumptions about the export format."""
    schema = f"template_{uuid4().hex[:8]}"
    _create_schema_with_table(schema)
    files = read_zip(_create_template_dashboard(client, schema))

    metadata = yaml.safe_load(files["metadata.yaml"])
    assert metadata["version"] == "1.0.0"
    assert metadata["type"] == "Dashboard"
    assert any(p.startswith("databases/") for p in files)
    assert any(p.startswith("datasets/") for p in files)
    assert any(p.startswith("charts/") for p in files)
    assert any(p.startswith("dashboards/") for p in files)
