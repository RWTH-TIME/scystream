import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from utils.database.connection import Base


class SharedWorkflowTemplate(Base):
    """A workflow template created from a project, visible to all users."""

    __tablename__ = "shared_workflow_templates"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False, default="")
    tags = Column(ARRAY(String(50)), nullable=False, default=list)
    # WorkflowTemplate without file_identifier (pipeline & blocks)
    definition = Column(JSON, nullable=False)
    # Superset visualization of the project at the time the template was
    # created, used as visualization template of projects created from it
    superset_template_s3_key = Column(String(512), nullable=True)
    source_project_uuid = Column(UUID(as_uuid=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_by_email = Column(String(255), nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
