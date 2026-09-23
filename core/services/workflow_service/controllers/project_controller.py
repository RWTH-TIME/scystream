from utils.database.session_injector import get_database
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from services.workflow_service.models.project import Project
from services.workflow_service.models.superset_import_status import (
    SupersetImportStatus,
)
from services.workflow_service.controllers import (
    compute_block_controller,
    template_controller,
)
from services.workflow_service.models.block import Block, block_dependencies
from services.workflow_service.models.entrypoint import Entrypoint
from services.workflow_service.models.input_output import (
    DataType,
    InputOutput,
    InputOutputType,
)
from services.workflow_service.schemas.workflow import WorkflowTemplate
from utils.config.defaults import (
    data_pg_dsn_for_core,
    ensure_schema_exists,
    project_schema,
)
# module import, project_sync depends on the models of this service
from services.superset_service import project_sync


def create_project(
    db: Session,
    name: str,
    current_user_uuid: UUID,
    owner_email: str | None = None,
) -> UUID:
    logging.debug(
        f"Creating project with name: {name} for user: {current_user_uuid}"
    )

    project: Project = Project()

    project.uuid = uuid4()
    project.name = name
    project.created_at = datetime.now(timezone.utc)
    project.users = [current_user_uuid]
    project.owner_email = owner_email
    project.superset_import_status = SupersetImportStatus.NONE.value

    db.add(project)

    logging.info(f"Project {project.uuid} created successfully")
    return project.uuid


def create_project_from_template(
    name: str,
    template_identifier: str,
    current_user_uuid: UUID,
    owner_email: str | None = None,
) -> UUID:
    """
    This method will handle the creation of project, blocks and edges as
    defined in the template.yaml
    """
    db: Session = next(get_database())

    template: WorkflowTemplate = (
        template_controller.get_workflow_template_by_identifier(
            template_identifier
        )
    )
    required_blocks = template_controller.extract_block_urls_from_template(
        template
    )
    unconfigured_blocks = compute_block_controller.bulk_query_blocks(
        required_blocks
    )

    G = template_controller.build_workflow_graph(template)

    try:
        with db.begin():
            project_id = create_project(
                db,
                name,
                current_user_uuid,
                owner_email=owner_email,
            )
            (
                block_name_to_model,
                block_outputs_by_name,
                block_inputs_by_name,
            ) = template_controller.configure_and_create_blocks(
                G, db, unconfigured_blocks, project_id
            )
            template_controller.create_edges_from_template(
                G,
                db,
                block_name_to_model,
                block_outputs_by_name,
                block_inputs_by_name,
            )
        _apply_shared_visualization(template_identifier, project_id)
        return project_id
    except Exception as e:
        logging.exception(f"Error creating project from template: {e}")
        raise e


def _apply_shared_visualization(
    template_identifier: str,
    project_id: UUID,
) -> None:
    """Projects created from a shared template use the Superset
    visualization of the template's source project."""
    from services.workflow_service.controllers import (
        shared_template_controller,
    )
    if not shared_template_controller.is_shared_identifier(
        template_identifier,
    ):
        return
    visualization = shared_template_controller.superset_template(
        template_identifier,
    )
    if visualization:
        project_sync.upload_template(project_id, visualization)


def read_project(project_uuid: UUID) -> Project:
    logging.debug(f"Reading project with UUID: {project_uuid}")
    db: Session = next(get_database())

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        logging.error(f"Project {project_uuid} not found")
        raise HTTPException(status_code=404, detail="Project not found")

    return project


def rename_project(project_uuid: UUID, new_name: str, db: Session) -> Project:
    logging.debug(f"Renaming project {project_uuid} to {new_name}.")

    project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()

    if not project:
        logging.error(f"Project {project_uuid} not found.")
        raise HTTPException(status_code=404, detail="Project not found")

    project.name = new_name

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
        db.query(Project).filter(Project.users.contains([user_uuid])).all()
    )

    if not projects:
        logging.error(f"No projects found for user {user_uuid}")
        raise HTTPException(
            status_code=404,
            detail="No projects found for user",
        )

    logging.info(f"Retrieved {len(projects)} projects for user {user_uuid}")

    return projects


def _new_file_name(io_name: str) -> str:
    return f"file_{io_name}_{uuid4()}"


def _remap_config(config: dict | None, value_map: dict) -> dict:
    return {
        key: value_map.get(value, value) if isinstance(value, str) else value
        for key, value in (config or {}).items()
    }


def clone_project(
    source_uuid: UUID,
    name: str,
    current_user_uuid: UUID,
    owner_email: str | None = None,
) -> UUID:
    """Copies a project with its compute blocks, configurations and edges.

    The clone writes its outputs to its own locations: database outputs use
    the clone's project schema, file outputs get new file names (inputs
    connected to them are updated accordingly). The Superset visualization
    of the source project becomes the visualization template of the clone.
    """
    db: Session = next(get_database())

    with db.begin():
        source = db.query(Project).filter_by(uuid=source_uuid).one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="Project not found")

        clone_uuid = create_project(
            db, name, current_user_uuid, owner_email=owner_email,
        )
        db.flush()

        value_map = {
            project_schema(source.uuid): project_schema(clone_uuid),
        }
        io_map: dict[UUID, InputOutput] = {}
        block_map: dict[UUID, Block] = {}
        has_db_outputs = False

        for block in source.blocks:
            entry = block.selected_entrypoint
            new_entry = Entrypoint(
                name=entry.name,
                description=entry.description,
                envs=dict(entry.envs or {}),
            )
            db.add(new_entry)
            db.flush()

            for io in entry.input_outputs:
                config = dict(io.config or {})
                if (io.type == InputOutputType.OUTPUT
                        and io.data_type == DataType.FILE):
                    for key, value in config.items():
                        if key.endswith("FILE_NAME") and value:
                            value_map[value] = _new_file_name(io.name)
                if io.data_type == DataType.DBTABLE:
                    has_db_outputs = True
                new_io = InputOutput(
                    type=io.type,
                    name=io.name,
                    data_type=io.data_type,
                    description=io.description,
                    config=config,
                    entrypoint_uuid=new_entry.uuid,
                )
                db.add(new_io)
                io_map[io.uuid] = new_io

            new_block = Block(
                name=block.name,
                project_uuid=clone_uuid,
                custom_name=block.custom_name,
                description=block.description,
                author=block.author,
                docker_image=block.docker_image,
                cbc_url=block.cbc_url,
                x_pos=block.x_pos,
                y_pos=block.y_pos,
                selected_entrypoint_uuid=new_entry.uuid,
            )
            db.add(new_block)
            block_map[block.uuid] = new_block

        for new_io in io_map.values():
            new_io.config = _remap_config(new_io.config, value_map)
        db.flush()

        edges = db.execute(
            block_dependencies.select().where(
                block_dependencies.c.upstream_block_uuid.in_(
                    list(block_map),
                ),
            ),
        ).fetchall()
        for edge in edges:
            db.execute(block_dependencies.insert().values(
                upstream_block_uuid=block_map[edge.upstream_block_uuid].uuid,
                upstream_output_uuid=io_map[edge.upstream_output_uuid].uuid,
                downstream_block_uuid=block_map[
                    edge.downstream_block_uuid].uuid,
                downstream_input_uuid=io_map[edge.downstream_input_uuid].uuid,
            ))

        if has_db_outputs:
            ensure_schema_exists(
                data_pg_dsn_for_core(), project_schema(clone_uuid),
            )

        clone = db.query(Project).filter_by(uuid=clone_uuid).one()
        project_sync.copy_visualization(source.uuid, clone)

    logging.info(f"Project {source_uuid} cloned to {clone_uuid}")
    return clone_uuid
