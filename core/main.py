from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.user_service.views import user as user_view

app = FastAPI(title="scystream-core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_view.router)
