import bcrypt
import jwt

from typing import Tuple
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta

from src.utils.config.environment import ENV

from src.utils.database.session_injector import get_database
from src.services.user_service.models.user import User


"""
The login function takes email, and password.
Returns a tuple of access_token and refresh_token
"""
def login(email: str, password: str) -> Tuple[str, str]:
    db: Session = next(get_database())
    user: User = db.query(User).filter_by(email=email).first()

    if not user:
        raise HTTPException(404, detail="User not found")
    
    if bcrypt.checkpw(password.encode("utf-8"), user.password):
        # create tokens
        now: datetime = datetime.now(tz=timezone.utc)

        access_token = jwt.encode({
                    "email": user.email,
                    "iat": now,
                    "exp": now + timedelta(minutes=ENV.JWT_ACCESS_TOKEN_EXPIRE_MIN)
                },
                ENV.JWT_SECRET,
                algorithm=ENV.JWT_ALGORITHM
            )
        
        refresh_token = jwt.encode({
                    "iat": now,
                    "exp": now + timedelta(days=ENV.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
                },
                ENV.JWT_SECRET,
                algorithm=ENV.JWT_ALGORITHM
        )
    else:
        raise HTTPException(401, detail="wrong password")

    return (access_token, refresh_token)

