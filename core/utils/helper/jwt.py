import jwt
from utils.config.environment import ENV
from services.user_service.models.user import User
from datetime import datetime, timezone, timedelta


def create_refresh_token() -> str:
    now: datetime = datetime.now(tz=timezone.utc)

    return _create_token(
        {
            "iat": now,
            "exp": now + timedelta(days=ENV.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        }
    )


def create_access_token(user: User) -> str:
    now: datetime = datetime.now(tz=timezone.utc)

    return _create_token(
        {
            "email": str(user.email),
            "uuid": str(user.uuid),
            "iat": now,
            "exp": now + timedelta(minutes=ENV.JWT_ACCESS_TOKEN_EXPIRE_MIN),
        }
    )


def _create_token(payload: dict) -> str:
    """
    wrapper function for jwt.encode creating jwt tokens with our secret and
    algorithm
    """
    return jwt.encode(payload, ENV.JWT_SECRET, algorithm=ENV.JWT_ALGORITHM)


def verify_token(token: str) -> bool:
    """
    Wrapper function for jwt.decode, verifying JWT tokens with our secret and
    algorithm. Returns the payload.
    """
    payload = jwt.decode(token, ENV.JWT_SECRET, algorithms=ENV.JWT_ALGORITHM)

    if not payload:  # can also throw: jwt.ExpiredSignatureError,
        # might be neccessary to change into try - except
        raise jwt.InvalidSignatureError
    return True


def decode_token(token: str) -> dict:
    """
    Wrapper function for jwt.decode, verifying JWT tokens with our secret and
    algorithm. Returns the payload.
    """
    payload = jwt.decode(token, ENV.JWT_SECRET, algorithms=ENV.JWT_ALGORITHM)

    if not payload:  # can also throw: jwt.ExpiredSignatureError,
        # might be neccessary to change into try - except
        raise jwt.InvalidSignatureError

    return payload
