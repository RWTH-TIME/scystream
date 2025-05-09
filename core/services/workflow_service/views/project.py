import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from services.user_service.middleware.authenticate_token import (
    authenticate_token,
)
from services.workflow_service.controllers import (
    project_controller,
    workflow_controller,
)
from services.workflow_service.schemas.project import (
    CreateProjectRequest,
    CreateProjectResponse,
    Project,
    ReadAllResponse,
    ReadByUserResponse,
    ReadProjectRequest,
    RenameProjectRequest,
)
from utils.errors.error import handle_error
from utils.security.token import UserInfo, get_user

router = APIRouter(prefix="/project", tags=["project"])


@router.post("/", response_model=CreateProjectResponse)
async def create_project(
    data: CreateProjectRequest,
    token_data: dict = Depends(authenticate_token),
    _: UserInfo = Depends(get_user),
):
    try:
        project_uuid = project_controller.create_project(
            data.name,
            token_data["uuid"],
        )
        return CreateProjectResponse(project_uuid=project_uuid)
    except Exception as e:
        logging.exception(f"Error creating project: {e}")
        raise handle_error(e)


@router.get("/", response_model=Project)
async def read_project(
    data: ReadProjectRequest,
    _: UserInfo = Depends(get_user),
):
    try:
        project = project_controller.read_project(data.project_uuid)
        return project
    except Exception as e:
        logging.exception(f"Error reading project: {e}")
        raise handle_error(e)


@router.get("/read_by_user", response_model=ReadByUserResponse)
async def read_projects_by_user(
    user_uuid: UUID, _: UserInfo = Depends(get_user)
):
    try:
        return project_controller.read_projects_by_user_uuid(user_uuid)
    except Exception as e:
        logging.exception(f"Error reading project by user: {e}")
        raise handle_error(e)


@router.get("/read_all", response_model=ReadAllResponse)
async def read_all_projects(_: UserInfo = Depends(get_user)):
    try:
        projects = project_controller.read_all_projects()
        return ReadAllResponse(projects=projects)
    except Exception as e:
        logging.exception(f"Error reading all projects: {e}")
        raise handle_error(e)


# TODO: Rename function aswell
@router.put("/", response_model=Project)
async def rename_project(
    data: RenameProjectRequest, _: UserInfo = Depends(get_user)
):
    try:
        updated_project = project_controller.rename_project(
            data.project_uuid,
            data.new_name,
        )
        return updated_project
    except Exception as e:
        raise handle_error(e)


@router.delete("/{project_id}", status_code=200)
async def delete_project(project_id: UUID, _: UserInfo = Depends(get_user)):
    try:
        project_controller.delete_project(project_id)
        workflow_controller.delete_dag_from_airflow(project_id)
    except Exception as e:
        logging.exception(f"Error deleting project with id {project_id}: {e}")
        raise handle_error(e)
