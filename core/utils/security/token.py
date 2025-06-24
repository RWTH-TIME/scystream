from uuid import UUID as UUID4

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError
from pydantic import BaseModel
from utils.config.environment import ENV

bearer_scheme = HTTPBearer()

keycloak_openid = KeycloakOpenID(
    server_url=ENV.KEYCLOAK_SERVER_URL,
    realm_name=ENV.KEYCLOAK_REALM,
    client_id=ENV.KEYCLOAK_CLIENT_ID,
    client_secret_key=ENV.KEYCLOAK_CLIENT_SECRET,
)


class User(BaseModel):
    uuid: UUID4

    username: str

    email: str | None = None
    email_verified: bool = False

    fullname: str | None = None


def verify(token: str) -> User:
    try:
        user_info = keycloak_openid.userinfo(token)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        return User(
            uuid=user_info["sub"],
            username=user_info["preferred_username"],
            email=user_info.get("email"),
            email_verified=user_info.get("email_verified") or False,
            fullname=user_info.get("name"),
        )
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_user_from_token(
    token: str = Query(...),
) -> User:
    user_info = verify(token)

    if not user_info.email_verified:
        raise HTTPException(403, detail="Verify email first")

    return user_info


def get_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    token = credentials.credentials

    user_info = verify(token)

    if not user_info.email_verified:
        raise HTTPException(403, detail="Verify email first")

    return user_info


def authenticate_user(keycode: str, request: Request) -> str:
    try:
        token = keycloak_openid.token(
            grant_type="authorization_code",
            code=keycode,
            redirect_uri=str(request.url_for("callback")),
            scope="openid profile email",
        )
        return token["access_token"]
    except KeycloakAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Login",
        ) from exc
    except KeycloakPostError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Grant",
        ) from exc
