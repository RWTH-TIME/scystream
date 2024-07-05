from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.utils.helper.validators import validate_email, validate_password


class EmailValidatorMixin(BaseModel):
    @field_validator("email", check_fields=False)
    @classmethod
    def validate_email(_, value):
        return validate_email(value)


class CreateUserRequest(EmailValidatorMixin):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(_, value):
        return validate_password(value)


class CreateUserResponse(BaseModel):
    uuid: UUID


class LoginRequest(EmailValidatorMixin):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
