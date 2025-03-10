import bcrypt

from typing import Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session

from utils.helper.jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
)

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
    access_token = create_access_token(user)
    refresh_token = create_refresh_token()

    return access_token, refresh_token


def refresh_access_token(old_access_token: str, refresh_token: str):
    """
    The refresh function takes a refresh token
    and generates a new access_token.
    Returns a tuple of access_token and refresh_token
    """

    if not verify_token(refresh_token):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # using old access token to get user email
    payload_old_access_token = decode_token(old_access_token)

    email: str = payload_old_access_token.get("email")

    db: Session = next(get_database())
    user: User = db.query(User).filter_by(email=email).first()

    if not user:
        raise HTTPException(403)

    # refresh tokens
    new_access_token = create_access_token(user)

    return new_access_token, refresh_token
