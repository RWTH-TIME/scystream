from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
import logging

from utils.errors.error import handle_error
from services.workflow_service.models.input_output import InputOutputType
from services.workflow_service.schemas.compute_block import (
    ComputeBlockInformationRequest, ComputeBlockInformationResponse,
    CreateComputeBlockRequest, IDResponse,
    GetNodesByProjectResponse,
    EdgeDTO, SimpleNodeDTO, InputOutputDTO, BaseInputOutputDTO,
    UpdateInputOutuputResponseDTO, UpdateComputeBlockDTO, ConfigType
)
from services.user_service.middleware.authenticate_token import (
    authenticate_token,
)
from services.workflow_service.controllers.compute_block_controller import (
    request_cb_info, create_compute_block, get_compute_blocks_by_project,
    delete_block, create_stream_and_update_target_cfg,
    get_block_dependencies_for_blocks, delete_edge, get_envs_for_entrypoint,
    get_io_for_entrypoint, update_ios, update_block
)
import services.workflow_service.controllers.workflow_controller as \
    workflow_controller

router = APIRouter(prefix="/compute_block", tags=["compute_block"])


@router.post("/information", response_model=ComputeBlockInformationResponse)
async def cb_information(
    data: ComputeBlockInformationRequest,
    _: dict = Depends(authenticate_token)
):
    try:
        cb = request_cb_info(
            data.cbc_url,
        )
        return ComputeBlockInformationResponse.from_sdk_compute_block(cb)
    except Exception as e:
        logging.error(f"Error getting compute block information: {e}")
        raise handle_error(e)


@router.post("/", response_model=SimpleNodeDTO)
async def create(
    data: CreateComputeBlockRequest,
    _: dict = Depends(authenticate_token)
):
    try:
        cb = create_compute_block(
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
             for input in data.selected_entrypoint.inputs],
            [output.to_input_output(output, "Output")
             for output in data.selected_entrypoint.outputs],
            data.project_id
        )
        return SimpleNodeDTO.from_compute_block(cb)
    except Exception as e:
        logging.error(f"Error creating compute block: {e}")
        raise handle_error(e)


@router.get("/by_project/{project_id}",
            response_model=GetNodesByProjectResponse)
async def get_by_project(
    project_id: UUID | None = None
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
                    cb, status.get(str(cb.uuid)))
                for cb in compute_blocks
            ],
            edges=[EdgeDTO.from_block_dependencies(
                dp) for dp in dependencies
            ]
        )
    except Exception as e:
        logging.error(f"Error getting compute blocks by project: {e}")
        raise handle_error(e)


@router.get("/entrypoint/{entry_id}/envs/",
            response_model=ConfigType)
async def get_envs(
    entry_id: UUID | None = None
):
    if not entry_id:
        raise HTTPException(
            status_code=422, detail="Entrypoint ID is required.")

    try:
        return get_envs_for_entrypoint(entry_id)
    except Exception as e:
        logging.error(f"Error getting envs of entrypoint {entry_id}: {e}")
        raise handle_error(e)


@router.put("/",
            response_model=UpdateComputeBlockDTO)
async def update_compute_block(
    data: UpdateComputeBlockDTO
):
    try:
        b = update_block(
            data.id,
            data.envs,
            data.custom_name,
            data.x_pos,
            data.y_pos
        )
        return UpdateComputeBlockDTO(
            id=b.uuid,
            envs=b.selected_entrypoint.envs,
            custom_name=b.custom_name,
            x_pos=b.x_pos,
            y_pos=b.y_pos
        )
    except Exception as e:
        logging.error(f"Error updating compute block {data.id}: {e}")
        raise handle_error(e)


@router.get("/entrypoint/{entry_id}/io/", response_model=list[InputOutputDTO])
async def get_io(
    entry_id: UUID,
    io_type: InputOutputType
):
    if not entry_id:
        raise HTTPException(
            status_code=422, detail="Entrypoint ID is required."
        )

    try:
        ios = get_io_for_entrypoint(entry_id, io_type)
        return [InputOutputDTO.from_input_output(io.name, io) for io in ios]
    except Exception as e:
        logging.error(f"Error getting {
                      io_type.value}s of entrypoint {entry_id}: {e}")
        raise handle_error(e)


@router.put("/entrypoint/io/",
            response_model=list[UpdateInputOutuputResponseDTO])
async def update_io(data: list[BaseInputOutputDTO]):
    try:
        id_to_config_map: dict[UUID, ConfigType] = {
            d.id: d.config for d in data
        }
        updated = update_ios(id_to_config_map)
        return [UpdateInputOutuputResponseDTO.from_input_output(io)
                for io in updated]
    except Exception as e:
        logging.error(f"Error updating ios with ids {
                      list(id_to_config_map.keys())}: {e}")
        raise handle_error(e)


@router.delete("/{block_id}", status_code=200)
async def delete_compute_block(
    block_id: UUID | None = None
):
    if not block_id:
        return HTTPException(
            status_code=422,
            detail="Compute Block id required."
        )

    try:
        delete_block(block_id)
    except Exception as e:
        logging.error(f"Error deleting compute block: {e}")
        raise handle_error(e)


@router.post("/edge", response_model=IDResponse)
def create_io_stream_and_update_io_cfg(
    data: EdgeDTO
):
    try:
        id = create_stream_and_update_target_cfg(
            data.source,
            data.sourceHandle,
            data.target,
            data.targetHandle
        )
        return IDResponse(id=id)
    except Exception as e:
        logging.error(f"Error creating an edge and configuring input: {e}")
        raise handle_error(e)


@router.post("/edge/delete", status_code=200)
def delete_stream(
    data: EdgeDTO
):
    try:
        delete_edge(
            data.source,
            data.sourceHandle,
            data.target,
            data.targetHandle
        )
    except Exception as e:
        logging.error(f"Error deleting an edge: {e}")
        raise handle_error(e)
