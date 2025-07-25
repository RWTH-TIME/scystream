import asyncio
import logging
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from services.workflow_service.controllers import workflow_controller
from services.workflow_service.schemas.workflow import WorkflowStatus
from utils.errors.error import handle_error
from utils.security.token import User, get_user, get_user_from_token

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/{project_id}", status_code=200)
def translate_project_to_dag(
    project_id: UUID | None = None,
    _: User = Depends(get_user),
):
    if not project_id:
        raise HTTPException(status_code=422, detail="Project ID missing")

    try:
        workflow_controller.validate_workflow(project_id)
        dag_id = workflow_controller.translate_project_to_dag(project_id)
        # Make sure airflow has enough time to create the dag internally
        if not workflow_controller.wait_for_dag_registration(dag_id):
            logging.error(f"DAG {dag_id} was not registered in time.")
            raise HTTPException(
                status_code=500,
                detail="DAG was not registered in time.",
            )
        workflow_controller.trigger_workflow_run(dag_id)
    except Exception as e:
        raise handle_error(e)


@router.post("/{project_id}/pause", status_code=200)
def pause_dag(
    project_id: UUID | None = None,
    _: User = Depends(get_user),
):
    if not project_id:
        raise HTTPException(status_code=422, detail="Project ID missing")

    dag_id = f"dag_{str(project_id).replace("-", "_")}"

    try:
        workflow_controller.unpause_dag(dag_id, True)
    except Exception as e:
        raise handle_error(e)


@router.websocket("/ws/project_status")
async def ws_project_status(
    websocket: WebSocket,
    _: User = Depends(get_user_from_token),
):
    """Returns the DAG statuses"""
    await websocket.accept()

    try:
        while True:
            all_dags = workflow_controller.get_all_dags()
            dag_runs = workflow_controller.last_dag_run_overview(all_dags)

            all_proj_status = {}

            for di, dr in dag_runs.items():
                project_id = workflow_controller.dag_id_to_project_id(di)
                status = WorkflowStatus.from_airflow_state(
                    str(dr.get("state")),
                )

                all_proj_status[project_id] = status.value

            await websocket.send_json(all_proj_status)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logging.info(f"Websocket disconnected for project {project_id!s}")
    except Exception as e:
        logging.exception(f"Error in ws_workflow_status: {e}")
        await websocket.close(code=1011)


@router.websocket("/ws/workflow_status/{project_id}")
async def ws_workflow_status(
    websocket: WebSocket,
    project_id: UUID,
    _: User = Depends(get_user_from_token),
):
    """Returns the status of the blocks within a workflow"""
    await websocket.accept()

    try:
        while True:
            status = workflow_controller.dag_status(project_id)
            await websocket.send_json(status)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logging.info(f"Websocket disconnected for project {project_id!s}")
    except Exception as e:
        logging.exception(f"Error in ws_workflow_status: {e}")
        await websocket.close(code=1011)
