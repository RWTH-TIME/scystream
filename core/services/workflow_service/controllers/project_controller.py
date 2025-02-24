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
    """
    This function contains the logic of creating a block.
    It validates if passed upstream blocks and downstream blocks exist.
    """

    new_block = Block(
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

    # Verify the project exists
    project = db.query(Project).filter(
        Project.uuid == project_uuid).one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Resolve upstream / downstream blocks if provided
    try:
        if upstream_blocks:
            upstream_blocks = db.query(Block).filter(
                Block.uuid.in_(upstream_blocks),
                Block.project_uuid == project_uuid,
            ).all()
            new_block.upstream_blocks = upstream_blocks
    except SQLAlchemyError:
        raise HTTPException(
            status_code=400, detail="Upstream blocks are invalid")
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Error with upstream blocks")

    try:
        if downstream_blocks:
            downstream_blocks = db.query(Block).filter(
                Block.uuid.in_(downstream_blocks),
                Block.project_uuid == project_uuid,
            ).all()
            new_block.downstream_blocks = downstream_blocks
    except SQLAlchemyError:
        raise HTTPException(
            status_code=400, detail="Downstream blocks are invalid")
    except Exception:
        raise HTTPException(status_code=400,
                            detail="Error with downstream blocks")

    # Add block to db
    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if new_block in project.blocks:
        raise HTTPException(
            status_code=409, detail="Block is already in the project"
        )

    existing_block = db.query(Block).filter_by(
        uuid=new_block.uuid).one_or_none()
    if not existing_block:
        db.add(new_block)
        db.commit()

    project.blocks.append(new_block)

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

    return projects


def read_projects_by_user_uuid(user_uuid: UUID) -> List[Project]:
    db: Session = next(get_database())

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    projects = user.projects

    return projects
