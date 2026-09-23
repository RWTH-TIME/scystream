import asyncio
import logging
from collections import defaultdict
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from services.workflow_service.controllers import (
    compute_block_controller as compute_block_controller,
)
from services.workflow_service.controllers import (
    project_controller as project_controller,
)
from services.workflow_service.controllers import (
    shared_template_controller,
    workflow_controller,
)
from services.superset_service.project_sync import sync_finished_runs
from services.workflow_service.schemas.workflow import (
    GetWorkflowConfigurationResponse,
    InputOutputWithBlockInfo,
    UpdateWorkflowConfigurations,
    WorkflowStatus,
    WorkflowTemplateMetaData,
    CreateSharedTemplateRequest,
)
from utils.database.session_injector import get_database
from utils.errors.error import handle_error
from utils.security.token import User, get_user, get_user_from_token

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get(
    "/configurations/{project_id}",
    response_model=GetWorkflowConfigurationResponse,
)
def get_workflow_configurations(
    project_id: UUID | None = None,
):
    if not project_id:
        raise HTTPException(
            status_code=422,
            detail="Project ID missing",
        )

    try:
        envs, inputs, inter, outputs, presigned, block_by_entry_id = (
            workflow_controller.get_workflow_configurations(
                project_id,
            )
        )

        return GetWorkflowConfigurationResponse(
            envs=envs,
            workflow_inputs=[
                InputOutputWithBlockInfo.from_input_output(
                    i.name,
                    i,
                    block_by_entry_id.get(i.entrypoint_uuid).uuid,
                    block_by_entry_id.get(i.entrypoint_uuid).custom_name,
                    presigned.get(i.uuid, None),
                )
                for i in inputs
            ],
            workflow_intermediates=[
                InputOutputWithBlockInfo.from_input_output(
                    i.name,
                    i,
                    block_by_entry_id.get(i.entrypoint_uuid).uuid,
                    block_by_entry_id.get(i.entrypoint_uuid).custom_name,
                    presigned.get(i.uuid, None),
                )
                for i in inter
            ],
            workflow_outputs=[
                InputOutputWithBlockInfo.from_input_output(
                    o.name,
                    o,
                    block_by_entry_id.get(o.entrypoint_uuid).uuid,
                    block_by_entry_id.get(o.entrypoint_uuid).custom_name,
                    presigned.get(o.uuid, None),
                )
                for o in outputs
            ],
        )
    except Exception as e:
        logging.exception(
            f"Exception when getting workflow configurations: {e}",
        )
        raise handle_error(e)


@router.put(
    "/configurations/{project_id}",
    status_code=200,
)
def update_workflow_configurations(
    project_id: UUID | None,
    data: UpdateWorkflowConfigurations,
):
    if not project_id:
        raise HTTPException(
            status_code=422,
            detail="Project ID missing",
        )

    db = next(get_database())

    try:
        with db.begin():
            if data.project_name:
                project_controller.rename_project(
                    project_uuid=project_id,
                    new_name=data.project_name,
                    db=db,
                )

            if data.envs:
                updated_blocks = (
                    compute_block_controller.bulk_update_block_envs(
                        db=db,
                        updates=[
                            compute_block_controller.BulkBlockEnvsUpdate(
                                block_id=envdto.block_uuid,
                                envs=envdto.envs,
                            )
                            for envdto in data.envs
                        ],
                    )
                )
                logging.info(updated_blocks)

            if data.ios:
                updated_ios = compute_block_controller.update_ios_with_uploads(
                    db=db,
                    data=data.ios,
                )
                logging.info(updated_ios)

    except Exception as e:
        logging.exception(f"Error updaing workflow configs: {e}")
        raise handle_error(e)


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


@router.get(
    "/workflow_templates",
    response_model=dict[str, list[WorkflowTemplateMetaData]],
)
def workflow_templates(user: User = Depends(get_user)):
    try:
        shared = {
            shared_template_controller.shared_identifier(r.uuid): r
            for r in shared_template_controller.list_shared_templates()
        }
        grouped_templates = workflow_controller.get_tagged_workflow_templates()

        result = defaultdict(list)
        for tag, templates in grouped_templates.items():
            for tpl in templates:
                record = shared.get(tpl.file_identifier)
                result[tag].append(
                    WorkflowTemplateMetaData(
                        file_identifier=tpl.file_identifier,
                        name=tpl.pipeline.name,
                        description=tpl.pipeline.description,
                        shared=record is not None,
                        created_by_email=record.created_by_email
                        if record else None,
                        can_delete=record is not None
                        and record.created_by == user.uuid,
                    ),
                )
        return dict(result)
    except Exception as e:
        raise handle_error(e)


@router.post("/workflow_templates", response_model=WorkflowTemplateMetaData)
def create_workflow_template(
    data: CreateSharedTemplateRequest,
    user: User = Depends(get_user),
):
    """Saves a project as template for all users."""
    try:
        record = shared_template_controller.create_shared_template(
            data.project_uuid,
            data.name,
            data.description,
            data.tags,
            user.uuid,
            user.email,
            include_settings=data.include_settings,
        )
        return WorkflowTemplateMetaData(
            file_identifier=shared_template_controller.shared_identifier(
                record.uuid,
            ),
            name=record.name,
            description=record.description,
            shared=True,
            created_by_email=record.created_by_email,
            can_delete=True,
        )
    except Exception as e:
        raise handle_error(e)


@router.get("/workflow_templates/{identifier}/yaml")
def workflow_template_yaml(identifier: str, _: User = Depends(get_user)):
    """A shared template in the format of the template repository."""
    try:
        return Response(
            content=shared_template_controller.template_yaml(identifier),
            media_type="application/yaml",
        )
    except Exception as e:
        raise handle_error(e)


@router.delete("/workflow_templates/{identifier}", status_code=200)
def delete_workflow_template(identifier: str, user: User = Depends(get_user)):
    try:
        shared_template_controller.delete_shared_template(
            identifier, user.uuid,
        )
    except Exception as e:
        raise handle_error(e)


def _collect_project_statuses() -> dict[str, str]:
    """Polls Airflow for the latest run of every project DAG and syncs the
    data of newly finished runs to Superset.

    This is blocking I/O and must not run on the event loop.
    """
    all_proj_status = {}
    finished_runs = {}

    all_dags = workflow_controller.get_all_dags()
    dag_runs = workflow_controller.last_dag_run_overview(all_dags)

    for di, dr in dag_runs.items():
        project_id = workflow_controller.dag_id_to_project_id(di)
        status = WorkflowStatus.from_airflow_state(dr.state)
        all_proj_status[project_id] = status.value
        if status == WorkflowStatus.FINISHED:
            finished_runs[project_id] = dr.dag_run_id

    sync_finished_runs(finished_runs)

    return all_proj_status


@router.websocket("/ws/project_status")
async def ws_project_status(
    websocket: WebSocket,
    _: User = Depends(get_user_from_token),
):
    """Returns the DAG statuses."""
    await websocket.accept()

    try:
        while True:
            all_proj_status = {}

            try:
                all_proj_status = await asyncio.to_thread(
                    _collect_project_statuses,
                )
            except Exception as e:
                logging.exception("Error polling project status: %s", e)

            await websocket.send_json(all_proj_status)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logging.info("Websocket disconnected for a project")
    except Exception as e:
        logging.exception(f"Error in ws_workflow_status: {e}")
        await websocket.close(code=1011)


@router.websocket("/ws/workflow_status/{project_id}")
async def ws_workflow_status(
    websocket: WebSocket,
    project_id: UUID,
    _: User = Depends(get_user_from_token),
):
    """Returns the status of the blocks within a workflow."""
    await websocket.accept()

    try:
        while True:
            status = await asyncio.to_thread(
                workflow_controller.dag_status,
                project_id,
            )
            await websocket.send_json(status)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logging.info(f"Websocket disconnected for project {project_id!s}")
    except Exception as e:
        logging.exception(f"Error in ws_workflow_status: {e}")
        await websocket.close(code=1011)
