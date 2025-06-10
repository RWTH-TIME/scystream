from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from uuid import UUID
from utils.errors.error import handle_error
import asyncio
import logging

from services.workflow_service.controllers import workflow_controller
from services.workflow_service.schemas.workflow import (
    WorkflowStatus, WorkflowTemplateMetaData, GetWorkflowConfigurationResponse
)
from services.workflow_service.schemas.compute_block import (
    InputOutputDTO
)

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get(
    "/configurations/{project_id}",
    response_model=GetWorkflowConfigurationResponse
)
def get_workflow_configurations(
        project_id: UUID | None = None
):
    if not project_id:
        raise HTTPException(
            status_code=422,
            detail="Project ID missing"
        )

    try:
        envs, inputs, inter, outputs, presigned = \
            workflow_controller.get_workflow_configurations(
                project_id
            )

        return GetWorkflowConfigurationResponse(
            envs=envs,
            workflow_inputs=[
                InputOutputDTO.from_input_output(
                    i.name,
                    i,
                    presigned.get(i.uuid, None),
                ) for i in inputs
            ],
            workflow_intermediates=[
                InputOutputDTO.from_input_output(
                    i.name,
                    i,
                    presigned.get(i.uuid, None),
                ) for i in inter
            ],
            workflow_outputs=[
                InputOutputDTO.from_input_output(
                    o.name,
                    o,
                    presigned.get(o.uuid, None),
                ) for o in outputs
            ]
        )
    except Exception as e:
        logging.exception(
            f"Exception when getting workflow configurations: {e}")
        raise handle_error(e)


@router.post("/{project_id}", status_code=200)
def translate_project_to_dag(
    project_id: UUID | None = None
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
                status_code=500, detail="DAG was not registered in time."
            )
        workflow_controller.trigger_workflow_run(dag_id)
    except Exception as e:
        raise handle_error(e)


@router.post("/{project_id}/pause", status_code=200)
def pause_dag(
    project_id: UUID | None = None
):
    if not project_id:
        raise HTTPException(status_code=422, detail="Project ID missing")

    dag_id = f"dag_{str(project_id).replace("-", "_")}"

    try:
        workflow_controller.unpause_dag(dag_id, True)
    except Exception as e:
        raise handle_error(e)


@router.get(
    "/workflow_templates",
    response_model=list[WorkflowTemplateMetaData]
)
async def workflow_templates():
    try:
        templates = workflow_controller.get_workflow_templates()
        return [
            WorkflowTemplateMetaData(
                file_identifier=tpl.file_identifier,
                name=tpl.pipeline.name,
                description=tpl.pipeline.description,
            )
            for tpl in templates
        ]
    except Exception as e:
        raise handle_error(e)


@router.websocket("/ws/project_status")
async def ws_project_status(websocket: WebSocket):
    """
    Returns the DAG statuses
    """
    await websocket.accept()

    try:
        while True:
            all_dags = workflow_controller.get_all_dags()
            dag_runs = workflow_controller.last_dag_run_overview(all_dags)

            all_proj_status = {}

            for di, dr in dag_runs.items():
                project_id = workflow_controller.dag_id_to_project_id(di)
                status = WorkflowStatus.from_airflow_state(
                    str(dr.get("state"))
                )

                all_proj_status[project_id] = status.value

            await websocket.send_json(all_proj_status)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logging.info(f"Websocket disconnected for project {str(project_id)}")
    except Exception as e:
        logging.error(f"Error in ws_workflow_status: {e}")
        await websocket.close(code=1011)


@router.websocket("/ws/workflow_status/{project_id}")
async def ws_workflow_status(websocket: WebSocket, project_id: UUID):
    """
    Returns the status of the blocks within a workflow
    """
    await websocket.accept()

    try:
        while True:
            status = workflow_controller.dag_status(project_id)
            await websocket.send_json(status)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logging.info(f"Websocket disconnected for project {str(project_id)}")
    except Exception as e:
        logging.error(f"Error in ws_workflow_status: {e}")
        await websocket.close(code=1011)
