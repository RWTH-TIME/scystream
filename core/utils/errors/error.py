from sqlalchemy import exc
from fastapi import HTTPException
from psycopg2 import Error as PostgresError
from psycopg2.errors import (
    UniqueViolation,
    ForeignKeyViolation,
    NotNullViolation,
)
import logging

"""
The handleError function is intented to be used in our views
Pass any Exception to the function and it will raise the.
"""


def handle_error(error: Exception) -> None:
    if isinstance(error, exc.IntegrityError):
        postgres_error: PostgresError = error.orig
        error_msg = postgres_error.pgerror

        # Constraint violations
        if isinstance(postgres_error, UniqueViolation):
            raise HTTPException(409, detail=error_msg)
        elif isinstance(postgres_error, ForeignKeyViolation):
            raise HTTPException(409, detail=error_msg)
        elif isinstance(postgres_error, NotNullViolation):
            raise HTTPException(422, detail=error_msg)
        else:
            raise HTTPException(
                409, detail=f"db integrity violated: {error_msg}"
            )
    elif isinstance(error, HTTPException):
        # HTTPExceptions are already in the right format
        raise error
    else:
        # TODO: Can we propagate more error details to the user
        logging.error(f"Could not handle exception {error}")
        raise HTTPException(500, detail="internal server error")
