from sqlalchemy import Column, String, ForeignKey
from utils.database.connection import Base


class UserProject(Base):
    __tablename__ = 'user_project'

    user_uuid = Column(String(36), ForeignKey('users.uuid'),
                       primary_key=True)
    project_uuid = Column(String(36), ForeignKey('projects.uuid'),
                          primary_key=True)
