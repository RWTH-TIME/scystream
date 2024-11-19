from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, LargeBinary
from sqlalchemy.orm import relationship

import uuid

from utils.database.connection import Base
from services.workflow_service.models.user_project import UserProject
from services.workflow_service.models.project import Project


class User(Base):
    __tablename__ = "users"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary, nullable=False)

    projects = relationship(Project, secondary=UserProject.__tablename__,
                            back_populates="users")
