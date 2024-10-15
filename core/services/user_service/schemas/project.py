from uuid import UUID

from pydantic import BaseModel
from utils.helper.jwt import decode_token
from fastapi import Depends
from datetime import datetime
from typing import List


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
    current_user_uuid: UUID = Depends(decode_token)


class CreateProjectResponse(BaseModel):
    project_uuid: UUID


class ReadProjectRequest(BaseModel):
    project_uuid: UUID


class ReadProjectResponse(Project):
    pass


class ReadByUserRequest(BaseModel):
    user_uuid: UUID


class ReadByUserResponse(BaseModel):
    projects: List[Project]


class ReadAllResponse(BaseModel):
    projects: List[Project]


class UpdateProjectRequest(BaseModel):
    project_uuid: UUID
    new_name: str


class UpdateProjectResponse(Project):
    pass


class DeleteProjectRequest():
    project_uuid: UUID


class DeleteProjectResponse():
    detail: str
