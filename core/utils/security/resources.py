from fastapi import HTTPException, Depends, Path
from sqlalchemy.orm import Session
from uuid import UUID

from utils.database.session_injector import get_database
from utils.security.token import User, get_user

from services.workflow_service.models import (
    Project,
)


def get_project(
    project_uuid: UUID = Path(...),
    user: User = Depends(get_user),
    db: Session = Depends(get_database)
):
    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()
    if not project:
        raise HTTPException(404, f"Project {project_uuid} not found")

    print(project.users)
    # authorize access
    if user.uuid not in (project.users or []):
        raise HTTPException(403, "Access to resource denied")

    return project
