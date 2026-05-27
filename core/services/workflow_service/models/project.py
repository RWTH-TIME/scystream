import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from utils.database.connection import Base

from services.workflow_service.models.block import Block
from services.workflow_service.models.superset_import_status import (
    SupersetImportStatus,
)


class Project(Base):
    __tablename__ = "projects"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    default_retries = Column(Integer, default=1)

    users = Column(ARRAY(UUID(as_uuid=True)))

    owner_email = Column(String(255), nullable=True)
    superset_export_s3_key = Column(String(512), nullable=True)
    superset_dashboard_id = Column(Integer, nullable=True)
    superset_dashboard_url = Column(String(1024), nullable=True)
    superset_import_status = Column(
        String(32),
        nullable=False,
        default=SupersetImportStatus.NONE.value,
    )
    superset_import_error = Column(String(2048), nullable=True)

    blocks = relationship(
        Block,
        back_populates="project",
        cascade="all, delete-orphan",
    )
