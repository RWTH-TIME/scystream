from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from utils.errors.error import handle_error

from services.user_service.schemas.project import (
    Project,
    CreateProjectRequest,
    CreateProjectResponse,
    ReadProjectRequest,
    ReadProjectResponse,
    ReadAllResponse,
    UpdateProjectRequest,
    UpdateProjectResponse,
    DeleteProjectRequest,
    DeleteProjectResponse
)


import services.user_service.controllers.project_controller as \
    project_controller


router = APIRouter(prefix="/project", tags=["project"])


# Create, Read, ReadByUserUuid, ReadAll, Update, Delete
@router.post("/create", response_model=CreateProjectResponse)
async def create_project(data: CreateProjectRequest):
    try:
        project_uuid = project_controller.create_project(
            data.name,
            data.current_user_uuid
        )
        return CreateProjectResponse(project_uuid=project_uuid)
    except Exception as e:
        raise handle_error(e)


@router.get("/read", response_model=ReadProjectResponse)
async def read_project(data: ReadProjectRequest):
    try:
        project = project_controller.read_project(data.project_uuid)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        raise handle_error(e)


@router.get("/read_by_user", response_model=List[Project])
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


@router.put("/update", response_model=UpdateProjectResponse)
async def update_project(data: UpdateProjectRequest):
    try:
        updated_project = project_controller.update_project(
            data.project_uuid,
            data.new_name
        )
        return UpdateProjectResponse(updated_project)
    except Exception as e:
        raise handle_error(e)


@router.delete("/delete", response_model=DeleteProjectResponse)
async def delete_project(data: DeleteProjectRequest):
    try:
        project_controller.delete_project(data.project_uuid)
        return DeleteProjectResponse(detail="Project deleted successfully")
    except Exception as e:
        raise handle_error(e)
