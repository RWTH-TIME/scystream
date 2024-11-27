from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship

import uuid

from utils.database.connection import Base
import enum

from .entrypoint import Entrypoint


class InputOutputType(enum.Enum):
    INPUT = "Input"
    OUTPUT = "Output"


class InputOutput(Base):
    __tablename__ = "inputoutputs"

    uuid = Column(UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4)
    type = Column(Enum(InputOutputType), nullable=False)
    name = Column(String(100), nullable=True)
    data_type = Column(String)  # ask Paul again if this should be enum?
    description = Column(String(500), nullable=True)
    config = Column(JSON, nullable=False)

    entrypoint_uuid = Column(UUID(as_uuid=True),
                             ForeignKey('blocks.uuid', ondelete="CASCADE"))

    entrypoints = relationship(Entrypoint, back_populates="entrypoints",
                               cascade="all, delete-orphan")
