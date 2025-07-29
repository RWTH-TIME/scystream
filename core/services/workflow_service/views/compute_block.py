import logging
from uuid import UUID

from sqlalchemy.orm import Session
from utils.database.session_injector import get_database
from utils.errors.error import handle_error
from utils.data.file_handling import bulk_presigned_urls_from_ios
from services.workflow_service.models.input_output import (
    InputOutputType
)
from services.workflow_service.schemas.compute_block import (
    ComputeBlockInformationRequest, ComputeBlockInformationResponse,
    CreateComputeBlockRequest, IDResponse,
    GetNodesByProjectResponse,
    EdgeDTO, SimpleNodeDTO, InputOutputDTO, BaseInputOutputDTO,
    UpdateInputOutuputResponseDTO, UpdateComputeBlockDTO, ConfigType,
    BlockStatus
)
from fastapi import APIRouter, Depends, HTTPException
from services.workflow_service.controllers import workflow_controller
from services.workflow_service.controllers.compute_block_controller import (
    bulk_upload_files,
    create_compute_block,
    create_stream_and_update_target_cfg,
    delete_block,
    delete_edge,
    get_block_dependencies_for_blocks,
    get_compute_blocks_by_project,
    get_envs_for_entrypoint,
    get_io_for_entrypoint,
    request_cb_info,
    update_block,
    update_ios_with_uploads
)
from utils.security.token import User, get_user

router = APIRouter(prefix="/compute_block", tags=["compute_block"])


@router.post("/information", response_model=ComputeBlockInformationResponse)
async def cb_information(
    data: ComputeBlockInformationRequest,
    _: User = Depends(get_user),
):
    try:
        cb = request_cb_info(
            data.cbc_url,
        )
        return ComputeBlockInformationResponse.from_sdk_compute_block(cb)
    except Exception as e:
        logging.exception(f"Error getting compute block information: {e}")
        raise handle_error(e)


@router.post("/", response_model=SimpleNodeDTO)
async def create(
    data: CreateComputeBlockRequest,
    _: User = Depends(get_user),
    db: Session = Depends(get_database)
):
    try:
        """
        Upload the files to the default bucket and update the configs
        accordingly
        """
        updated_is = bulk_upload_files(
            data.selected_entrypoint.inputs,
        )

        with db.begin():
            cb = create_compute_block(
                db,
                data.name,
                data.description,
                data.author,
                data.image,
                data.cbc_url,
                data.custom_name,
                data.x_pos,
                data.y_pos,
                data.selected_entrypoint.name,
                data.selected_entrypoint.description,
                data.selected_entrypoint.envs,
                [input.to_input_output(input, "Input")
                 for input in updated_is],
                [output.to_input_output(output, "Output")
                 for output in data.selected_entrypoint.outputs],
                data.project_id,
            )
            return SimpleNodeDTO.from_compute_block(cb)
    except Exception as e:
        logging.exception(f"Error creating compute block: {e}")
        raise handle_error(e)


@router.get(
    "/by_project/{project_id}",
    response_model=GetNodesByProjectResponse,
)
async def get_by_project(
    project_id: UUID | None = None,
    _: User = Depends(get_user),
):
    if not project_id:
        raise HTTPException(status_code=422, detail="Project ID is required.")

    try:
        compute_blocks = get_compute_blocks_by_project(project_id)
        status = workflow_controller.dag_status(project_id)

        block_uuids = [block.uuid for block in compute_blocks]
        dependencies = get_block_dependencies_for_blocks(block_uuids)

        return GetNodesByProjectResponse(
            blocks=[
                SimpleNodeDTO.from_compute_block(
                    cb,
                    status.get(str(cb.uuid), BlockStatus.IDLE),
                )
                for cb in compute_blocks
            ],
            edges=[EdgeDTO.from_block_dependencies(dp) for dp in dependencies],
        )
    except Exception as e:
        logging.exception(f"Error getting compute blocks by project: {e}")
        raise handle_error(e)


@router.get("/entrypoint/{entry_id}/envs/", response_model=ConfigType)
async def get_envs(
    entry_id: UUID | None = None,
    _: User = Depends(get_user),
):
    if not entry_id:
        raise HTTPException(
            status_code=422,
            detail="Entrypoint ID is required.",
        )

    try:
        return get_envs_for_entrypoint(entry_id)
    except Exception as e:
        logging.exception(f"Error getting envs of entrypoint {entry_id}: {e}")
        raise handle_error(e)


@router.put("/", response_model=UpdateComputeBlockDTO)
async def update_compute_block(
    data: UpdateComputeBlockDTO,
    _: User = Depends(get_user),
):
    try:
        b = update_block(
            data.id,
            data.envs,
            data.custom_name,
            data.x_pos,
            data.y_pos,
        )
        return UpdateComputeBlockDTO(
            id=b.uuid,
            envs=b.selected_entrypoint.envs,
            custom_name=b.custom_name,
            x_pos=b.x_pos,
            y_pos=b.y_pos,
        )
    except Exception as e:
        logging.exception(f"Error updating compute block {data.id}: {e}")
        raise handle_error(e)


@router.get("/entrypoint/{entry_id}/io/", response_model=list[InputOutputDTO])
async def get_io(
    entry_id: UUID,
    io_type: InputOutputType,
    _: User = Depends(get_user),
):
    if not entry_id:
        raise HTTPException(
            status_code=422,
            detail="Entrypoint ID is required.",
        )
    try:
        ios = get_io_for_entrypoint(entry_id, io_type)
        presigned_urls = bulk_presigned_urls_from_ios(ios)
        return [InputOutputDTO.from_input_output(
            io.name,
            io,
            presigned_urls.get(io.uuid, None)) for io in ios
        ]
    except Exception as e:
        logging.exception(
            f"Error getting {io_type.value}s of entrypoint {entry_id}: {e}",
        )
        raise handle_error(e)


@router.put("/entrypoint/io/",
            response_model=list[UpdateInputOutuputResponseDTO])
async def update_io(data: list[BaseInputOutputDTO]):
    db = next(get_database())
    try:
        with db.begin():
            updated = update_ios_with_uploads(data, db)

        presigneds = bulk_presigned_urls_from_ios(updated)

        return [
            UpdateInputOutuputResponseDTO.from_input_output(
                io,
                presigneds.get(io.uuid),
                presigneds.get(str(io.uuid)),
            )
            for io in updated
        ]

    except Exception as e:
        logging.exception(
            f"Error updating ios with ids {[d.id for d in data]}: {e}",
        )
        raise handle_error(e)


@router.delete("/{block_id}", status_code=200)
async def delete_compute_block(
    block_id: UUID | None = None,
    _: User = Depends(get_user),
):
    if not block_id:
        return HTTPException(
            status_code=422,
            detail="Compute Block id required.",
        )

    try:
        delete_block(block_id)
    except Exception as e:
        logging.exception(f"Error deleting compute block: {e}")
        raise handle_error(e)


@router.post("/edge", response_model=IDResponse)
def create_io_stream_and_update_io_cfg(
    data: EdgeDTO,
    _: User = Depends(get_user),
):
    db = next(get_database())

    try:
        with db.begin():
            id = create_stream_and_update_target_cfg(
                db,
                data.source,
                data.sourceHandle,
                data.target,
                data.targetHandle
            )
        return IDResponse(id=id)
    except Exception as e:
        logging.exception(f"Error creating an edge and configuring input: {e}")
        raise handle_error(e)


@router.post("/edge/delete", status_code=200)
def delete_stream(
    data: EdgeDTO,
    _: User = Depends(get_user),
):
    try:
        delete_edge(
            data.source,
            data.sourceHandle,
            data.target,
            data.targetHandle,
        )
    except Exception as e:
        logging.exception(f"Error deleting an edge: {e}")
        raise handle_error(e)
