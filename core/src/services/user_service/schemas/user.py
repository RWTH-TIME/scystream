from uuid import UUID

from pydantic import BaseModel, Field, validator

from src.utils.helper.validators import validate_email, validate_password

class CreateUserRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)

    @validator("email")
    @classmethod
    def validate_email(_, value):
        return validate_email(value)

    @validator("password")
    @classmethod
    def validate_password(_, value):
        return validate_password(value)

class CreateUserResponse(BaseModel):
    uuid: UUID
