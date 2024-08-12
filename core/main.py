from fastapi import FastAPI

from services.user_service.views import user as user_view

from services.user_service.middleware.authenticate_token \
    import JWTAuthMiddleware

from utils.config.environment import ENV

app = FastAPI(title="scystream-core")

app.add_middleware(JWTAuthMiddleware, secret_key=ENV.JWT_SECRET)
app.include_router(user_view.router)

