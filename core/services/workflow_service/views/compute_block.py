from fastapi import APIRouter, Depends

from utils.errors.error import handle_error
from services.workflow_service.schemas.compute_block import (
    CreateComputeBlockResponse, CreateComputeBlockRequest
)
from services.user_service.middleware.authenticate_token import (
    authenticate_token,
)
from services.workflow_service.controllers.compute_block_controller import (
    create_compute_block
)

router = APIRouter(prefix="/compute_block", tags=["compute_block"])


@router.post("/", response_model=CreateComputeBlockResponse)
async def create_cb(
    data: CreateComputeBlockRequest,
    _: dict = Depends(authenticate_token)
):
    try:
        create_compute_block(data.compute_block_title, data.cbc_url)
    except Exception as e:
        raise handle_error(e)
