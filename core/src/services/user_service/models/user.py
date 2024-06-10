from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String

import uuid

from src.utils.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String,)
    password = Column(String,)
