from fastapi import FastAPI
from utils.database.connection import Base, engine

from contextlib import asynccontextmanager

from services.user_service.views import user as user_view


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="scystream-core", lifespan=lifespan)

app.include_router(user_view.router)
