"""Makes the data of a project available in Superset.

After a successful workflow run, every table the compute blocks wrote into
the data postgres (the project schema and any other schema configured on a
database output of the project) becomes a Superset dataset. The project gets
a dashboard for them:

* if a visualization template (Superset dashboard export) was uploaded or
  inherited from a cloned project, it is imported with its references
  pointing to the project's datasets (see template.py)
* otherwise a standard dashboard with a table chart per dataset is created

Superset may run anywhere, it only needs to reach the data postgres via
SUPERSET_DATA_SQLALCHEMY_URI.
"""

import json
import logging
from dataclasses import dataclass, field
from uuid import UUID

import psycopg2
from sqlalchemy.engine import make_url

from services.superset_service import template as tpl
from services.superset_service.superset_client import SupersetClient
from utils.config.defaults import data_pg_dsn_for_core, project_schema
from utils.config.environment import ENV

logger = logging.getLogger(__name__)

STANDARD_DASHBOARD_SLUG_PREFIX = "scystream-"
STANDARD_CHART_ROW_LIMIT = 1000
CHARTS_PER_ROW = 2


@dataclass(frozen=True)
class Table:
    schema: str
    name: str


@dataclass
class SyncResult:
    dashboard_id: int
    dashboard_url: str
    datasets: dict[Table, dict] = field(default_factory=dict)


# data postgres

def data_sqlalchemy_uri() -> str:
    """URI Superset uses to connect to the data postgres."""
    if ENV.SUPERSET_DATA_SQLALCHEMY_URI:
        return ENV.SUPERSET_DATA_SQLALCHEMY_URI
    return str(make_url(
        "postgresql+psycopg2://"
        f"{ENV.DEFAULT_CB_CONFIG_PG_HOST}:{ENV.DEFAULT_CB_CONFIG_PG_PORT}"
        f"/{ENV.DEFAULT_CB_CONFIG_PG_DB}",
    ).set(
        username=ENV.DEFAULT_CB_CONFIG_PG_USER,
        password=ENV.DEFAULT_CB_CONFIG_PG_PASS,
    ).render_as_string(hide_password=False))


def discover_tables(schemas: list[str]) -> list[Table]:
    """Returns all tables and views in the given schemas of the data
    postgres, i.e. everything the workflow steps wrote there."""
    if not schemas:
        return []
    conn = psycopg2.connect(data_pg_dsn_for_core())
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema = ANY(%s)
                  AND table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY table_schema, table_name
                """,
                (list(schemas),),
            )
            return [Table(schema, name) for schema, name in cur.fetchall()]
    finally:
        conn.close()


# superset

def standard_dashboard_slug(project_uuid: UUID) -> str:
    return f"{STANDARD_DASHBOARD_SLUG_PREFIX}{project_uuid.hex}"


def _chart_name(table: Table, default_schema: str) -> str:
    if table.schema == default_schema:
        return table.name
    return f"{table.schema}.{table.name}"


def _layout(charts: list[dict], title: str) -> dict:
    """Dashboard layout (position_json) with the charts in rows."""
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID",
                    "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [],
                    "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID",
                      "meta": {"text": title}},
    }
    width = 12 // CHARTS_PER_ROW
    for row_index in range(0, len(charts), CHARTS_PER_ROW):
        row_id = f"ROW-{row_index // CHARTS_PER_ROW}"
        position["GRID_ID"]["children"].append(row_id)
        row = {"type": "ROW", "id": row_id, "children": [],
               "parents": ["ROOT_ID", "GRID_ID"],
               "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        for chart in charts[row_index:row_index + CHARTS_PER_ROW]:
            chart_node_id = f"CHART-{chart['id']}"
            row["children"].append(chart_node_id)
            position[chart_node_id] = {
                "type": "CHART", "id": chart_node_id, "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {"chartId": chart["id"], "width": width,
                         "height": 50, "sliceName": chart["slice_name"]},
            }
        position[row_id] = row
    return position


class SupersetSync:
    def __init__(self, client: SupersetClient | None = None):
        self.client = client or SupersetClient()

    def ensure_database(self) -> dict:
        return self.client.ensure_database(
            ENV.SUPERSET_DATA_DATABASE_NAME,
            data_sqlalchemy_uri(),
        )

    def ensure_datasets(
        self,
        database_id: int,
        tables: list[Table],
    ) -> dict[Table, dict]:
        return {
            table: self.client.ensure_dataset(
                database_id, table.schema, table.name,
            )
            for table in tables
        }

    def standard_dashboard(
        self,
        project_uuid: UUID,
        title: str,
        datasets: dict[Table, dict],
    ) -> int:
        """Creates (or extends) the standard dashboard: one table chart with
        the raw records per dataset. Charts of datasets that already have one
        are kept, so changes made in Superset survive later runs."""
        default_schema = project_schema(project_uuid)
        slug = standard_dashboard_slug(project_uuid)
        existing = self.client.find_dashboard_by_slug(slug)
        dashboard_id = (
            existing["id"] if existing
            else self.client.create_dashboard(title, slug)
        )

        charts = self.client.list_charts_for_dashboard(dashboard_id)
        chart_names = {chart["slice_name"] for chart in charts}
        added = False
        for table, dataset in datasets.items():
            name = _chart_name(table, default_schema)
            if name in chart_names:
                continue
            columns = [
                column["column_name"]
                for column in self.client.get_dataset(dataset["id"])
                .get("columns", [])
            ]
            chart_id = self.client.create_chart(
                name,
                dataset["id"],
                {
                    "query_mode": "raw",
                    "all_columns": columns,
                    "row_limit": STANDARD_CHART_ROW_LIMIT,
                },
                [dashboard_id],
            )
            charts.append({"id": chart_id, "slice_name": name})
            added = True

        if added or not existing:
            self.client.update_dashboard(
                dashboard_id,
                position_json=json.dumps(_layout(charts, title)),
            )
        return dashboard_id

    def import_template(
        self,
        project_uuid: UUID,
        template: bytes,
        database: dict,
        datasets: dict[Table, dict],
    ) -> int:
        default_schema = project_schema(project_uuid)
        uri = make_url(data_sqlalchemy_uri())
        dataset_refs: dict[str, tpl.DatasetRef] = {}
        # prefer tables of the project schema if names are ambiguous
        for table, dataset in sorted(
            datasets.items(),
            key=lambda item: item[0].schema != default_schema,
        ):
            dataset_refs.setdefault(
                table.name, tpl.DatasetRef(dataset["uuid"], table.schema),
            )

        target = tpl.TemplateTarget(
            project_uuid=project_uuid,
            schema=default_schema,
            database_uuid=database["uuid"],
            database_name=ENV.SUPERSET_DATA_DATABASE_NAME,
            masked_sqlalchemy_uri=uri.render_as_string(hide_password=True)
            .replace("***", "XXXXXXXXXX"),
            password=uri.password or "",
            datasets=dataset_refs,
        )
        bundle, passwords, dashboard_uuids = tpl.apply_template(
            template, target,
        )
        self.client.import_dashboard_zip(bundle, passwords)

        dashboard_id = self.client.find_dashboard_id_by_uuid(dashboard_uuids)
        if not dashboard_id:
            raise tpl.TemplateError(
                "Imported dashboard could not be found in Superset",
            )
        # the template may describe fewer columns than the real tables have
        for dataset in datasets.values():
            self.client.ensure_dataset(
                database["id"], dataset["schema"], dataset["table_name"],
            )
        return dashboard_id

    def sync(
        self,
        project_uuid: UUID,
        title: str,
        schemas: list[str],
        template: bytes | None = None,
        owner_emails: list[str] | None = None,
    ) -> SyncResult:
        database = self.ensure_database()
        tables = discover_tables(schemas)
        datasets = self.ensure_datasets(database["id"], tables)

        if template:
            dashboard_id = self.import_template(
                project_uuid, template, database, datasets,
            )
            # the standard dashboard is replaced by the template
            standard = self.client.find_dashboard_by_slug(
                standard_dashboard_slug(project_uuid),
            )
            if standard and standard["id"] != dashboard_id:
                self.client.delete_dashboard(standard["id"])
        else:
            dashboard_id = self.standard_dashboard(
                project_uuid, title, datasets,
            )

        for email in owner_emails or []:
            self.share(dashboard_id, email)

        dashboard = self.client.get_dashboard(dashboard_id)
        url = (
            f"{ENV.superset_public_url.rstrip('/')}{dashboard.get('url', '')}"
        )
        return SyncResult(dashboard_id, url, datasets)

    def share(self, dashboard_id: int, email: str) -> None:
        """Gives the user (created if needed) access to the dashboard and
        the data of its datasets."""
        user_id = self.client.ensure_user(email)
        self.client.grant_dashboard_access(dashboard_id, user_id)

    def export(self, dashboard_id: int) -> bytes:
        return self.client.export_dashboard(dashboard_id)
