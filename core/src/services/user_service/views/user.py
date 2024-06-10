from fastapi import APIRouter, Depends, HTTPException
from src.utils.errors.error import handle_error

from src.services.user_service.schemas.user import CreateUserResponse, CreateUserRequest
import src.services.user_service.controllers.user as user_controller 


router = APIRouter(prefix="/user", tags=["user"])

@router.post("/create", response_model=CreateUserResponse)
async def createUser(data: CreateUserRequest):
    try:
        userID = user_controller.createUser(data.email, data.password)
    except Exception as e:
        error = handle_error(e)
    
    return CreateUserResponse(uuid=userID)
