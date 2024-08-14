import bcrypt

from typing import Tuple
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from utils.config.environment import ENV
from utils.helper.jwt import create_token, verify_token

from utils.database.session_injector import get_database
from services.user_service.models.user import User


def login(email: str, password: str) -> Tuple[str, str]:
    """
    The login function takes email, and password.
    Returns a tuple of access_token and refresh_token
    """

    db: Session = next(get_database())
    user: User = db.query(User).filter_by(email=email).first()

    if not user:
        raise HTTPException(404, detail="User not found")

    if not bcrypt.checkpw(password.encode("utf-8"), user.password):
        raise HTTPException(401, detail="wrong password")

    # create tokens
    now: datetime = datetime.now(tz=timezone.utc)

    access_token = create_token({
        "email": user.email,
        "iat": now,
        "exp": now + timedelta(minutes=ENV.JWT_ACCESS_TOKEN_EXPIRE_MIN)
    })

    refresh_token = create_token({
        "iat": now,
        "exp": now + timedelta(days=ENV.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    })

    return access_token, refresh_token


def refresh_access_token(access_token: str, refresh_token: str):
    """
    The refresh function takes a refresh token
    and generates a new access_token.
    Returns a tuple of access_token and refresh_token
    """
    payload_refresh = verify_token(refresh_token)
    if not payload_refresh:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # using old access token to get user email
    payload_access = verify_token(access_token)

    email: str = payload_access.get("email")

    db: Session = next(get_database())
    user: User = db.query(User).filter_by(email=email).first()

    if not user:
        raise HTTPException(403)

    # refresh tokens
    now = datetime.now(tz=timezone.utc)
    access_token = create_token({
        "email": user.email,
        "iat": now,
        "exp": now + timedelta(minutes=ENV.JWT_ACCESS_TOKEN_EXPIRE_MIN)
    })

    return access_token, refresh_token
