from uuid import UUID
from urllib.parse import urlparse

from pydantic import BaseModel, validator
from typing import List, Dict, Optional, Union
from services.workflow_service.models.inputoutput import InputOutputType, DataType
from utils.config.environment import ENV


def _validate_url(url: str):
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError("Insecure URL! Only HTTPs URLs are allowed.")

    if parsed.netloc not in ENV.TRUSTED_CBC_DOMAINS:
        raise ValueError("Untrusted Domain.")


class InputOutput(BaseModel):
    uuid: UUID
    type: InputOutputType
    name: str
    data_type: DataType
    description: str
    # TODO: optional
    config: Dict[str, Optional[Union[str, int, float, List, bool]]]


class Entrypoint(BaseModel):
    uuid: UUID
    name: str
    description: str
    inputs: List[InputOutput]  # TODO: optional?
    outputs: List[InputOutput]  # TODO: optional?
    # TODO: optional
    envs: Dict[str, Optional[Union[str, int, float, List, bool]]]


class CreateComputeBlockRequest(BaseModel):
    compute_block_title: str
    cbc_url: str

    @validator("cbc_url")
    def validate_cbc_url(cls, v):
        _validate_url(v)
        return v


class CreateComputeBlockResponse(BaseModel):
    uuid: UUID
    name: str
    author: str
    image: str
    project_uuid: UUID
    entrypoints: List[Entrypoint]
