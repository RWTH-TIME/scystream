from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from utils.database.session_injector import get_database
from services.workflow_service.models.project import Project
from services.user_service.models.user import User
from services.workflow_service.controllers.compute_block_controller import (
    create_compute_blocks_from_template
)
import services.workflow_service.controllers.workflow_controller as \
    workflow_controller


def create_project(db: Session, name: str, current_user_uuid: UUID) -> UUID:
    logging.debug(f"Creating project with name: {
        name} for user: {current_user_uuid}")
    project: Project = Project()

    project.uuid = uuid4()
    project.name = name
    project.created_at = datetime.now(timezone.utc)

    current_user = (
        db.query(User).filter_by(uuid=current_user_uuid).one_or_none()
    )

    if not current_user:
        logging.error(f"User {current_user_uuid} not found.")
        raise HTTPException(404, detail="User not found")

    db.add(project)

    logging.info(f"Project {project.uuid} created successfully")
    return project.uuid


def create_project_from_template(
        name: str,
        template_identifier: str,
        current_user_uuid: UUID
) -> UUID:
    """
    This method will handle the creation of project, blocks and edges as
    defined in the template.yaml
    """
    db: Session = next(get_database())

    template = workflow_controller.get_workflow_template_by_identifier(
        template_identifier
    )

    # TODO:
    # - Test if Template overwrites io configs correctly.
    # - Coordinates
    # - Create Edges
    # - Test!!
    try:
        with db.begin():
            project_id = create_project(db, name, current_user_uuid)
            create_compute_blocks_from_template(db, template, project_id)

    except Exception as e:
        logging.exception(f"Error creating project from template: {e}")
        raise e


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

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        logging.error(f"User {user_uuid} not found.")
        raise HTTPException(status_code=404, detail="User not found")

    if user in project.users:
        logging.warning(f"User {user_uuid} is already part of project {
            project_uuid}.")
        raise HTTPException(
            status_code=404, detail="User is already added to the project"
        )

    project.users.append(user)

    db.commit()
    logging.info(f"User {user_uuid} added to project {project_uuid}.")


def delete_user(project_uuid: UUID, user_uuid: UUID) -> None:
    logging.debug(f"Removing user {user_uuid} from {project_uuid}")
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        logging.error(f"Project {project_uuid} not found")
        raise HTTPException(status_code=404, detail="Project not found")

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        logging.error(f"User {user_uuid} not found")
        raise HTTPException(status_code=404, detail="User not found")

    if user not in project.users:
        logging.warning(
            f"User {user_uuid} is not part of project {project_uuid}")
        raise HTTPException(
            status_code=404, detail="User is not part of the project"
        )

    project.users.remove(user)

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

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        logging.error(f"User {user_uuid} not found")
        raise HTTPException(status_code=404, detail="User not found")

    projects = user.projects
    logging.info(f"Retrieved {len(projects)} projects for user {user_uuid}")
    return projects
