from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

import uuid

from datetime import datetime
from utils.database.connection import Base
from .block import Block


class Project(Base):
    __tablename__ = "projects"

    uuid = Column(UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", secondary="user_project",
                         back_populates="projects")

    blocks = relationship(Block, back_populates="project",
                          cascade="all, delete-orphan")
