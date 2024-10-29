from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey
from utils.database.connection import Base


class UserProject(Base):
    __tablename__ = 'user_project'

    user_uuid = Column(UUID(as_uuid=True),
                       ForeignKey('users.uuid', ondelete="CASCADE"),
                       primary_key=True)
    project_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('projects.uuid', ondelete="CASCADE"),
                          primary_key=True)
