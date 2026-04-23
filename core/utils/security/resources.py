from sqlalchemy import any_
from fastapi import HTTPException, Depends, Path
from sqlalchemy.orm import Session
from uuid import UUID

from utils.database.session_injector import get_database
from utils.security.token import User, get_user

from services.workflow_service.models import (
    Project,
    Entrypoint,
    Block,
    InputOutput,
    InputOutputType,
)


def get_project(
    project_uuid: UUID = Path(...),
    user: User = Depends(get_user),
    db: Session = Depends(get_database)
):
    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()
    if not project:
        raise HTTPException(404, f"Project {project_uuid} not found")

    # authorize access
    if user.uuid not in (project.users or []):
        raise HTTPException(403, "Access to resource denied")

    return project


def get_entrypoint(
    entrypoint_uuid: UUID = Path(...),
    user: User = Depends(get_user),
    db: Session = Depends(get_database)
):
    # Query Entrypoint while joining Block and Project
    entrypoint = (
        db.query(Entrypoint)
        .join(Block, Block.selected_entrypoint_uuid == Entrypoint.uuid)
        .join(Project, Project.uuid == Block.project_uuid)
        .filter(
            Entrypoint.uuid == entrypoint_uuid,
            user.uuid == any_(Project.users)
        )
        .one_or_none()
    )

    if not entrypoint:
        raise HTTPException(404, f"Entrypoint {entrypoint_uuid} not found")

    return entrypoint


def get_ios_by_entrypoint_uuid(
    io_type: InputOutputType,
    entrypoint_uuid: UUID = Path(...),
    user: User = Depends(get_user),
    db: Session = Depends(get_database),
):
    ios = (
        db.query(InputOutput)
        .join(Entrypoint, InputOutput.entrypoint_uuid == Entrypoint.uuid)
        .join(Block, Block.selected_entrypoint_uuid == Entrypoint.uuid)
        .join(Project, Project.uuid == Block.project_uuid)
        .filter(
            InputOutput.entrypoint_uuid == entrypoint_uuid,
            user.uuid == any_(Project.users)
        )
        .all()
    )

    if not ios:
        return []

    return ios
