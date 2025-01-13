from fastapi import APIRouter
from uuid import UUID
from utils.errors.error import handle_error

import services.workflow_service.controllers.DAG_translator \
    as DAG_translator
from pydantic import BaseModel


router = APIRouter(prefix="/dag", tags=["dag"])


class ProjectRequest(BaseModel):
    project_uuid: UUID


@router.post("/translate", response_model=str)
async def translate_project_to_dag(request: ProjectRequest):
    try:
        DAG_translator.translate_project_to_dag(request.project_uuid)
        return "Test complete"
    except Exception as e:
        raise handle_error(e)
