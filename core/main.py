from services.user_service.views import user as user_view
from services.workflow_service.views import workflow as workflow_view, \
    project as project_view, compute_block as compute_block_view
from utils.config.environment import ENV
from utils.database.connection import engine
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.exc import OperationalError
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=ENV.LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="scystream-core")


@app.on_event("startup")
async def test_db_conn():
    try:
        engine.connect()
    except OperationalError:
        logging.error("Connection to database failed.")
        raise RuntimeError("Shutdown, database connection failed.")


origins = ["*" if ENV.DEVELOPMENT else ENV.EXTERNAL_URL]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user_view.router)
app.include_router(workflow_view.router)
app.include_router(project_view.router)
app.include_router(compute_block_view.router)
