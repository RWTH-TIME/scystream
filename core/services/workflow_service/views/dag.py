from fastapi import APIRouter
from uuid import UUID
from utils.errors.error import handle_error

import services.workflow_service.controllers.DAG_translator \
    as DAG_translator
import services.workflow_service.controllers.project_controller \
    as project_controller
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


class CreateTestDagRequest(BaseModel):
    project_name: str
    current_user_uuid: UUID

    block_name: str
    block_project_uuid: UUID

    block_priority_weight: int
    block_retries: int
    block_retry_delay: int

    block_custom_name: str
    block_description: str
    block_author: str
    block_docker_image: str
    block_repo_url: str
    block_selected_entrypoint_uuid: UUID
    block_x_pos: float
    block_y_pos:    float

    block_schedule_interval: str
    block_environment: str
    block_upstream_blocks_uuids: List[UUID]


router = APIRouter(prefix="/dag", tags=["dag"])


@router.get("/create_test_dag", response_model=str)
async def create_test_dag(
    data: CreateTestDagRequest,
):
    try:
        project_controller.create_project(
            data.project_namename,
            data.current_user_uuid
        )

    except Exception as e:
        raise handle_error(e)


@router.get("/translate", response_model=str)
async def translate_project_to_dag(
    data.project_uuid: UUID,
):
    try:
        DAG_translator.translate_project_to_dag(data)
        return "Test complete"
    except Exception as e:
        raise handle_error(e)
