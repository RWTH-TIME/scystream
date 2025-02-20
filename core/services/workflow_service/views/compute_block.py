from fastapi import APIRouter, Depends

from utils.errors.error import handle_error
from services.workflow_service.schemas.compute_block import (
    ComputeBlockInformationRequest, ComputeBlockInformationResponse
)
from services.user_service.middleware.authenticate_token import (
    authenticate_token,
)
from services.workflow_service.controllers.compute_block_controller import (
    request_cb_info
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
