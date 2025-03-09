from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from utils.errors.error import handle_error
from services.workflow_service.schemas.compute_block import (
    ComputeBlockInformationRequest, ComputeBlockInformationResponse,
    CreateComputeBlockRequest, IDResponse,
    GetNodesByProjectResponse, NodeDTO, UpdateComputeBlockRequest,
    EdgeDTO
)
from services.user_service.middleware.authenticate_token import (
    authenticate_token,
)
from services.workflow_service.controllers.compute_block_controller import (
    request_cb_info, create_compute_block, get_compute_blocks_by_project,
    update_compute_block, delete_block, create_stream_and_update_target_cfg,
    get_block_dependencies_for_blocks, delete_edge
)

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
        raise handle_error(e)


@router.post("/", response_model=IDResponse)
async def create(
    data: CreateComputeBlockRequest,
    _: dict = Depends(authenticate_token)
):
    try:
        uuid = create_compute_block(
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
        return IDResponse(
            id=uuid
        )
    except Exception as e:
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

        block_uuids = [block.uuid for block in compute_blocks]
        dependencies = get_block_dependencies_for_blocks(block_uuids)

        return GetNodesByProjectResponse(
            blocks=[
                NodeDTO.from_compute_block(cb)
                for cb in compute_blocks
            ],
            edges=[EdgeDTO.from_block_dependencies(
                dp) for dp in dependencies
            ]
        )
    except Exception as e:
        raise handle_error(e)


@router.put("/", response_model=IDResponse)
async def update_cb(data: UpdateComputeBlockRequest):
    try:
        id = update_compute_block(
            id=data.id,
            custom_name=data.custom_name,
            selected_entrypoint=data.selected_entrypoint,
            x_pos=data.x_pos,
            y_pos=data.y_pos
        )
        return IDResponse(
            id=id
        )
    except Exception as e:
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
        raise handle_error(e)
