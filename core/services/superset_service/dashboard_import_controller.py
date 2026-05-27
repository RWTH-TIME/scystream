import io
import json
import logging
import zipfile
from uuid import UUID

import yaml
from sqlalchemy.orm import Session

from services.superset_service.export_adapter import (
    ExportAdapterError,
    adapt_export_zip,
)
from services.superset_service.superset_client import (
    SupersetClient,
    SupersetClientError,
)
from services.workflow_service.controllers import workflow_controller
from services.workflow_service.models.project import Project
from services.workflow_service.models.superset_import_status import (
    SupersetImportStatus,
)
from services.workflow_service.schemas.workflow import WorkflowStatus
from utils.config.environment import ENV
from utils.data import file_handling as fh
from utils.database.session_injector import get_database

logger = logging.getLogger(__name__)


def _extract_dashboard_uuids(zip_bytes: bytes) -> list[str]:
    uuids: list[str] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as bundle:
        for name in bundle.namelist():
            stripped = name.split("/", 1)[-1]
            if not stripped.startswith("dashboards/") or not stripped.endswith(
                (".yaml", ".yml")
            ):
                continue
            config = yaml.safe_load(bundle.read(name).decode())
            if isinstance(config, dict) and config.get("uuid"):
                uuids.append(str(config["uuid"]))
    return uuids


def _resolve_dashboard_id(client: SupersetClient, dashboard_uuids: list[str]) -> int | None:
    for dashboard_uuid in dashboard_uuids:
        query = {
            "filters": [{"col": "uuid", "opr": "eq", "value": dashboard_uuid}],
            "page_size": 1,
        }
        resp = client.session.get(
            f"{client.base_url}/api/v1/dashboard/",
            params={"q": json.dumps(query)},
        )
        if resp.ok:
            results = resp.json().get("result", [])
            if results:
                return results[0]["id"]
    return None


def _mark_import_failed(db: Session, project: Project, message: str) -> None:
    project.superset_import_status = SupersetImportStatus.FAILED.value
    project.superset_import_error = message[:2048]
    db.commit()


def _is_pipeline_finished(project_id: UUID) -> bool:
    dag_id = f"dag_{str(project_id).replace('-', '_')}"
    dag_runs = workflow_controller.last_dag_run_overview([dag_id])
    dag_run = dag_runs.get(dag_id)
    if not dag_run or not dag_run.state:
        return False
    status = WorkflowStatus.from_airflow_state(dag_run.state)
    return status == WorkflowStatus.FINISHED


def try_import_dashboard_for_project(project_id: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_id).one_or_none()
    if not project:
        return

    if project.superset_import_status != SupersetImportStatus.PENDING.value:
        return

    if not project.superset_export_s3_key:
        return

    if not _is_pipeline_finished(project_id):
        return

    updated = (
        db.query(Project)
        .filter_by(uuid=project_id)
        .filter(
            Project.superset_import_status == SupersetImportStatus.PENDING.value
        )
        .update(
            {Project.superset_import_status: SupersetImportStatus.IMPORTING.value}
        )
    )
    db.commit()

    if not updated:
        return

    project = db.query(Project).filter_by(uuid=project_id).one()

    try:
        raw_zip = fh.get_project_bytes(project.superset_export_s3_key)
        adapted_zip, passwords = adapt_export_zip(raw_zip, project_id)
        dashboard_uuids = _extract_dashboard_uuids(adapted_zip)

        client = SupersetClient()
        client.import_dashboard_zip(adapted_zip, passwords)

        if not project.owner_email:
            raise ExportAdapterError("Project owner email is missing")

        owner_id = client.find_user_id_by_email(project.owner_email)
        if not owner_id:
            raise SupersetClientError(
                f"Superset user not found for {project.owner_email}"
            )

        dashboard_id = _resolve_dashboard_id(client, dashboard_uuids)
        if not dashboard_id:
            raise SupersetClientError(
                "Imported dashboard could not be resolved in Superset"
            )

        client.grant_dashboard_access(dashboard_id, owner_id)
        dashboard = client.get_dashboard(dashboard_id)

        project.superset_dashboard_id = dashboard_id
        project.superset_dashboard_url = (
            f"{ENV.superset_public_url.rstrip('/')}{dashboard.get('url', '')}"
        )
        project.superset_import_status = SupersetImportStatus.IMPORTED.value
        project.superset_import_error = None
        db.commit()
        logger.info(
            "Imported Superset dashboard %s for project %s",
            dashboard_id,
            project_id,
        )
    except (ExportAdapterError, SupersetClientError, RuntimeError) as exc:
        logger.exception(
            "Superset dashboard import failed for project %s: %s",
            project_id,
            exc,
        )
        project = db.query(Project).filter_by(uuid=project_id).one()
        _mark_import_failed(db, project, str(exc))
    except Exception as exc:
        logger.exception(
            "Unexpected Superset dashboard import failure for project %s",
            project_id,
        )
        project = db.query(Project).filter_by(uuid=project_id).one()
        _mark_import_failed(db, project, str(exc))


def process_pending_dashboard_imports(project_ids: list[UUID]) -> None:
    for project_id in project_ids:
        try:
            try_import_dashboard_for_project(project_id)
        except Exception:
            logger.exception(
                "Error while processing dashboard import for project %s",
                project_id,
            )
