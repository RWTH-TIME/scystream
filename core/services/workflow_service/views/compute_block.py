from fastapi import APIRouter, Depends

from utils.errors.error import handle_error
from services.workflow_service.schemas.compute_block import (
    ComputeBlockInformationRequest, ComputeBlockInformationResponse, CreateComputeBlockRequest,
    CreateComputeBlockResponse
)
from services.user_service.middleware.authenticate_token import (
    authenticate_token,
)
from services.workflow_service.controllers.compute_block_controller import (
    request_cb_info, create_compute_block
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
        return ComputeBlockInformationResponse.from_compute_block(cb)
    except Exception as e:
        raise handle_error(e)


@router.post("/", response_model=CreateComputeBlockResponse)
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
        return CreateComputeBlockResponse.from_compute_block(cb)
    except Exception as e:
        raise handle_error(e)
