from fastapi import FastAPI

from services.user_service.views import user as user_view

from services.user_service.middleware.authenticate_token import JWTAuthMiddleware
import os

app = FastAPI(title="scystream-core")

app.add_middleware(JWTAuthMiddleware, secret_key=os.getenv('ACCESS_TOKEN_SECRET'))

app.include_router(user_view.router)
