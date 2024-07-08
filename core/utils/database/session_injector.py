from sqlalchemy.orm import Session

from utils.database.connection import SessionLocal


def get_database() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
