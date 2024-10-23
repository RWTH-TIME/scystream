from fastapi import HTTPException, Request
from utils.helper.jwt import decode_token


def authenticate_token(request: Request):
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

    payload = decode_token(token)

    return payload
