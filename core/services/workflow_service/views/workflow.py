from fastapi import APIRouter, HTTPException
from uuid import UUID
from utils.errors.error import handle_error
from services.workflow_service.controllers import workflow_controller

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/{project_id}", status_code=200)
def translate_project_to_dag(
    project_id: UUID | None = None
):
    if not project_id:
        raise HTTPException(status_code=422, detail="Project ID missing")

    try:
        workflow_controller.validate_workflow(project_id)
        dag_id = workflow_controller.translate_project_to_dag(project_id)
        workflow_controller.trigger_workflow_run(dag_id)
    except Exception as e:
        raise handle_error(e)
