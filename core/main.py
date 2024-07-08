from fastapi import FastAPI
from utils.database.connection import Base, engine

from contextlib import asynccontextmanager

from services.user_service.views import user as user_view

app = FastAPI(title="scystream-core")

app.include_router(user_view.router)
