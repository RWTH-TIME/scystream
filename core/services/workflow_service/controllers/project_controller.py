import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from services.workflow_service.models.project import Project
from sqlalchemy.orm import Session
from utils.database.session_injector import get_database


def create_project(name: str, current_user_uuid: UUID) -> UUID:
    logging.debug(
        f"Creating project with name: {name} for user: {current_user_uuid}",
    )
    db: Session = next(get_database())
    project: Project = Project()

    project.uuid = uuid4()
    project.name = name
    project.created_at = datetime.now(timezone.utc)
    project.users = [current_user_uuid]

    db.add(project)
    db.commit()
    db.refresh(project)

    logging.info(f"Project {project.uuid} created successfully")
    return project.uuid


def read_project(project_uuid: UUID) -> Project:
    logging.debug(f"Reading project with UUID: {project_uuid}")
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        logging.error(f"Project {project_uuid} not found")
        raise HTTPException(status_code=404, detail="Project not found")

    return project


def rename_project(project_uuid: UUID, new_name: str) -> Project:
    logging.debug(f"Renaming project {project_uuid} to {new_name}.")
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        logging.error(f"Project {project_uuid} not found.")
        raise HTTPException(status_code=404, detail="Project not found")

    project.name = new_name

    db.commit()
    db.refresh(project)

    logging.info(f"Project {project_uuid} renamed successfully to {new_name}")
    return project


def add_user(project_uuid: UUID, user_uuid: UUID) -> None:
    logging.debug(f"Adding user {user_uuid} to project {project_uuid}.")
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        logging.error(f"Project {project_uuid} not found.")
        raise HTTPException(status_code=404, detail="Project not found")

    if user_uuid in project.users:
        logging.warning(
            f"User {user_uuid} is already part of project {project_uuid}.",
        )
        raise HTTPException(
            status_code=404,
            detail="User is already added to the project",
        )

    project.users.append(user_uuid)

    db.commit()
    logging.info(f"User {user_uuid} added to project {project_uuid}.")


def delete_user(project_uuid: UUID, user_uuid: UUID) -> None:
    logging.debug(f"Removing user {user_uuid} from {project_uuid}")
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        logging.error(f"Project {project_uuid} not found")
        raise HTTPException(status_code=404, detail="Project not found")

    if user_uuid not in project.users:
        logging.warning(
            f"User {user_uuid} is not part of project {project_uuid}",
        )
        raise HTTPException(
            status_code=404,
            detail="User is not part of the project",
        )

    project.users.remove(user_uuid)

    db.commit()
    logging.info(f"User {user_uuid} removed from project {project_uuid}")


def delete_project(project_uuid: UUID) -> None:
    logging.debug(f"Deleting project with UUID: {project_uuid}")
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        logging.error(f"Project {project_uuid} not found")
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    logging.info(f"Project {project_uuid} deleted successfully")


def read_all_projects() -> list[Project]:
    db: Session = next(get_database())

    projects = db.query(Project).all()

    return projects


def read_projects_by_user_uuid(user_uuid: UUID) -> list[Project]:
    logging.debug(f"Fetching projects for user UUID: {user_uuid}")
    db: Session = next(get_database())

    projects = (
        db.query(Project)
        .filter(Project.user_uuids.contains([user_uuid]))
        .all()
    )

    if not projects:
        logging.error(f"No projects found for user {user_uuid}")
        raise HTTPException(
            status_code=404,
            detail="No projects found for user",
        )

    logging.info(f"Retrieved {len(projects)} projects for user {user_uuid}")
    return projects
