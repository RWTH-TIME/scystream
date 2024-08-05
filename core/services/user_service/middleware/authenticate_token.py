# middleware/authenticate_token.py
from fastapi import Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from utils.helper.jwt import create_token, verify_token

from typing import Callable
import os

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next: Callable):
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1]
        else:
            token = None

        if not token:
            raise HTTPException(status_code=401, detail="Access token is missing or invalid")

        payload = verify_token(token)
        request.state.user = payload  # Attach user info to the request state
        
        response = await call_next(request)
        return response
