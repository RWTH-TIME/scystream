import jwt
from utils.config.environment import ENV
from fastapi import HTTPException


def create_token(payload: dict) -> str:
    """
    wrapper function for jwt.encode creating jwt tokens with our secret and
    algorithm
    """
    return jwt.encode(payload, ENV.JWT_SECRET, algorithm=ENV.JWT_ALGORITHM)


def verify_token(token: str) -> bool:
    """
    Wrapper function for jwt.decode, verifying JWT tokens with our secret and
    algorithm. Returns True if the token is not expired.
    """
    try:
        jwt.decode(
            token,
            ENV.JWT_SECRET,
            algorithms=ENV.JWT_ALGORITHM
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature")

    return True


def decode_token(token: str) -> dict:
    """
    Decodes a JWT token manually without verification, even if it is expired.
    Returns the payload as a dictionary.
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=ENV.JWT_ALGORITHM
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature")

    return payload
