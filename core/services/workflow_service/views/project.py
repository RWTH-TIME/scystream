from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from utils.errors.error import handle_error
import logging
from sqlalchemy.orm import Session

from services.workflow_service.controllers import (
    project_controller,
    workflow_controller,
)
from services.workflow_service.schemas.project import (
    CreateProjectRequest,
    CreateProjectResponse,
    ReadByUserResponse,
    ReadAllResponse,
    RenameProjectRequest,
    CreateProjectFromTemplateResponse,
    CreateProjectFromTemplateRequest,
    Project,
)
from utils.database.session_injector import get_database
from utils.security.token import User, get_user

router = APIRouter(prefix="/project", tags=["project"])


@router.post("/", response_model=CreateProjectResponse)
async def create_project(
    data: CreateProjectRequest,
    user: User = Depends(get_user),
    db: Session = Depends(get_database)
):
    try:
        with db.begin():
            project_uuid = project_controller.create_project(
                db, data.name, user.uuid
            )
        return CreateProjectResponse(project_uuid=project_uuid)
    except Exception as e:
        logging.exception(f"Error creating project: {e}")
        raise handle_error(e)


@router.post(
    "/from_template",
    response_model=CreateProjectFromTemplateResponse
)
async def create_project_from_template(
    data: CreateProjectFromTemplateRequest,
    user: User = Depends(get_user)
):
    try:
        id = project_controller.create_project_from_template(
            data.name,
            data.template_identifier,
            user.uuid,
        )
        return CreateProjectResponse(project_uuid=id)
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


@router.get("/{project_id}", response_model=Project)
async def read_project(
        project_id: UUID | None = None,
):
    try:
        if project_id is None:
            raise HTTPException(status=422, detail="Project ID is required")

        project = project_controller.read_project(project_id)
        return project
    except Exception as e:
        logging.error(f"Error reading project: {e}")
        raise handle_error(e)


@router.put("/", response_model=Project)
async def rename_project(
    data: RenameProjectRequest,
    db: Session = Depends(get_database)
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
