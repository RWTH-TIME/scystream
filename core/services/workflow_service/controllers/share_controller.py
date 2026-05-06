from services.workflow_service.controllers import (
    project_controller,
    template_controller,
)
from services.workflow_service.models.project import Project
from utils.config.environment import ENV
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from sqlalchemy.orm import Session
from sqlalchemy import update
from fastapi import HTTPException

from uuid import UUID


serializer = URLSafeTimedSerializer(ENV.INVITE_SECRET_KEY)


def _make_token(project_uuid: UUID) -> str:
    return serializer.dumps(str(project_uuid), salt=ENV.INVITE_SALT)


def _read_token(token: str) -> UUID:
    try:
        project_uuid_str = serializer.loads(
            token,
            salt=ENV.INVITE_SALT,
            max_age=ENV.INVITE_MAX_AGE_SECONDS,
        )
        return UUID(project_uuid_str)
    except SignatureExpired:
        raise HTTPException(status_code=410, detail="Invite link expired.")
    except BadSignature:
        raise HTTPException(status_code=400, detail="Invalid invite link.")


def generate_project_token(
    db: Session, project_uuid: UUID, user_id: UUID
) -> str:
    """
    Returns a token tied to the project that can be used to build the invite
    link
    """

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if user_id not in (project.users or []):
        raise HTTPException(
            status_code=403, detail="You are not a member of this project."
        )

    token = _make_token(project_uuid)

    return token


def accept_invite(
    db: Session,
    token: str,
    user_id: UUID,
):
    project_uuid = _read_token(token)

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    current_users: list[UUID] = project.users or []

    if user_id in current_users:
        raise HTTPException(
            status_code=409, detail="User is already member of the project."
        )

    db.execute(
        update(Project)
        .where(Project.uuid == project_uuid)
        .values(users=current_users + [user_id])
    )
    db.commit()

    return {
        "detail": "Successfully joined the project.",
        "project_uuid": str(project_uuid),
    }


def accept_from_template_share(
    db: Session,
    token: str,
    project_name: str,
    user_uuid: UUID,
) -> UUID:
    project_uuid = _read_token(token)

    generated_template = template_controller.export_workflow_to_template(
        db, project_uuid
    )

    created_project_id = project_controller.build_project_from_template(
        db,
        generated_template,
        user_uuid,
        project_name,
    )

    return created_project_id
