from uuid import UUID

from pydantic import BaseModel
from datetime import datetime
from typing import List


# TODO:Still missing some field validation (empty name...)
class Project(BaseModel):
    uuid: UUID
    name: str
    created_at: datetime
    users: List[UUID]
    blocks: List[UUID]

    class Config:
        from_attributes = True
        # helps with converting sqlalchemy models into pydantic models


class CreateProjectRequest(BaseModel):
    name: str


class CreateProjectResponse(BaseModel):
    project_uuid: UUID


class ReadProjectRequest(BaseModel):
    project_uuid: UUID


class ReadByUserRequest(BaseModel):
    user_uuid: UUID


class ReadByUserResponse(BaseModel):
    projects: List[Project]


class ReadAllResponse(BaseModel):
    projects: List[Project]


class RenameProjectRequest(BaseModel):
    project_uuid: UUID
    new_name: str


class DeleteProjectRequest(BaseModel):
    project_uuid: UUID
