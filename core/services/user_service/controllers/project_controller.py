from uuid import UUID, uuid4
from sqlalchemy.orm import Session
import datetime
from typing import List

from utils.database.session_injector import get_database
from services.user_service.models.project import Project
from services.user_service.models.user import User
from services.user_service.models.block import Block


# Create, Read, Update, Delete. ReadAll, ReadByUserUuid
# Still missing any field validation (empty name, uuid is not UUID..)
# Does current uuid need to be extracted from the token?
def create_project(name: str,  current_user_uuid: UUID) -> UUID:
    db: Session = next(get_database())
    project: Project = Project()

    project.uuid = uuid4()
    project.name = name
    project.created_at = datetime.utcnow()
    current_user = (db.query(User).filter_by(uuid=current_user_uuid)
                    .one_or_none())

    if not current_user:
        raise ValueError("User not found")
    # add relation with blocks?

    db.add(project)
    db.commit()
    db.refresh(project)

    return project.uuid


def read_project(project_uuid: UUID) -> Project:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise ValueError("Project not found")

    return project


def rename_project(project_uuid: UUID, new_name: str) -> Project:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise ValueError("Project not found")

    project.name = new_name

    db.commit()
    db.refresh(project)

    return project


def add_user(project_uuid: UUID, user_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise ValueError("Project not found")

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        raise ValueError("User not found")

    if user in project.users:
        raise ValueError("User is already added to the project")

    project.users.append(user)

    db.commit()

    return None


def delete_user(project_uuid: UUID, user_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise ValueError("Project not found")

    user = db.query(User).filter_by(uuid=user_uuid).one_or_none()
    if not user:
        raise ValueError("User not found")

    if user not in project.users:
        raise ValueError("User is not part of the project")

    project.users.remove(user)

    db.commit()

    return None


def add_block(project_uuid: UUID, block_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise ValueError("Project not found")

    block = db.query(Block).filter_by(uuid=block_uuid).one_or_none()
    if not block:
        raise ValueError("Block not found")

    if block in project.blocks:
        raise ValueError("Block is already added to the project")

    project.blocks.append(block)

    db.commit()

    return None


def delete_block(project_uuid: UUID, block_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise ValueError("Project not found")

    block = db.query(Block).filter_by(uuid=block_uuid).one_or_none()
    if not block:
        raise ValueError("Block not found")

    if block not in project.blocks:
        raise ValueError("Block is not part of the project")

    project.blocks.remove(block)

    db.commit()

    return None


def update_block(project_uuid: UUID, block_uuid: UUID,
                 new_block_name: str) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise ValueError("Project not found")

    block = db.query(Block).filter_by(uuid=block_uuid).one_or_none()
    if not block:
        raise ValueError("Block not found")

    if block not in project.blocks:
        raise ValueError("Block is not part of the project")

    block.name = new_block_name

    db.commit()

    return None


def delete_project(project_uuid: UUID) -> None:
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        raise ValueError("Project not found")

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
        raise ValueError("User not found")

    projects = user.projects

    return projects
