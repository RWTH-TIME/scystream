from fastapi import APIRouter
from uuid import UUID
from utils.errors.error import handle_error

import core.services.workflow_service.controllers.DAG_translator \
    as DAG_translator


router = APIRouter(prefix="/dag", tags=["dag"])


@router.get("/translate", response_model=str)
async def translate_project_to_dag(
    data: UUID,
):
    try:
        DAG_translator.translate_project_to_dag(data.project_uuid)
        return "Test complete"
    except Exception as e:
        raise handle_error(e)
