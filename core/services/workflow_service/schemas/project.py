from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


# TODO:Still missing some field validation (empty name...)
class Project(BaseModel):
    uuid: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
        # helps with converting sqlalchemy models into pydantic models


class CreateProjectRequest(BaseModel):
    name: str = Field(..., max_length=30)


class CreateProjectResponse(BaseModel):
    project_uuid: UUID


class AcceptTemplateRequest(BaseModel):
    project_name: str


class CreateProjectFromTemplateRequest(BaseModel):
    name: str = Field(..., max_length=30)
    template_identifier: str  # File Name of yaml definition of DAG-Template


class CreateProjectFromTemplateResponse(BaseModel):
    project_uuid: UUID


class ReadProjectRequest(BaseModel):
    project_uuid: UUID


class ReadByUserRequest(BaseModel):
    user_uuid: UUID


class ReadByUserResponse(BaseModel):
    projects: list[Project]


class ReadAllResponse(BaseModel):
    projects: list[Project]


class RenameProjectRequest(BaseModel):
    project_uuid: UUID
    new_name: str


class DeleteProjectRequest(BaseModel):
    project_uuid: UUID
