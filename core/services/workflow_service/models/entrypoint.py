from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import relationship
from utils.database.connection import Base
import uuid


class Entrypoint(Base):
    __tablename__ = "entrypoints"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    envs = Column(JSON, nullable=False)

    block = relationship("Block", back_populates="selected_entrypoint")

    input_outputs = relationship("InputOutput", back_populates="entrypoint",
                                 cascade="all, delete-orphan")
