import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from services.user_service.views import user as user_view
from services.workflow_service.views import compute_block as compute_block_view
from services.workflow_service.views import project as project_view
from services.workflow_service.views import workflow as workflow_view
from sqlalchemy.exc import OperationalError
from utils.config.environment import ENV
from utils.database.connection import engine
from utils.security.token import authenticate_user, keycloak_openid

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=ENV.LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="scystream-core")


@asynccontextmanager
async def lifespan(_: FastAPI):
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


@app.get("/callback", include_in_schema=False)
async def callback(request: Request):
    keycode = request.query_params.get("code") or ""

    access_token = authenticate_user(keycode, request)

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    return Response(content=access_token, media_type="text/plain")


@app.get("/login", response_class=RedirectResponse, include_in_schema=False)
async def login(request: Request):
    auth_url = keycloak_openid.auth_url(
        redirect_uri=str(request.url_for("callback")),
        scope="openid profile email",
    )

    return RedirectResponse(auth_url)
