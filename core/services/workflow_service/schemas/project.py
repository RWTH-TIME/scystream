from uuid import UUID

from pydantic import BaseModel
from datetime import datetime
from typing import List


# TODO:Still missing any field validation (empty name, uuid is not UUID..)
class Project(BaseModel):
    uuid: UUID
    name: str
    created_at: datetime
    users: List[UUID]
    blocks: List[UUID]

    class Config:
        orm_mode = True  # ORM mode: easy conversion from SQLAlchemy objects


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
