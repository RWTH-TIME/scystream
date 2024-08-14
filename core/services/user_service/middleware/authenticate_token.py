from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from utils.helper.jwt import verify_token


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next):
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
        request.state.user = payload

        response = await call_next(request)
        return response
