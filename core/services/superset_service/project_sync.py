"""Superset integration of projects: syncing the data of finished runs,
visualization templates and access to the project dashboard."""

import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.superset_service import template as tpl
from services.superset_service.sync import SupersetSync
from services.workflow_service.models.block import Block
from services.workflow_service.models.input_output import (
    DataType,
    InputOutput,
)
from services.workflow_service.models.project import Project
from services.workflow_service.models.superset_import_status import (
    SupersetImportStatus,
)
from utils.config.defaults import project_schema
from utils.data import file_handling as fh
from utils.database.session_injector import get_database

logger = logging.getLogger(__name__)


def _db() -> Session:
    return next(get_database())


def _get_project(db: Session, project_uuid: UUID) -> Project:
    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def project_schemas(db: Session, project: Project) -> list[str]:
    """The project schema and all schemas the project's database outputs
    are configured to write to."""
    schemas = {project_schema(project.uuid)}
    ios = (
        db.query(InputOutput)
        .join(Block, Block.selected_entrypoint_uuid ==
              InputOutput.entrypoint_uuid)
        .filter(Block.project_uuid == project.uuid)
        .filter(InputOutput.data_type == DataType.DBTABLE)
        .all()
    )
    for io in ios:
        for key, value in (io.config or {}).items():
            if key.endswith("DB_SCHEMA") and isinstance(value, str) and value:
                schemas.add(value)
    return sorted(schemas)


def _template_bytes(project: Project) -> bytes | None:
    if not project.superset_export_s3_key:
        return None
    return fh.get_project_bytes(project.superset_export_s3_key)


def store_template(project: Project, raw: bytes) -> None:
    """Validates a template (zip or tar.gz) and stores it as the project's
    visualization template."""
    normalized = tpl.normalize_template(raw)
    key = fh.project_superset_export_key(project.uuid)
    fh.put_project_bytes(key, normalized)
    project.superset_export_s3_key = key


def sync_project(
    project_uuid: UUID,
    run_id: str | None = None,
    sync: SupersetSync | None = None,
) -> Project:
    """Syncs the project's data to Superset and creates or updates its
    dashboard. Does nothing if a sync of the project is already running."""
    db = _db()
    try:
        claimed = (
            db.query(Project)
            .filter_by(uuid=project_uuid)
            .filter(Project.superset_import_status
                    != SupersetImportStatus.IMPORTING.value)
            .update({Project.superset_import_status:
                     SupersetImportStatus.IMPORTING.value})
        )
        db.commit()
        project = _get_project(db, project_uuid)
        if not claimed:
            return project

        try:
            result = (sync or SupersetSync()).sync(
                project.uuid,
                project.name,
                project_schemas(db, project),
                template=_template_bytes(project),
                owner_emails=[project.owner_email]
                if project.owner_email else [],
            )
        except Exception as exc:
            logger.exception("Superset sync of project %s failed",
                             project_uuid)
            project.superset_import_status = (
                SupersetImportStatus.FAILED.value
            )
            project.superset_import_error = str(exc)[:2048]
            if run_id:
                # don't retry the same run on every status poll
                project.superset_synced_run_id = run_id
            db.commit()
            db.refresh(project)
            return project

        project.superset_dashboard_id = result.dashboard_id
        project.superset_dashboard_url = result.dashboard_url
        project.superset_import_status = SupersetImportStatus.IMPORTED.value
        project.superset_import_error = None
        if run_id:
            project.superset_synced_run_id = run_id
        db.commit()
        db.refresh(project)
        logger.info("Synced project %s to Superset dashboard %s",
                    project_uuid, result.dashboard_id)
        return project
    finally:
        db.close()


def sync_finished_runs(finished_runs: dict[str, str]) -> None:
    """Syncs projects whose latest successful run was not synced yet.

    :param finished_runs: project id -> id of its latest, successful run
    """
    if not finished_runs:
        return
    db = _db()
    try:
        projects = (
            db.query(Project.uuid, Project.superset_synced_run_id)
            .filter(Project.uuid.in_(
                [UUID(project_id) for project_id in finished_runs],
            ))
            .all()
        )
    finally:
        db.close()

    for project_uuid, synced_run_id in projects:
        run_id = finished_runs[str(project_uuid)]
        if synced_run_id == run_id:
            continue
        try:
            sync_project(project_uuid, run_id)
        except Exception:
            logger.exception("Error syncing project %s to Superset",
                             project_uuid)


def upload_template(project_uuid: UUID, raw: bytes) -> Project:
    """Stores the visualization template. Projects that already have data
    are synced right away, all others after their next successful run."""
    db = _db()
    try:
        project = _get_project(db, project_uuid)
        store_template(project, raw)
        has_data = bool(project.superset_synced_run_id
                        or project.superset_dashboard_id)
        project.superset_import_status = SupersetImportStatus.PENDING.value
        project.superset_import_error = None
        db.commit()
    finally:
        db.close()

    if has_data:
        return sync_project(project_uuid)
    return read(project_uuid)


def read(project_uuid: UUID) -> Project:
    db = _db()
    try:
        return _get_project(db, project_uuid)
    finally:
        db.close()


def dashboard_url_for_user(
    project_uuid: UUID,
    email: str | None,
    sync: SupersetSync | None = None,
) -> str:
    """Returns the dashboard url and gives the user access to the dashboard
    and its data."""
    project = read(project_uuid)
    if not project.superset_dashboard_id:
        raise HTTPException(
            status_code=409,
            detail="The project has no Superset dashboard yet, it is "
                   "created after the first successful run",
        )
    if not email:
        raise HTTPException(
            status_code=422,
            detail="Your account has no email address, which Superset "
                   "needs to identify you",
        )
    (sync or SupersetSync()).share(project.superset_dashboard_id, email)
    return project.superset_dashboard_url


def export_template(
    project_uuid: UUID,
    sync: SupersetSync | None = None,
) -> bytes:
    """The project's visualization as template: the current state of its
    dashboard in Superset, or the uploaded template if it has not been
    imported yet."""
    project = read(project_uuid)
    if project.superset_dashboard_id:
        return (sync or SupersetSync()).export(project.superset_dashboard_id)
    template = _template_bytes(project)
    if template:
        return template
    raise HTTPException(
        status_code=404,
        detail="The project has no Superset visualization yet",
    )


def copy_visualization(
    source_uuid: UUID,
    target: Project,
    sync: SupersetSync | None = None,
) -> None:
    """Uses the visualization of the source project as template of the
    target project (e.g. when cloning). Failures are logged, cloning a
    project must not depend on Superset being reachable."""
    try:
        template = export_template(source_uuid, sync)
    except HTTPException:
        return
    except Exception:
        logger.exception("Could not export the Superset visualization of "
                         "project %s", source_uuid)
        return
    store_template(target, template)
    target.superset_import_status = SupersetImportStatus.PENDING.value
