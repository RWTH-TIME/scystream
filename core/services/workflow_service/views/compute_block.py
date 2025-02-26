from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from utils.errors.error import handle_error
from services.workflow_service.schemas.compute_block import (
    ComputeBlockInformationRequest, ComputeBlockInformationResponse,
    CreateComputeBlockRequest, CreateComputeBlockResponse,
    GetNodesByProjectResponse, NodeDTO
)
from services.user_service.middleware.authenticate_token import (
    authenticate_token,
)
from services.workflow_service.controllers.compute_block_controller import (
    request_cb_info, create_compute_block, get_compute_blocks_by_project
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


@router.post("/", response_model=CreateComputeBlockResponse)
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
        return CreateComputeBlockResponse(
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
        return GetNodesByProjectResponse([
            NodeDTO.from_compute_block(cb)
            for cb in compute_blocks
        ])
    except Exception as e:
        raise handle_error(e)
