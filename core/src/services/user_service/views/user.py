import src.services.user_service.controllers.auth_controller as auth_controller
from fastapi import APIRouter
from src.utils.errors.error import handle_error

from src.services.user_service.schemas.user import CreateUserResponse, \
    CreateUserRequest, LoginRequest, LoginResponse

import src.services.user_service.controllers.create_user \
    as create_user_controller

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/create", response_model=CreateUserResponse)
async def create_user(data: CreateUserRequest):
    try:
        userID = create_user_controller.createUser(data.email, data.password)
        return CreateUserResponse(uuid=userID)
    except Exception as e:
        raise handle_error(e)


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    try:
        access_token, refresh_token = auth_controller.login(
            data.email, data.password)
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except Exception as e:
        raise handle_error(e)
