from fastapi import APIRouter
from utils.errors.error import handle_error

from services.user_service.schemas.user import CreateUserResponse, \
    CreateUserRequest, LoginRequest, LoginResponse, \
    RefreshAccessResponse, RefreshAccessRequest

import services.user_service.controllers.auth_controller as auth_controller

import services.user_service.controllers.create_user \
    as create_user_controller

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/create", response_model=CreateUserResponse)
async def create_user(data: CreateUserRequest):
    try:
        userID = create_user_controller.create_user(data.email, data.password)
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


@router.post("/refresh", response_model=RefreshAccessResponse)
async def refresh_access(data: RefreshAccessRequest):
    try:
        access_token, refresh_token = \
            auth_controller.refresh_access_token(
                data.refresh_token
            )

        return RefreshAccessResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except Exception as e:
        raise handle_error(e)
