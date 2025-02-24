from fastapi import HTTPException
import requests
import os
import uuid
from sqlalchemy.orm import Session, joinedload

from utils.database.session_injector import get_database
from services.workflow_service.models.block import Block
from services.workflow_service.models.entrypoint import Entrypoint
from services.workflow_service.models.inputoutput import (
    InputOutput, InputOutputType, DataType
)

from scystream.sdk.config import SDKConfig, load_config

TEMP_DIR = "tmp/"
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


def _create_compute_block(name: str, repo_url: str, project_id: str) -> Block:
    db: Session = next(get_database())
    loaded_cb = _get_cb_info_from_repo(repo_url)

    try:
        # Start transaction
        with db.begin():
            # (1) Create Compute Block
            compute_block = Block(
                name=loaded_cb.name,
                description=loaded_cb.description,
                author=loaded_cb.author,
                docker_image=loaded_cb.docker_image,
                repo_url=repo_url,
                project_uuid=project_id,
                custom_name=name,
                priority_weight=None,  # TODO: Set priority weight
                retries=None,  # TODO: Set retries
                retry_delay=None,  # TODO: Set retry delay
                x_pos=None,  # TODO: Set x_pos
                y_pos=None,  # TODO: Set y_pos
            )
            db.add(compute_block)
            db.flush()

            # (2) Create Entrypoints
            entrypoints = []
            entrypoints_mapping = {}
            for entry_name, entry_data in loaded_cb.entrypoints.items():
                entrypoint_obj = Entrypoint(
                    uuid=uuid.uuid4(),
                    name=entry_name,
                    description=entry_data.description,
                    envs=entry_data.envs if entry_data.envs else {},
                    block_uuid=compute_block.uuid
                )
                entrypoints.append(entrypoint_obj)
                entrypoints_mapping[entry_name] = entrypoint_obj

            db.bulk_save_objects(entrypoints)
            db.flush()

            # (3) Insert Input/Outputs
            input_outputs = []

            for entry_name, entry_data in loaded_cb.entrypoints.items():
                entrypoint_uuid = entrypoints_mapping[entry_name].uuid

                for io_type, io_items in [
                    ("inputs", entry_data.inputs),
                    ("outputs", entry_data.outputs)
                ]:
                    if io_items is None:
                        continue

                    for io_name, io_data in io_items.items():
                        input_outputs.append(InputOutput(
                            type=(
                                InputOutputType.INPUT
                                if io_type == "inputs"
                                else InputOutputType.OUTPUT
                            ),
                            name=io_name,
                            data_type=(
                                DataType.DBINPUT
                                if io_data.type == "db_table"
                                else DataType.FILE
                            ),
                            description=io_data.description,
                            config=io_data.config,
                            entrypoint_uuid=entrypoint_uuid
                        ))

            if input_outputs:
                db.bulk_save_objects(input_outputs)

            db.commit()

        # Load the compute_block in ORM format with all its relations
        compute_block = db.query(Block).options(
            joinedload(Block.entrypoints).joinedload(Entrypoint.input_outputs)
        ).filter(Block.uuid == compute_block.uuid).one()

        return compute_block
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="Could not query file.")
    except HTTPException as e:
        raise e
