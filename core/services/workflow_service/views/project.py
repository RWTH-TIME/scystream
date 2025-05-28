from fastapi import APIRouter, Depends
from uuid import UUID
from utils.errors.error import handle_error
import logging

import services.workflow_service.controllers.project_controller as \
    project_controller
import services.workflow_service.controllers.workflow_controller as \
    workflow_controller
from services.workflow_service.schemas.project import (
    Project,
    CreateProjectRequest,
    CreateProjectResponse,
    ReadProjectRequest,
    ReadByUserResponse,
    ReadAllResponse,
    RenameProjectRequest,
    CreateProjectFromTemplateResponse,
    CreateProjectFromTemplateRequest
)
from services.user_service.middleware.authenticate_token import (
    authenticate_token,
)
from utils.database.session_injector import get_database


router = APIRouter(prefix="/project", tags=["project"])


@router.post("/", response_model=CreateProjectResponse)
async def create_project(
    data: CreateProjectRequest,
    token_data: dict = Depends(authenticate_token)
):
    db = next(get_database())
    try:
        with db.begin():
            project_uuid = project_controller.create_project(
                db, data.name, token_data["uuid"]
            )
        return CreateProjectResponse(project_uuid=project_uuid)
    except Exception as e:
        logging.error(f"Error creating project: {e}")
        raise handle_error(e)


@router.post(
    "/from_template",
    response_model=CreateProjectFromTemplateResponse
)
async def create_project_from_template(
    data: CreateProjectFromTemplateRequest,
    # token_data: dict = Depends(authenticate_token)
):
    try:
        id = project_controller.create_project_from_template(
            data.name,
            data.template_identifier,
            "a654459c-c021-4f3d-80ad-8bb5b51a0d20"
        )
        return CreateProjectResponse(project_uuid=id)
    except Exception as e:
        logging.error(f"Error creating project from template: {e}")
        raise handle_error(e)


@router.get("/", response_model=Project)
async def read_project(
        data: ReadProjectRequest,
):
    try:
        project = project_controller.read_project(data.project_uuid)
        return project
    except Exception as e:
        logging.error(f"Error reading project: {e}")
        raise handle_error(e)


@router.get("/read_by_user", response_model=ReadByUserResponse)
async def read_projects_by_user(user_uuid: UUID):
    try:
        return project_controller.read_projects_by_user_uuid(user_uuid)
    except Exception as e:
        logging.error(f"Error reading project by user: {e}")
        raise handle_error(e)


@router.get("/read_all", response_model=ReadAllResponse)
async def read_all_projects():
    try:
        projects = project_controller.read_all_projects()
        return ReadAllResponse(projects=projects)
    except Exception as e:
        logging.error(f"Error reading all projects: {e}")
        raise handle_error(e)


# TODO: Rename function aswell
@router.put("/", response_model=Project)
async def rename_project(data: RenameProjectRequest):
    try:
        updated_project = project_controller.rename_project(
            data.project_uuid, data.new_name
        )
        return updated_project
    except Exception as e:
        raise handle_error(e)


@router.delete("/{project_id}", status_code=200)
async def delete_project(
    project_id: UUID | None = None
):
    try:
        project_controller.delete_project(project_id)
        workflow_controller.delete_dag_from_airflow(project_id)
    except Exception as e:
        logging.error(f"Error deleting project with id {project_id}: {e}")
        raise handle_error(e)
