from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from uuid import UUID
from utils.errors.error import handle_error
import asyncio

from services.workflow_service.controllers import workflow_controller
from services.workflow_service.schemas.workflow import WorkflowStatus

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


@router.websocket("/ws/project_status")
async def ws_project_status(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            all_dags = workflow_controller.get_all_dags()
            dag_runs = workflow_controller.last_dag_run_overview(all_dags)

            all_proj_status = {}

            for di, dr in dag_runs.items():
                project_id = di.replace(
                    "dag_", "").replace("_", "-")
                status = WorkflowStatus.from_airflow_state(
                    str(dr.get("state"))
                )

                all_proj_status[project_id] = status.value

            await websocket.send_json(all_proj_status)
            await asyncio.sleep(5)
    except WebSocketDisconnect as e:
        raise handle_error(e)

# TODO: Websocket for Compute Block Status
