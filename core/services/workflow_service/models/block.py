from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String,  ForeignKey
from sqlalchemy.orm import relationship

import uuid

from utils.database.connection import Base


class Block(Base):
    __tablename__ = "blocks"

    uuid = Column(UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    project_uuid = Column(UUID(as_uuid=True), ForeignKey('projects.uuid',
                                                         ondelete="CASCADE"))

    project = relationship("Project", back_populates="blocks")
