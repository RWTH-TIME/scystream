from fastapi import HTTPException
from utils.helper.jwt import verify_token
from services.user_service.schemas.user import RefreshAccessRequest


def authenticate_token(request: RefreshAccessRequest):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is missing"
        )

    parts = auth_header.split(" ")

    # Ensure there are exactly two parts
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(
            status_code=401,
            detail="Authorization header format is invalid"
        )

    token = parts[1]

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Access token is missing or invalid"
        )

    payload = verify_token(token)

    return payload
