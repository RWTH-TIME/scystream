from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String,  ForeignKey, Table, Integer, Float
from sqlalchemy.orm import relationship

import uuid

from utils.database.connection import Base


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

    # airflow-Task specific columns
    priority_weight = Column(Integer, nullable=True)
    retries = Column(Integer, default=0)
    retry_delay = Column(Integer, default=300)  # Delay in seconds
    # schedule_interval = Column(String, nullable=True)

    # sdk specific columns, set by user
    custom_name = Column(String(100), nullable=False)
    description = Column(String(100), nullable=True)  # nullable false instead?
    author = Column(String(100), nullable=True)
    docker_image = Column(String(150), nullable=False)
    repo_url = Column(String(100), nullable=False)
    selected_entrypoint = Column(
        UUID(as_uuid=True), ForeignKey('entrypoints.uuid', ondelete="CASCADE"))

    # position
    x_pos = Column(Float, nullable=True)
    y_pos = Column(Float, nullable=True)

    project = relationship("Project", back_populates="blocks")
    # there could be problems between this relationship and the selected 
    # entrypoint relationship
    entrypoints = relationship("Entrypoint", back_populates="blocks")

    # think about logic again
    upstream_blocks = relationship(
        "Block",
        secondary=block_dependencies,
        primaryjoin=uuid == block_dependencies.c.downstream_block_uuid,
        secondaryjoin=uuid == block_dependencies.c.upstream_block_uuid,
        back_populates="downstream_blocks"
    )
    downstream_blocks = relationship(
        "Block",
        secondary=block_dependencies,
        primaryjoin=uuid == block_dependencies.c.upstream_block_uuid,
        secondaryjoin=uuid == block_dependencies.c.downstream_block_uuid,
        back_populates="upstream_blocks"
    )
