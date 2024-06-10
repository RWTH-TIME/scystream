from fastapi import FastAPI
from src.utils.database.connection import Base, engine

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="scystream-core", lifespan=lifespan)
