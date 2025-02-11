from fastapi import APIRouter
from uuid import UUID
from utils.errors.error import handle_error

import services.workflow_service.controllers.project_controller as \
    project_controller

from services.workflow_service.schemas.project import (
    Project,
    CreateProjectRequest,
    CreateProjectResponse,
    ReadProjectRequest,
    ReadByUserResponse,
    ReadAllResponse,
    RenameProjectRequest,
    AddNewBlockRequest
)


router = APIRouter(prefix="/project", tags=["project"])


@router.post("/", response_model=CreateProjectResponse)
async def create_project(
    data: CreateProjectRequest
):
    # TODO: Get the User_UUID from the token
    try:
        project_uuid = project_controller.create_project(
            data.name, data.user_uuid
        )
        return CreateProjectResponse(project_uuid=project_uuid)
    except Exception as e:
        raise handle_error(e)


@router.get("/", response_model=Project)
async def read_project(data: ReadProjectRequest):
    try:
        project = project_controller.read_project(data.project_uuid)
        return project
    except Exception as e:
        raise handle_error(e)


@router.get("/read_by_user", response_model=ReadByUserResponse)
async def read_projects_by_user(user_uuid: UUID):
    try:
        return project_controller.read_projects_by_user_uuid(user_uuid)
    except Exception as e:
        raise handle_error(e)


@router.get("/read_all", response_model=ReadAllResponse)
async def read_all_projects():
    try:
        projects = project_controller.read_all_projects()
        return ReadAllResponse(projects=projects)
    except Exception as e:
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
    except Exception as e:
        raise handle_error(e)


@router.put("/add_new_block", status_code=200)
async def add_new_block(data: AddNewBlockRequest):
    try:
        project_controller.add_new_block(
            data.project_uuid,
            data.name,
            data.priority_weight,
            data.retries,
            data.retry_delay,
            data.custom_name,
            data.description,
            data.author,
            data.docker_image,
            data.repo_url,
            data.selected_entrypoint_uuid,
            data.x_pos,
            data.y_pos,
            data.upstream_blocks,
            data.downstream_blocks
        )
    except Exception as e:
        raise handle_error(e)
