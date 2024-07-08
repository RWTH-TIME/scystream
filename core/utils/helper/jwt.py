import jwt
from utils.config.environment import ENV


def create_token(payload: dict) -> str:
    """
    wrapper function for jwt.encode creating jwt tokens with our secret and
    algorithm
    """
    return jwt.encode(
        payload,
        ENV.JWT_SECRET,
        algorithm=ENV.JWT_ALGORITHM
    )
