import logging

from airflow_client.client.exceptions import ApiException
from fastapi import HTTPException
from psycopg2 import Error as PostgresError
from psycopg2.errors import (
    ForeignKeyViolation,
    NotNullViolation,
    UniqueViolation,
)
from sqlalchemy import exc

"""
The handleError function is intented to be used in our views
Pass any Exception to the function and it will raise the.
"""


def handle_error(error: Exception) -> None:
    if isinstance(error, exc.IntegrityError):
        postgres_error: PostgresError = error.orig
        error_msg = postgres_error.pgerror

        # Constraint violations
        if isinstance(postgres_error, UniqueViolation) or isinstance(
            postgres_error,
            ForeignKeyViolation,
        ):
            raise HTTPException(409, detail=error_msg)
        if isinstance(postgres_error, NotNullViolation):
            raise HTTPException(422, detail=error_msg)
        raise HTTPException(
            409,
            detail=f"db integrity violated: {error_msg}",
        )
    if isinstance(error, ApiException):
        logging.error(
            f"API Exception ocurred when contacting Airflow: {error}",
        )
        raise HTTPException(
            500,
            detail="While talking to Airflow an error occured.",
        )
    if isinstance(error, HTTPException):
        # HTTPExceptions are already in the right format
        raise error
    # TODO: Can we propagate more error details to the user
    logging.error(f"Could not handle exception {error}")
    raise HTTPException(500, detail="internal server error")
