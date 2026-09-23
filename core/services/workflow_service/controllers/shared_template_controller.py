"""Workflow templates created from projects ("save as template").

Besides the templates of the template repository (WORKFLOW_TEMPLATE_REPO),
users can turn a project into a template that is visible to all users. It
has the same format as a repository template, so it can be exported as
YAML and committed to the template repository as well.

A template describes *what* a workflow does, not *where* a project stores
its data: generated locations (file names, buckets, database tables,
schemas, DSNs, S3 endpoints and credentials) are left out, so every project
created from the template gets its own. Settings that look like secrets are
never included.
"""

import logging
import re
from uuid import UUID, uuid4

import yaml
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from services.superset_service import project_sync
from services.workflow_service.models.block import Block, block_dependencies
from services.workflow_service.models.input_output import (
    DataType,
    InputOutputType,
)
from services.workflow_service.models.project import Project
from services.workflow_service.models.workflow_template import (
    SharedWorkflowTemplate,
)
from services.workflow_service.schemas.workflow import WorkflowTemplate
from utils.config.environment import ENV
from utils.data import file_handling as fh
from utils.database.session_injector import get_database

IDENTIFIER_PREFIX = "shared:"
DEFAULT_TAG = "shared"

# configuration every project generates for its own inputs & outputs
MANAGED_IO_KEYS = (
    "S3_HOST", "S3_PORT", "S3_ACCESS_KEY", "S3_SECRET_KEY", "BUCKET_NAME",
    "FILE_PATH", "FILE_NAME", "DB_DSN", "DB_TABLE", "DB_SCHEMA",
)
SECRET_KEY_PATTERN = re.compile(
    r"(PASSWORD|PASSWD|PASS|SECRET|TOKEN|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY"
    r"|CREDENTIALS?)$",
    re.IGNORECASE,
)


def is_shared_identifier(identifier: str) -> bool:
    return identifier.startswith(IDENTIFIER_PREFIX)


def shared_identifier(template_uuid: UUID) -> str:
    return f"{IDENTIFIER_PREFIX}{template_uuid}"


def _is_empty(value) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _is_secret(key: str) -> bool:
    return bool(SECRET_KEY_PATTERN.search(key))


def _is_managed(key: str) -> bool:
    return any(key.endswith(managed) for managed in MANAGED_IO_KEYS)


def _template_envs(envs: dict | None, include_settings: bool) -> dict | None:
    if not include_settings:
        return None
    settings = {
        key: value for key, value in (envs or {}).items()
        if not _is_secret(key) and not _is_empty(value)
    }
    return settings or None


def _template_io_settings(config: dict | None, include_settings: bool):
    if not include_settings:
        return None
    settings = {
        key: value for key, value in (config or {}).items()
        if not _is_managed(key) and not _is_secret(key)
        and not _is_empty(value)
    }
    return settings or None


def project_to_template(
    db: Session,
    project: Project,
    name: str,
    description: str,
    tags: list[str],
    include_settings: bool = True,
) -> dict:
    """Describes the project's workflow in the workflow template format."""
    blocks: list[Block] = list(project.blocks)
    if not blocks:
        raise HTTPException(
            status_code=422,
            detail="The project has no compute blocks",
        )
    by_uuid = {block.uuid: block for block in blocks}

    edges = db.execute(
        block_dependencies.select().where(
            block_dependencies.c.downstream_block_uuid.in_(list(by_uuid)),
        ),
    ).fetchall()
    io_names = {
        io.uuid: io.name
        for block in blocks
        for io in block.selected_entrypoint.input_outputs
    }
    depends_on = {
        edge.downstream_input_uuid: {
            "block": by_uuid[edge.upstream_block_uuid].custom_name,
            "output": io_names[edge.upstream_output_uuid],
        }
        for edge in edges
        if edge.upstream_block_uuid in by_uuid
    }

    template_blocks = []
    for block in sorted(blocks, key=lambda b: (b.x_pos or 0, b.y_pos or 0)):
        entry = block.selected_entrypoint
        inputs, outputs = [], []
        for io in sorted(entry.input_outputs, key=lambda io: io.name or ""):
            item = {"identifier": io.name}
            connected = io.uuid in depends_on
            # connected inputs are configured from their upstream output,
            # custom ones keep their own configuration
            if not connected or io.data_type == DataType.CUSTOM:
                settings = _template_io_settings(io.config, include_settings)
                if settings:
                    item["settings"] = settings
            if io.type == InputOutputType.INPUT:
                if connected:
                    item["depends_on"] = depends_on[io.uuid]
                inputs.append(item)
            else:
                outputs.append(item)

        template_block = {
            "name": block.custom_name,
            "repo_url": block.cbc_url,
            "entrypoint": entry.name,
        }
        envs = _template_envs(entry.envs, include_settings)
        if envs:
            template_block["settings"] = envs
        if inputs:
            template_block["inputs"] = inputs
        if outputs:
            template_block["outputs"] = outputs
        template_blocks.append(template_block)

    return {
        "pipeline": {
            "name": name,
            "description": description,
            "tags": tags,
        },
        "blocks": template_blocks,
    }


def _validate(definition: dict, identifier: str) -> WorkflowTemplate:
    # imported here, template_controller imports this module
    from services.workflow_service.controllers import template_controller

    try:
        template = WorkflowTemplate.model_validate(
            {**definition, "file_identifier": identifier},
        )
    except ValidationError as e:
        raise HTTPException(status_code=422,
                            detail=f"Invalid template: {e}") from e
    template_controller.build_workflow_graph(template)
    return template


def _superset_template_key(template_uuid: UUID) -> str:
    return (
        f"{ENV.SUPERSET_EXPORT_S3_PREFIX.strip('/')}/templates/"
        f"{template_uuid.hex}/superset/export.zip"
    )


def create_shared_template(
    project_uuid: UUID,
    name: str,
    description: str,
    tags: list[str] | None,
    user_uuid: UUID,
    user_email: str | None,
    include_settings: bool = True,
) -> SharedWorkflowTemplate:
    db: Session = next(get_database())
    try:
        project = db.query(Project).filter_by(uuid=project_uuid).one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        tags = [t.strip() for t in (tags or []) if t and t.strip()] or [
            DEFAULT_TAG,
        ]
        template_uuid = uuid4()
        definition = project_to_template(
            db, project, name, description, tags, include_settings,
        )
        _validate(definition, shared_identifier(template_uuid))

        superset_key = None
        try:
            visualization = project_sync.export_template(project_uuid)
        except HTTPException:
            visualization = None  # the project has no visualization
        except Exception:
            logging.exception("Could not export the Superset visualization "
                              "of project %s", project_uuid)
            visualization = None
        if visualization:
            superset_key = _superset_template_key(template_uuid)
            fh.put_project_bytes(superset_key, visualization)

        record = SharedWorkflowTemplate(
            uuid=template_uuid,
            name=name,
            description=description,
            tags=tags,
            definition=definition,
            superset_template_s3_key=superset_key,
            source_project_uuid=project_uuid,
            created_by=user_uuid,
            created_by_email=user_email,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logging.info("Created shared template %s from project %s",
                     template_uuid, project_uuid)
        return record
    finally:
        db.close()


def list_shared_templates() -> list[SharedWorkflowTemplate]:
    db: Session = next(get_database())
    try:
        return (
            db.query(SharedWorkflowTemplate)
            .order_by(SharedWorkflowTemplate.created_at.desc())
            .all()
        )
    finally:
        db.close()


def _get_record(identifier: str) -> SharedWorkflowTemplate:
    try:
        template_uuid = UUID(identifier.removeprefix(IDENTIFIER_PREFIX))
    except ValueError:
        raise HTTPException(status_code=404, detail="Template not found")
    db: Session = next(get_database())
    try:
        record = (
            db.query(SharedWorkflowTemplate)
            .filter_by(uuid=template_uuid)
            .one_or_none()
        )
    finally:
        db.close()
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    return record


def to_workflow_template(record: SharedWorkflowTemplate) -> WorkflowTemplate:
    return WorkflowTemplate.model_validate({
        **record.definition,
        "file_identifier": shared_identifier(record.uuid),
    })


def get_shared_template(identifier: str) -> WorkflowTemplate:
    return to_workflow_template(_get_record(identifier))


def superset_template(identifier: str) -> bytes | None:
    record = _get_record(identifier)
    if not record.superset_template_s3_key:
        return None
    return fh.get_project_bytes(record.superset_template_s3_key)


def template_yaml(identifier: str) -> str:
    """The template in the format of the template repository."""
    return yaml.safe_dump(_get_record(identifier).definition,
                          sort_keys=False)


def delete_shared_template(identifier: str, user_uuid: UUID) -> None:
    record = _get_record(identifier)
    if record.created_by != user_uuid:
        raise HTTPException(
            status_code=403,
            detail="Only the creator can delete a template",
        )
    db: Session = next(get_database())
    try:
        db.query(SharedWorkflowTemplate).filter_by(uuid=record.uuid).delete()
        db.commit()
    finally:
        db.close()
