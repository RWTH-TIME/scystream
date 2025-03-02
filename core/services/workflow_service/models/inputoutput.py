from utils.database.connection import Base
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
import enum


# Enum for Input/Output type
class InputOutputType(enum.Enum):
    INPUT = "Input"
    OUTPUT = "Output"


class DataType(enum.Enum):
    DBINPUT = "db_table"
    FILE = "file"


class InputOutput(Base):
    __tablename__ = "inputoutputs"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(InputOutputType), nullable=False)
    name = Column(String(100), nullable=True)
    data_type = Column(Enum(DataType), nullable=False)
    description = Column(String(500), nullable=True)
    config = Column(JSON, nullable=False)

    entrypoint_uuid = Column(UUID(as_uuid=True), ForeignKey(
        'entrypoints.uuid', ondelete="CASCADE"), nullable=False)
    entrypoint = relationship("Entrypoint", back_populates="input_outputs")
