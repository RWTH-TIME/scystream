from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List  # , Tuple

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


def add_new_block(
    project_uuid: UUID,
    name: str,
    priority_weight: int,
    retries: int,
    retry_delay: int,
    custom_name: str,
    description: str,
    author: str,
    docker_image: str,
    repo_url: str,
    selected_entrypoint_uuid: UUID,
    x_pos: float,
    y_pos: float,
    upstream_blocks: List[UUID],
    downstream_blocks: List[UUID]
) -> None:

    # Create block

    block = Block(
        uuid=uuid4(),
        name=name,
        project_uuid=project_uuid,
        priority_weight=priority_weight,
        retries=retries,
        retry_delay=retry_delay,
        custom_name=custom_name,
        description=description,
        author=author,
        docker_image=docker_image,
        repo_url=repo_url,
        selected_entrypoint_uuid=selected_entrypoint_uuid,
        x_pos=x_pos,
        y_pos=y_pos,

    )

    db: Session = next(get_database())
    print(project_uuid)
    # Verify the project exists
    project = db.query(Project).filter(
        Project.uuid == project_uuid).one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Resolve upstream blocks if provided
    try:
        if upstream_blocks:
            upstream_blocks = db.query(Block).filter(
                Block.uuid.in_(upstream_blocks),
                Block.project_uuid == project_uuid,
            ).all()
            block.upstream_blocks = upstream_blocks
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Upstream blocks are invalid")

    try:
        if downstream_blocks:
            downstream_blocks = db.query(Block).filter(
                Block.uuid.in_(downstream_blocks),
                Block.project_uuid == project_uuid,
            ).all()
            block.downstream_blocks = downstream_blocks
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Downstream blocks are invalid")

    # Add block to db
    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if block in project.blocks:
        raise HTTPException(
            status_code=404, detail="Block is already in the project"
        )

    project.blocks.append(block)

    db.commit()

    return None


def delete_block(project_uuid: UUID, block_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    block = db.query(Block).filter_by(uuid=block_uuid).one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    if block not in project.blocks:
        raise HTTPException(
            status_code=404, detail="Block is not part of the project"
        )

    project.blocks.remove(block)

    db.commit()

    return None


def update_block(
    project_uuid: UUID, block_uuid: UUID, new_block_name: str
) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    block = db.query(Block).filter_by(uuid=block_uuid).one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

    if block not in project.blocks:
        raise HTTPException(
            status_code=404, detail="Block is not part of the project"
        )
    block.name = new_block_name

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

    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")

    return projects


def read_projects_by_user_uuid(user_uuid: UUID) -> List[Project]:
    db: Session = next(get_database())

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    projects = user.projects

    return projects
