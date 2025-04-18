from fastapi import HTTPException
import requests
import os
from typing import List, Dict, Optional, Union
from uuid import UUID, uuid4
import tempfile
import urllib.parse

from sqlalchemy import select, case, asc, delete
from sqlalchemy.orm import Session, contains_eager
from utils.database.session_injector import get_database
from services.workflow_service.models.block import Block, block_dependencies
from utils.config.environment import ENV
from services.workflow_service.models.entrypoint import Entrypoint
from services.workflow_service.models.input_output import (
    InputOutput, InputOutputType, DataType
)
from services.workflow_service.schemas.compute_block import (
    UpdateEntrypointDTO, UpdateInputOutputDTO
)

from scystream.sdk.config import SDKConfig, load_config
from scystream.sdk.env.settings import PostgresSettings, FileSettings
from scystream.sdk.config.models import ComputeBlock

# TODO: Hash the secrets
FILE_CFG_DEFAULTS = {
    "S3_HOST": ENV.DEFAULT_CB_CONFIG_S3_HOST,
    "S3_PORT": ENV.DEFAULT_CB_CONFIG_S3_PORT,
    "S3_ACCESS_KEY": ENV.DEFAULT_CB_CONFIG_S3_ACCESS_KEY,
    "S3_SECRET_KEY": ENV.DEFAULT_CB_CONFIG_S3_SECRET_KEY,
    "BUCKET_NAME": ENV.DEFAULT_CB_CONFIG_S3_BUCKET_NAME,
    "FILE_PATH": ENV.DEFAULT_CB_CONFIG_S3_FILE_PATH,
    "FILE_NAME": f"file_{uuid4()}",
}

PG_CFG_DEFAULTS = {
    "PG_USER": ENV.DEFAULT_CB_CONFIG_PG_USER,
    "PG_PASS": ENV.DEFAULT_CB_CONFIG_PG_PASS,
    "PG_HOST": ENV.DEFAULT_CB_CONFIG_S3_HOST,
    "PG_PORT": ENV.DEFAULT_CB_CONFIG_PG_PORT,
    "DB_TABLE": f"table_{uuid4()}",
}

SETTINGS_CLASS = {
    DataType.FILE: FileSettings,
    DataType.PGTABLE: PostgresSettings
}


def _convert_github_to_raw(github_url: str) -> str:
    parsed_url = urllib.parse.urlparse(github_url)

    raw_url = parsed_url._replace(
        netloc="raw.githubusercontent.com",
        path=parsed_url.path.replace("/blob/", "/")
    )

    return urllib.parse.urlunparse(raw_url)


def _get_cb_info_from_repo(repo_url: str) -> ComputeBlock:
    if "github.com" in repo_url:
        repo_url = _convert_github_to_raw(repo_url)

    try:
        response = requests.get(repo_url, timeout=10)
        response.raise_for_status()

        if len(response.content) > ENV.MAX_CBC_FILE_SIZE:
            raise HTTPException(status_code=401, detail="File too large.")

        with tempfile.NamedTemporaryFile(
                delete=False,
                mode="w",
                encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(response.text)
            temp_file_path = tmp_file.name

        """
        Convert to ComputeBlock
        TODO: If the SDK provides us with the functionality to pass the file
        into the load_config() function directly, without specifying the
        path in SDK config, use this.
        """
        sdk_config = SDKConfig()
        sdk_config.set_config_path(temp_file_path)
        loaded_cb = load_config()

        return loaded_cb
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="Could not query file.")
    except HTTPException as e:
        raise e
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def request_cb_info(repo_url: str) -> ComputeBlock:
    cb = _get_cb_info_from_repo(repo_url)

    for entry_name, entry in cb.entrypoints.items():
        for on, output in entry.outputs.items():
            # Determine the type and the default values
            o_type = (
                DataType.FILE if output.type == "file"
                else DataType.PGTABLE
            )
            default_values = (
                FILE_CFG_DEFAULTS if o_type is DataType.FILE
                else PG_CFG_DEFAULTS
            )

            # Update the config with default values
            output.config = _updated_configs_with_values(
                output, default_values, o_type
            )

    return cb


def _updated_configs_with_values(
        io: InputOutput,
        default_values: dict,
        type: DataType
) -> dict:
    """
    Returns a new config dict with default keys replaced by values from
    default_values.

    Parameters:
    - io: InputOutput object whose config will be updated.
    - default_values: Dict mapping default keys to their replacement values.

    Returns:
    - A new config dictionary with updated values.
    """
    new_config = io.config.copy() if io.config else {}

    settings_class = SETTINGS_CLASS.get(type)
    if not settings_class:
        return new_config

    default_keys = settings_class.__annotations__.keys()
    cfg_keys = {key: key for key in new_config}

    for dk in default_keys:
        key = next((k for k in cfg_keys if dk in k), None)
        if key and dk in default_values:
            # Only replace if default_values[dk] is set
            new_config[key] = default_values[dk]

    return new_config


def _extract_default_keys_to_update_values(
    io: InputOutput
):
    """
    This class returns a dict that maps the previously prefixed
    default keys values to their default keys.

    e.g.
    d = {
        prefix_S3_HOST: test
    }

    to:

    p = {
        S3_HOST: test
    }
    """
    settings_class = SETTINGS_CLASS.get(io.data_type)
    default_keys = set(
        settings_class.__annotations__.keys()
    )
    return {
        dk: value for key, value in io.config.items()
        if (dk := next((d for d in default_keys if d in key), None))
    }


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

            for o in input_outputs:
                o.entrypoint_uuid = entry.uuid

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

    order_case = case(
        (InputOutput.data_type == DataType.FILE, 1),
        (InputOutput.data_type == DataType.PGTABLE, 2),
        (InputOutput.data_type == DataType.CUSTOM, 3),
        else_=4
    )

    blocks = (
        db.query(Block)
        .join(Block.selected_entrypoint)
        .outerjoin(Entrypoint.input_outputs)
        .filter(Block.project_uuid == project_id)
        .order_by(order_case, asc(InputOutput.name))
        .options(
            contains_eager(Block.selected_entrypoint)
            .contains_eager(Entrypoint.input_outputs)
        )
        .all()
    )

    return blocks


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
    entrypoint: Entrypoint,
    db: Session
):
    if to_be_io is None or entrypoint is None:
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

            # If it's an OUTPUT, check for connected inputs that can
            # be overwritten
            if (
                    io_type == InputOutputType.OUTPUT and
                    (io.data_type == DataType.FILE
                     or io.data_type == DataType.PGTABLE)
            ):
                result = db.execute(
                    select(block_dependencies.c.downstream_input_uuid)
                    .where(
                        block_dependencies.c.upstream_output_uuid == io.uuid
                    )
                ).fetchall()

                downstream_inputs = [row[0] for row in result]

            if downstream_inputs:
                downstream_ios = db.query(InputOutput).filter(
                    InputOutput.uuid.in_(downstream_inputs)
                ).all()

                # Apply the same config update to connected inputs
                # We are sure here that the downstream has the same type
                for downstream_io in downstream_ios:
                    update_dict = _extract_default_keys_to_update_values(io)
                    downstream_io.config = _updated_configs_with_values(
                        downstream_io, update_dict, downstream_io.data_type)


def update_compute_block(
    id: UUID,
    custom_name: Optional[str] = None,
    selected_entrypoint: Optional[UpdateEntrypointDTO] = None,
    x_pos: Optional[float] = None,
    y_pos: Optional[float] = None,
) -> UUID:
    db: Session = next(get_database())

    try:
        with db.begin():
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
            if selected_entrypoint and entrypoint:
                # Update envs safely
                if selected_entrypoint.envs:
                    entrypoint.envs.update(selected_entrypoint.envs)

                _update_io(selected_entrypoint.inputs,
                           InputOutputType.INPUT, entrypoint, db)
                _update_io(selected_entrypoint.outputs,
                           InputOutputType.OUTPUT, entrypoint, db)

            db.flush()
            db.refresh(cb)

        return cb.uuid

    except Exception as e:
        raise e


def delete_block(
    id: UUID
):
    db: Session = next(get_database())

    block = db.query(Block).filter_by(uuid=id).one_or_none()

    if not block:
        raise HTTPException(status_code=404, detail="Block not found.")

    db.delete(block)
    db.commit()


def create_stream_and_update_target_cfg(
    from_block_uuid: UUID,
    from_output_uuid: UUID,
    to_block_uuid: UUID,
    to_input_uuid: UUID,
):
    db: Session = next(get_database())

    try:
        with db.begin():
            dependency = {
                "upstream_block_uuid": from_block_uuid,
                "upstream_output_uuid": from_output_uuid,
                "downstream_block_uuid": to_block_uuid,
                "downstream_input_uuid": to_input_uuid,
            }

            db.execute(block_dependencies.insert().values(dependency))

            # Compare the cfgs, overwrite the cfgs
            target_io = db.query(InputOutput).filter_by(
                uuid=to_input_uuid).one_or_none()
            source_io = db.query(InputOutput).filter_by(
                uuid=from_output_uuid).one_or_none()

            if target_io.data_type != source_io.data_type:
                # Data types do not match, dont allow connection
                raise HTTPException(
                    status_code=400,
                    detail="Source & Target types do not match"
                )

                # Custom inputs are not overwritten
            if (
                    (target_io.data_type != source_io.data_type) or
                    (target_io.data_type is DataType.CUSTOM)
            ):
                return target_io.uuid

            extracted_defaults = _extract_default_keys_to_update_values(
                source_io
            )
            target_io.config = _updated_configs_with_values(
                target_io, extracted_defaults, target_io.data_type)

            return target_io.uuid
    except Exception as e:
        raise e


def delete_edge(
    from_block_uuid: UUID,
    from_output_uuid: UUID,
    to_block_uuid: UUID,
    to_input_uuid: UUID,
):
    db: Session = next(get_database())

    stmt = delete(block_dependencies).where(
        block_dependencies.c.upstream_block_uuid == from_block_uuid,
        block_dependencies.c.upstream_output_uuid == from_output_uuid,
        block_dependencies.c.downstream_block_uuid == to_block_uuid,
        block_dependencies.c.downstream_input_uuid == to_input_uuid,
    )

    db.execute(stmt)
    db.commit()
