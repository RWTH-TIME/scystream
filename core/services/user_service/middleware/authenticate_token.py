from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from utils.helper.jwt import verify_token


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header:
            token = auth_header.split(" ")[1]
        
        if not token:
            raise HTTPException(
                status_code=401, 
                detail="Access token is missing or invalid"
                )

        payload = verify_token(token)
        request.state.user = payload  # Attach user info to the request state
        
        response = await call_next(request)
        return response
