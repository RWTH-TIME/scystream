from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.orm import relationship

import uuid

from datetime import datetime
from utils.database.connection import Base


class Project(Base):
    __tablename__ = "projects"

    uuid = Column(UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # DAG-specific columns
    schedule_interval = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    catchup = Column(Boolean, default=False)
    concurrency = Column(Integer, nullable=True, default=1)
    default_retries = Column(Integer, default=1)
    dag_timeout = Column(Integer, nullable=True) 

    users = relationship("User", secondary="user_project",
                         back_populates="projects")

    blocks = relationship("Block", back_populates="project",
                          cascade="all, delete-orphan")
