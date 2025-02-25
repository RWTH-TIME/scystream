from fastapi import HTTPException
import requests
import os
from typing import List, Dict, Optional, Union

from sqlalchemy.orm import Session
from utils.database.session_injector import get_database
from services.workflow_service.models.block import Block
from services.workflow_service.models.entrypoint import Entrypoint
from services.workflow_service.models.inputoutput import InputOutput

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
) -> Block:
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
        return db.query(Block).filter(Block.uuid == cb.uuid).first()
    except Exception as e:
        raise e
