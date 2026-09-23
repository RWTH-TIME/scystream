import logging
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from sqlalchemy.orm import Session

from services.superset_service import project_sync
from services.superset_service.template import TemplateError
from services.workflow_service.controllers import (
    project_controller,
    workflow_controller,
)
from services.workflow_service.schemas.project import (
    CreateProjectResponse,
    CreateProjectFromTemplateResponse,
    Project,
    ReadAllResponse,
    ReadByUserResponse,
    RenameProjectRequest,
    SupersetDashboardResponse,
)
from utils.database.session_injector import get_database
from utils.errors.error import handle_error
from utils.security.token import User, get_user

router = APIRouter(prefix="/project", tags=["project"])

MAX_DASHBOARD_EXPORT_SIZE = 50 * 1024 * 1024


async def _read_dashboard_export(
    dashboard_export: UploadFile | None,
) -> bytes | None:
    if dashboard_export is None or not dashboard_export.filename:
        return None

    if not dashboard_export.filename.lower().endswith(
        (".zip", ".tar.gz", ".tgz"),
    ):
        raise HTTPException(
            status_code=422,
            detail="Dashboard export must be a .zip or .tar.gz file",
        )

    content = await dashboard_export.read()
    if len(content) > MAX_DASHBOARD_EXPORT_SIZE:
        raise HTTPException(
            status_code=422,
            detail="Dashboard export exceeds maximum allowed size",
        )
    if not content:
        raise HTTPException(
            status_code=422,
            detail="Dashboard export is empty",
        )

    return content


@router.post("/", response_model=CreateProjectResponse)
async def create_project(
    name: str = Form(...),
    user: User = Depends(get_user),
    db: Session = Depends(get_database),
):
    try:
        with db.begin():
            project_uuid = project_controller.create_project(
                db,
                name,
                user.uuid,
                owner_email=user.email,
            )
        return CreateProjectResponse(project_uuid=project_uuid)
    except TemplateError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.exception(f"Error creating project: {e}")
        raise handle_error(e)


@router.post(
    "/from_template", response_model=CreateProjectFromTemplateResponse
)
async def create_project_from_template(
    name: str = Form(...),
    template_identifier: str = Form(...),
    user: User = Depends(get_user),
):
    try:
        project_id = project_controller.create_project_from_template(
            name,
            template_identifier,
            user.uuid,
            owner_email=user.email,
        )
        return CreateProjectResponse(project_uuid=project_id)
    except TemplateError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.error(f"Error creating project from template: {e}")
        raise handle_error(e)


@router.get("/read_all", response_model=ReadAllResponse)
async def read_all_projects():
    try:
        projects = project_controller.read_all_projects()
        return ReadAllResponse(projects=projects)
    except Exception as e:
        logging.error(f"Error reading all projects: {e}")
        raise handle_error(e)


@router.get("/read_by_user", response_model=ReadByUserResponse)
async def read_projects_by_user(
    user: User = Depends(get_user),
):
    try:
        projects = project_controller.read_projects_by_user_uuid(user.uuid)
        return ReadByUserResponse(projects=projects)
    except Exception as e:
        logging.exception(f"Error reading project by user: {e}")
        raise handle_error(e)


@router.put("/{project_id}/dashboard_export", response_model=Project)
async def upload_dashboard_export(
    project_id: UUID,
    dashboard_export: UploadFile = File(...),
    user: User = Depends(get_user),
):
    try:
        export_bytes = await _read_dashboard_export(dashboard_export)
        if export_bytes is None:
            raise HTTPException(
                status_code=422,
                detail="Dashboard export is required",
            )

        return project_sync.upload_template(project_id, export_bytes)
    except TemplateError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.exception(
            "Error uploading dashboard export for project %s: %s",
            project_id,
            e,
        )
        raise handle_error(e)


@router.get(
    "/{project_id}/superset/dashboard",
    response_model=SupersetDashboardResponse,
)
def superset_dashboard(
    project_id: UUID,
    user: User = Depends(get_user),
):
    """Link to the project dashboard, shared with the requesting user."""
    try:
        return SupersetDashboardResponse(
            url=project_sync.dashboard_url_for_user(project_id, user.email),
        )
    except Exception as e:
        logging.exception(f"Error sharing dashboard of {project_id}: {e}")
        raise handle_error(e)


@router.get("/{project_id}/superset/template")
def download_superset_template(
    project_id: UUID,
    _: User = Depends(get_user),
):
    """The project's visualization as Superset export, usable as template
    for other projects."""
    try:
        content = project_sync.export_template(project_id)
        return Response(
            content=content,
            media_type="application/zip",
            headers={
                "Content-Disposition":
                f'attachment; filename="superset-template-{project_id}.zip"',
            },
        )
    except Exception as e:
        logging.exception(f"Error exporting template of {project_id}: {e}")
        raise handle_error(e)


@router.post("/{project_id}/superset/sync", response_model=Project)
def sync_superset(
    project_id: UUID,
    _: User = Depends(get_user),
):
    """Syncs the project's data and dashboard to Superset now."""
    try:
        return project_sync.sync_project(project_id)
    except Exception as e:
        logging.exception(f"Error syncing {project_id} to Superset: {e}")
        raise handle_error(e)


@router.post("/{project_id}/clone", response_model=CreateProjectResponse)
def clone_project(
    project_id: UUID,
    name: str = Form(..., max_length=30),
    user: User = Depends(get_user),
):
    try:
        clone_uuid = project_controller.clone_project(
            project_id, name, user.uuid, owner_email=user.email,
        )
        return CreateProjectResponse(project_uuid=clone_uuid)
    except Exception as e:
        logging.exception(f"Error cloning project {project_id}: {e}")
        raise handle_error(e)


@router.get("/{project_id}", response_model=Project)
async def read_project(
    project_id: UUID | None = None,
):
    try:
        if project_id is None:
            raise HTTPException(
                status_code=422,
                detail="Project ID is required",
            )

        project = project_controller.read_project(project_id)
        return project
    except Exception as e:
        logging.error(f"Error reading project: {e}")
        raise handle_error(e)


@router.put("/", response_model=Project)
async def rename_project(
    data: RenameProjectRequest, db: Session = Depends(get_database)
):
    try:
        with db.begin():
            updated_project = project_controller.rename_project(
                data.project_uuid, data.new_name, db
            )
        return updated_project
    except Exception as e:
        raise handle_error(e)


@router.delete("/{project_id}", status_code=200)
async def delete_project(project_id: UUID, _: User = Depends(get_user)):
    try:
        project_controller.delete_project(project_id)
        workflow_controller.delete_dag_from_airflow(project_id)
    except Exception as e:
        logging.exception(f"Error deleting project with id {project_id}: {e}")
        raise handle_error(e)
