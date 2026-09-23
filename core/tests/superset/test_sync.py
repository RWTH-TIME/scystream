from uuid import UUID

import pytest
from services.superset_service import sync as sync_module
from services.superset_service.sync import SupersetSync, Table, _layout
from tests.superset.export_fixture import build_export_zip

PROJECT = UUID("0b6f3c0e-8a51-4d6c-9a57-6f1f8f0e2c11")
SCHEMA = "s0b6f3c0e8a514d6c9a576f1f8f0e2c11"


class FakeSuperset:
    """In memory stand-in for SupersetClient."""

    def __init__(self):
        self.datasets = {}
        self.dashboards = {}
        self.charts = {}
        self.imports = []
        self.owners = {}
        self.deleted = []

    def ensure_database(self, name, uri):
        self.database = (name, uri)
        return {"id": 1, "uuid": "11111111-1111-4111-8111-111111111111"}

    def ensure_dataset(self, database_id, schema, table):
        key = (schema, table)
        if key not in self.datasets:
            n = len(self.datasets) + 1
            self.datasets[key] = {
                "id": n, "uuid": f"00000000-0000-4000-8000-{n:012d}",
                "schema": schema, "table_name": table,
            }
        return self.datasets[key]

    def get_dataset(self, dataset_id):
        return {"columns": [{"column_name": "a"}, {"column_name": "b"}]}

    def find_dashboard_by_slug(self, slug):
        return next(
            ({"id": i} for i, d in self.dashboards.items()
             if d["slug"] == slug), None,
        )

    def create_dashboard(self, title, slug):
        dashboard_id = len(self.dashboards) + 1
        self.dashboards[dashboard_id] = {"title": title, "slug": slug}
        return dashboard_id

    def list_charts_for_dashboard(self, dashboard_id):
        return [
            {"id": i, "slice_name": c["name"]}
            for i, c in self.charts.items() if c["dashboard"] == dashboard_id
        ]

    def create_chart(self, name, dataset_id, params, dashboard_ids):
        chart_id = len(self.charts) + 1
        self.charts[chart_id] = {"name": name, "dataset": dataset_id,
                                 "params": params,
                                 "dashboard": dashboard_ids[0]}
        return chart_id

    def update_dashboard(self, dashboard_id, **fields):
        self.dashboards[dashboard_id].update(fields)

    def import_dashboard_zip(self, bundle, passwords):
        self.imports.append((bundle, passwords))

    def find_dashboard_id_by_uuid(self, uuids):
        return 99

    def delete_dashboard(self, dashboard_id):
        self.deleted.append(dashboard_id)
        self.dashboards.pop(dashboard_id, None)

    def ensure_user(self, email):
        return {"a@b.de": 5}.get(email, 6)

    def grant_dashboard_access(self, dashboard_id, user_id):
        self.owners.setdefault(dashboard_id, set()).add(user_id)

    def get_dashboard(self, dashboard_id):
        return {"url": f"/superset/dashboard/{dashboard_id}/"}


@pytest.fixture
def superset(monkeypatch):
    tables = [Table(SCHEMA, "topics"), Table(SCHEMA, "authors"),
              Table("custom", "topics")]
    monkeypatch.setattr(sync_module, "discover_tables", lambda s: [
        t for t in tables if t.schema in s
    ])
    monkeypatch.setattr(sync_module.ENV, "SUPERSET_PUBLIC_URL",
                        "https://superset.example.org/")
    return FakeSuperset()


def test_standard_dashboard_has_a_chart_per_table(superset):
    result = SupersetSync(superset).sync(
        PROJECT, "My project", [SCHEMA, "custom"], owner_emails=["a@b.de"],
    )

    assert result.dashboard_url == (
        f"https://superset.example.org/superset/dashboard/"
        f"{result.dashboard_id}/"
    )
    assert superset.dashboards[result.dashboard_id]["slug"] == (
        f"scystream-{PROJECT.hex}"
    )
    names = sorted(c["name"] for c in superset.charts.values())
    assert names == ["authors", "custom.topics", "topics"]
    assert all(c["params"]["all_columns"] == ["a", "b"]
               for c in superset.charts.values())
    assert "position_json" in superset.dashboards[result.dashboard_id]
    assert superset.owners == {result.dashboard_id: {5}}


def test_resync_only_adds_new_charts(superset):
    sync = SupersetSync(superset)
    first = sync.sync(PROJECT, "p", [SCHEMA])
    superset.dashboards[first.dashboard_id].pop("position_json")

    second = sync.sync(PROJECT, "p", [SCHEMA])
    assert second.dashboard_id == first.dashboard_id
    assert len(superset.charts) == 2
    # layout is untouched if nothing changed (keeps edits made in Superset)
    assert "position_json" not in superset.dashboards[first.dashboard_id]

    sync.sync(PROJECT, "p", [SCHEMA, "custom"])
    assert len(superset.charts) == 3
    assert "position_json" in superset.dashboards[first.dashboard_id]


def test_template_replaces_standard_dashboard(superset):
    sync = SupersetSync(superset)
    standard = sync.sync(PROJECT, "p", [SCHEMA])

    result = sync.sync(PROJECT, "p", [SCHEMA], template=build_export_zip())

    assert result.dashboard_id == 99
    assert standard.dashboard_id in superset.deleted
    (bundle, passwords), = superset.imports
    assert passwords == {"databases/scystream-data.yaml": "postgres"}


def test_layout_places_charts_in_rows():
    charts = [{"id": i, "slice_name": f"c{i}"} for i in range(1, 4)]
    layout = _layout(charts, "t")
    assert layout["GRID_ID"]["children"] == ["ROW-0", "ROW-1"]
    assert layout["ROW-0"]["children"] == ["CHART-1", "CHART-2"]
    assert layout["CHART-3"]["meta"]["chartId"] == 3
