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


def verify_token(token: str) -> dict: 
    """
    wrapper function for jwt.decode, verifying jwt tokens with our secret and
    algorithm, returns the payload
    """
    payload= jwt.decode(
            token,
            ENV.JWT_SECRET,
            algorithm=ENV.JWT_ALGORITHM
        )
    if not payload:     #can also throw: jwt.ExpiredSignatureError, might be necessary to change into try - except
        raise jwt.InvalidSignatureError

    return payload