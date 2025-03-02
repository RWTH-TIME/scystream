from fastapi import HTTPException
import requests
import os
from typing import List, Dict, Optional, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from utils.database.session_injector import get_database
from services.workflow_service.models.block import Block, block_dependencies
from services.workflow_service.models.entrypoint import Entrypoint
from services.workflow_service.models.inputoutput import (
    InputOutput, InputOutputType
)
from services.workflow_service.schemas.compute_block import (
    UpdateEntrypointDTO, UpdateInputOutputDTO
)

from scystream.sdk.config import SDKConfig, load_config

TEMP_DIR = "tmp/"
# TODO: ENV Var?
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

os.makedirs(TEMP_DIR, exist_ok=True)


def _convert_github_to_raw(github_url: str) -> str:
    return (
        github_url.replace("github.com", "raw.githubusercontent.com")
        .replace("/blob/", "/")
    )


def _get_cb_info_from_repo(repo_url: str) -> Block:
    if "github.com" in repo_url:
        repo_url = _convert_github_to_raw(repo_url)

    try:
        response = requests.get(repo_url, timeout=10)
        response.raise_for_status()

        if len(response.content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=401, detail="File too large.")

        fn = os.path.basename("cbc.yml")
        fp = os.path.join(TEMP_DIR, fn)

        with open(fp, "w", encoding="utf-8") as f:
            f.write(response.text)

        """
        Convert to ComputeBlock
        TODO: If the SDK provides us with the functionality to pass the file
        into the load_config() function directly, without specifying the
        path in SDK config, use this.
        """
        SDKConfig(
            config_path=fp
        )
        loaded_cb = load_config()

        os.remove(fp)

        return loaded_cb
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="Could not query file.")
    except HTTPException as e:
        raise e


def request_cb_info(repo_url: str) -> Block:
    return _get_cb_info_from_repo(repo_url)


def create_compute_block(
        name: str,
        description: str,
        author: str,
        docker_image: str,
        repo_url: str,
        custom_name: str,
        x_pos: float,
        y_pos: float,
        entry_name: str,
        entry_description: str,
        envs: Dict[str, Optional[Union[str, int, float, List, bool]]],
        inputs: List[InputOutput],
        outputs: List[InputOutput],
        project_id: str
) -> UUID:
    db: Session = next(get_database())

    try:
        with db.begin():
            # (1) Create Entrypoint
            entry = Entrypoint(
                name=entry_name,
                description=entry_description,
                envs=envs,
            )
            db.add(entry)
            db.flush()

            # (2) Create Input/Outputs
            input_outputs = inputs + outputs

            for io_item in input_outputs:
                io_item.entrypoint_uuid = entry.uuid

            if input_outputs:
                db.bulk_save_objects(input_outputs)
                db.flush()

            # (3) Create Block
            cb = Block(
                name=name,
                project_uuid=project_id,
                custom_name=custom_name,
                description=description,
                author=author,
                docker_image=docker_image,
                cbc_url=repo_url,
                x_pos=x_pos,
                y_pos=y_pos,
                selected_entrypoint_uuid=entry.uuid
            )
            db.add(cb)
            db.flush()

            db.refresh(entry)
        return cb.uuid
    except Exception as e:
        raise e


def get_compute_blocks_by_project(project_id: UUID) -> List[Block]:
    db: Session = next(get_database())

    return db.query(Block).filter(Block.project_uuid == project_id).all()


def get_block_dependencies_for_blocks(
    block_ids: List[UUID]
) -> list:
    db: Session = next(get_database())

    query = select(
        block_dependencies.c.upstream_block_uuid,
        block_dependencies.c.upstream_output_uuid,
        block_dependencies.c.downstream_block_uuid,
        block_dependencies.c.downstream_input_uuid
    ).where(
        block_dependencies.c.upstream_block_uuid.in_(block_ids) |
        block_dependencies.c.downstream_block_uuid.in_(block_ids)
    )

    # Fetch the dependencies
    return db.execute(query).fetchall()


def _update_io(
        to_be_io: Optional[List[UpdateInputOutputDTO]],
        io_type: InputOutputType,
        entrypoint: Entrypoint
):
    if to_be_io is None:
        return

    existing_io = {
        io.uuid: io for io in entrypoint.input_outputs if io.type == io_type
    }

    for io_update_data in to_be_io:
        if not io_update_data.id or io_update_data.id not in existing_io:
            continue

        io = existing_io[io_update_data.id]

        # Update Config Dict
        if io_update_data.config:
            io.config = {**io.config, **io_update_data.config}


def update_compute_block(
    id: UUID,
    custom_name: Optional[str] = None,
    selected_entrypoint: Optional[UpdateEntrypointDTO] = None,
    x_pos: Optional[float] = None,
    y_pos: Optional[float] = None,
) -> UUID:
    db: Session = next(get_database())

    cb = db.query(Block).filter_by(uuid=id).one_or_none()

    if not cb:
        raise HTTPException(status_code=400, detail="Block not found.")

    # Simple Attributes
    for attr, value in {
        "custom_name": custom_name,
        "x_pos": x_pos,
        "y_pos": y_pos,
    }.items():
        if value is not None:
            setattr(cb, attr, value)

    entrypoint = cb.selected_entrypoint
    if selected_entrypoint:
        # update envs
        if selected_entrypoint.envs:
            entrypoint.envs = {**entrypoint.envs, **selected_entrypoint.envs}

        # Update Inputs/Outputs
        _update_io(selected_entrypoint.inputs,
                   InputOutputType.INPUT, entrypoint)
        _update_io(selected_entrypoint.outputs,
                   InputOutputType.OUTPUT, entrypoint)

    db.commit()
    db.refresh(cb)

    return cb.uuid


def delete_block(
    id: UUID
):
    db: Session = next(get_database())

    block = db.query(Block).filter_by(uuid=id).one_or_none()

    if not block:
        raise HTTPException(status_code=404, detail="Block not found.")

    db.delete(block)
    db.commit()

    return


def create_stream(
    from_block_uuid: UUID,
    from_output_uuid: UUID,
    to_block_uuid: UUID,
    to_input_uuid: UUID
):
    db: Session = next(get_database())

    dependency = {
        "upstream_block_uuid": from_block_uuid,
        "upstream_output_uuid": from_output_uuid,
        "downstream_block_uuid": to_block_uuid,
        "downstream_input_uuid": to_input_uuid,
    }

    db.execute(block_dependencies.insert().values(dependency))
    db.commit()
