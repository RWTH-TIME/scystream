from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from typing import List

from utils.database.session_injector import get_database
from services.workflow_service.models.project import Project
from services.user_service.models.user import User
from services.workflow_service.models.block import Block


def create_project(name: str, current_user_uuid: UUID) -> UUID:
    db: Session = next(get_database())
    project: Project = Project()

    project.uuid = uuid4()
    project.name = name
    project.created_at = datetime.now(timezone.utc)

    current_user = (
        db.query(User).filter_by(uuid=current_user_uuid).one_or_none()
    )

    if not current_user:
        raise HTTPException(404, detail="User not found")

    # TODO: add relation with blocks

    db.add(project)
    db.commit()
    db.refresh(project)

    return project.uuid


def read_project(project_uuid: UUID) -> Project:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


def rename_project(project_uuid: UUID, new_name: str) -> Project:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.name = new_name

    db.commit()
    db.refresh(project)

    return project


def add_user(project_uuid: UUID, user_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user in project.users:
        raise HTTPException(
            status_code=404, detail="User is already added to the project"
        )

    project.users.append(user)

    db.commit()

    return None


def delete_user(project_uuid: UUID, user_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user not in project.users:
        raise HTTPException(
            status_code=404, detail="User is not part of the project"
        )

    project.users.remove(user)

    db.commit()

    return None


def delete_project(project_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return None


def read_all_projects() -> List[Project]:
    db: Session = next(get_database())

    projects = db.query(Project).all()

    return projects


def read_projects_by_user_uuid(user_uuid: UUID) -> List[Project]:
    db: Session = next(get_database())

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    projects = user.projects

    return projects
