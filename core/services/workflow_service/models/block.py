from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String,  ForeignKey, Table, Integer, Float
from sqlalchemy.orm import relationship, foreign

import uuid

from utils.database.connection import Base
from services.workflow_service.models.entrypoint import Entrypoint  # noqa: F401, E501


# Association table for block dependencies
block_dependencies = Table(
    "block_dependencies", Base.metadata,
    Column("upstream_block_uuid", UUID(as_uuid=True),
           ForeignKey(
               "blocks.uuid", ondelete="CASCADE", name="fk_upstream_block"),
           primary_key=True),
    Column("downstream_block_uuid", UUID(as_uuid=True),
           ForeignKey(
               "blocks.uuid", ondelete="CASCADE", name="fk_downstream_block"),
           primary_key=True)
)


class Block(Base):
    __tablename__ = "blocks"

    uuid = Column(UUID(as_uuid=True), primary_key=True,
                  default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    project_uuid = Column(UUID(as_uuid=True),
                          ForeignKey("projects.uuid",
                                     ondelete="CASCADE",
                                     name="fk_project_uuid"))

    # airflow-Task specific columns
    priority_weight = Column(Integer, nullable=True)
    retries = Column(Integer, default=0)
    # delay in seconds before rerun of pipeline after fail
    retry_delay = Column(Integer, default=300)
    # schedule_interval = Column(String, nullable=True)

    # sdk specific columns, set by user
    custom_name = Column(String(100), nullable=False)
    description = Column(String(100), nullable=True)
    author = Column(String(100), nullable=True)
    docker_image = Column(String(150), nullable=False)
    repo_url = Column(String(100), nullable=False)

    selected_entrypoint_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "entrypoints.uuid",
            ondelete="SET NULL",
            name="fk_selected_entrypoint_uuid"
        ),
        nullable=True
    )

    # position
    x_pos = Column(Float, nullable=True)
    y_pos = Column(Float, nullable=True)

    project = relationship("Project", back_populates="blocks")

    entrypoints = relationship(
        "Entrypoint",
        back_populates="block",
        cascade="all, delete-orphan",
        foreign_keys=[Entrypoint.block_uuid]
    )

    selected_entrypoint = relationship(
        "Entrypoint",
        foreign_keys=[selected_entrypoint_uuid],
        uselist=False
    )

    upstream_blocks = relationship(
        "Block",
        secondary="block_dependencies",
        primaryjoin=foreign(uuid)
        == block_dependencies.c.downstream_block_uuid,
        secondaryjoin=foreign(uuid)
        == block_dependencies.c.upstream_block_uuid,
        back_populates="downstream_blocks"
    )

    downstream_blocks = relationship(
        "Block",
        secondary="block_dependencies",
        primaryjoin=foreign(uuid)
        == block_dependencies.c.upstream_block_uuid,
        secondaryjoin=foreign(uuid)
        == block_dependencies.c.downstream_block_uuid,
        back_populates="upstream_blocks"
    )
