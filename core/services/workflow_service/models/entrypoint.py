from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship

import uuid

from utils.database.connection import Base

from .block import Block


class Entrypoint(Base):
    __tablename__ = "entrypoints"

    uuid = Column(UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    envs = Column(JSON, nullable=False)
    block_uuid = Column(UUID(as_uuid=True),
                        ForeignKey('blocks.uuid', ondelete="CASCADE"))

    block = relationship(Block, back_populates="entrypoints")
    input_outputs = relationship("InputOutput", back_populates="entrypoints",
                                 cascade="all, delete-orphan")
