import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from utils.database.connection import Base

from services.workflow_service.models.block import Block


class Project(Base):
    __tablename__ = "projects"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # DAG-specific columns
    default_retries = Column(Integer, default=1)

    users = Column(ARRAY(UUID(as_uuid=True)))

    blocks = relationship(
        Block,
        back_populates="project",
        cascade="all, delete-orphan",
    )
