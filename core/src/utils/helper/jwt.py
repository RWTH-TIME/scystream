import jwt
from src.utils.config.environment import ENV


"""
wrapper function for jwt.encode creating jwt tokens with our secret and algorithm
"""
def create_token(payload: dict) -> str:
    return jwt.encode(
                payload,
                ENV.JWT_SECRET,
                algorithm=ENV.JWT_ALGORITHM
            )
