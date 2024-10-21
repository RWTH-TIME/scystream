from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, LargeBinary

import uuid

from utils.database.connection import Base


class Test(Base):
    __tablename__ = "test"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary, nullable=False)
