from typing import List, Dict, Optional, Union
from pydantic import BaseModel, validator
from urllib.parse import urlparse

from services.workflow_service.models.inputoutput import (
    InputOutputType,
    DataType
)
from services.workflow_service.models.entrypoint import Entrypoint
from utils.config.environment import ENV


# Helper function to validate URLs
def _validate_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Insecure URL! Only HTTPs URLs are allowed.")
    if parsed.netloc not in ENV.TRUSTED_CBC_DOMAINS:
        raise ValueError("Untrusted Domain.")


class InputOutputResponse(BaseModel):
    name: str
    data_type: DataType
    description: Optional[str] = None
    config: Dict[str, Optional[Union[str, int, float, List, bool]]]

    @classmethod
    def from_input_output(cls, name: str, input_output):
        return cls(
            name=name,
            data_type=(DataType.FILE if input_output.type ==
                       "file" else DataType.DBINPUT),
            description=input_output.description or "",
            config=input_output.config or {}
        )


class EntrypointResponse(BaseModel):
    name: str
    description: str
    inputs: List[InputOutputResponse]
    outputs: List[InputOutputResponse]
    envs: Dict[str, Optional[Union[str, int, float, List, bool]]]

    @classmethod
    def from_entrypoint(cls, name: str, entrypoint: Entrypoint):
        return cls(
            name=name,
            description=entrypoint.description,
            envs=entrypoint.envs or {},
            inputs=[
                InputOutputResponse.from_input_output(io_name, io_model)
                for io_name, io_model in (entrypoint.inputs or {}).items()
            ],
            outputs=[
                InputOutputResponse.from_input_output(io_name, io_model)
                for io_name, io_model in (entrypoint.outputs or {}).items()
            ],
        )

        @staticmethod
        def _filter_and_transform(input_outputs, type_filter):
            return [
                InputOutputResponse.from_input_output(input_output)
                for input_output in input_outputs
                if input_output.type == type_filter
            ]


class ComputeBlockInformationRequest(BaseModel):
    cbc_url: str

    @validator("cbc_url")
    def validate_cbc_url(cls, v):
        _validate_url(v)
        return v


class ComputeBlockInformationResponse(BaseModel):
    name: str
    description: str
    author: str
    image: Optional[str]
    entrypoints: List[EntrypointResponse]

    @classmethod
    def from_compute_block(cls, cb):
        return cls(
            name=cb.name,
            author=cb.author,
            description=cb.description,
            image=cb.docker_image,
            entrypoints=[
                EntrypointResponse.from_entrypoint(name, entrypoint)
                for name, entrypoint in cb.entrypoints.items()
            ]
        )
