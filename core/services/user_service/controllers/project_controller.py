from uuid import UUID, uuid4
from sqlalchemy.orm import Session
import datetime
from typing import List

from utils.database.session_injector import get_database
from services.user_service.models.project import Project
from services.user_service.models.user import User


# Still missing any field validation (empty name, uuid is not UUID..)
# Does current uuid need to be extracted from the token?
def create_project(name: str,  current_user_uuid: UUID) -> UUID:
    db: Session = next(get_database())
    project: Project = Project()

    project.uuid = uuid4()
    project.name = name
    project.created_at = datetime.utcnow()
    current_user = db.query(User).filter_by(uuid=current_user_uuid).first()
    if not current_user:
        raise ValueError("User not found")
    # add relation with blocks?

    db.add(project)
    db.commit()
    db.refresh(project)

    return project.uuid


def read_project(project_uuid: UUID) -> Project:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).first()

    if not project:
        raise ValueError("Project not found")

    return project


# split into rename, add users, add blocks, delete users, delete blocks?
def update_project(project_uuid: UUID, new_name: str) -> Project:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).first()

    if not project:
        raise ValueError("Project not found")

    project.name = new_name
    # add relation with users? adding current user to the project?
    # add relation with blocks

    db.commit()
    db.refresh(project)

    return project


def delete_project(project_uuid: UUID) -> None:
    db: Session = next(get_database())

    # Fetch the project by its UUID
    project = db.query(Project).filter_by(uuid=project_uuid).first()

    if not project:
        raise ValueError("Project not found")

    # Delete the project
    db.delete(project)
    db.commit()

    return None


def read_all_projects() -> List[Project]:
    db: Session = next(get_database())

    projects = db.query(Project).all()

    return projects


def read_projects_by_user_uuid(user_uuid: UUID) -> List[Project]:
    db: Session = next(get_database())

    # Fetch the user by UUID
    user = db.query(User).filter_by(uuid=user_uuid).first()

    if not user:
        raise ValueError("User not found")

    # Fetch all projects related to this user
    projects = user.projects
    # This assumes the relationship is defined correctly

    return projects
