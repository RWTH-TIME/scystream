from fastapi import FastAPI

from services.user_service.views import user as user_view

app = FastAPI(title="scystream-core")

app.include_router(user_view.router)
