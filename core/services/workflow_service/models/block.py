from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String,  ForeignKey, Table, Enum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON

import uuid

from utils.database.connection import Base
import enum


# Define operator types
class OperatorType(enum.Enum):
    POSTGRES = "PostgresOperator"
    PYTHON = "PythonOperator"
    MYSQL = "MySQLOperator"


# Association table for block dependencies
block_dependencies = Table(
    'block_dependencies', Base.metadata,
    Column('upstream_block_uuid', UUID(as_uuid=True),
           ForeignKey('blocks.uuid', ondelete="CASCADE"), primary_key=True),
    Column('downstream_block_uuid', UUID(as_uuid=True),
           ForeignKey('blocks.uuid', ondelete="CASCADE"), primary_key=True)
)


class Block(Base):
    __tablename__ = "blocks"

    uuid = Column(UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    project_uuid = Column(UUID(as_uuid=True), ForeignKey('projects.uuid',
                                                         ondelete="CASCADE"))
    # Task specific columns
    block_type = Column(Enum(OperatorType), nullable=False)
    # This can contain a lot of optional parameters
    parameters = Column(JSON, nullable=True)
    priority_weight = Column(Integer, nullable=True)
    retries = Column(Integer, default=0)
    retry_delay = Column(Integer, default=300)  # Delay in seconds
    schedule_interval = Column(String, nullable=True)
    # in case some enviroment setup is needed (API key, database connection)
    environment = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="blocks")

    upstream_blocks = relationship(
        "Block",
        secondary=block_dependencies,
        primaryjoin=uuid == block_dependencies.c.downstream_block_uuid,
        secondaryjoin=uuid == block_dependencies.c.upstream_block_uuid,
        backref="downstream_blocks"
    )
