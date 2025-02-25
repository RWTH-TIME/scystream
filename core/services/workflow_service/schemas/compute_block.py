from uuid import UUID

from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, validator
from urllib.parse import urlparse

from services.workflow_service.models.inputoutput import (
    DataType,
    InputOutput,
    InputOutputType
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


class InputOutputDTO(BaseModel):
    id: Optional[UUID] = None
    name: str
    data_type: DataType
    description: Optional[str] = None
    config: Dict[str, Optional[Union[str, int, float, List, bool]]]

    @classmethod
    def from_input_output(cls, name: str, input_output):
        return cls(
            id=getattr(input_output, "uuid", None),
            name=name,
            data_type=(DataType.FILE if input_output.type ==
                       "file" else DataType.DBINPUT),
            description=input_output.description or "",
            config=input_output.config or {}
        )

    @classmethod
    def to_input_output(
        cls,
        input_output,
        type: Literal["Input", "Output"]
    ):
        return InputOutput(
            type=(InputOutputType.INPUT if type ==
                  "Input" else InputOutputType.OUTPUT),
            name=input_output.name,
            data_type=input_output.data_type,
            description=input_output.description,
            config=input_output.config
        )


class EntrypointDTO(BaseModel):
    id: Optional[UUID] = None
    name: str
    description: str
    inputs: List[InputOutputDTO]
    outputs: List[InputOutputDTO]
    envs: Dict[str, Optional[Union[str, int, float, List, bool]]]

    @classmethod
    def from_entrypoint(cls, name: str, entrypoint: Entrypoint):
        return cls(
            name=name,
            description=entrypoint.description,
            envs=entrypoint.envs or {},
            inputs=[
                InputOutputDTO.from_input_output(io_name, io_model)
                for io_name, io_model in (entrypoint.inputs or {}).items()
            ],
            outputs=[
                InputOutputDTO.from_input_output(io_name, io_model)
                for io_name, io_model in (entrypoint.outputs or {}).items()
            ],
        )

    @staticmethod
    def _filter_and_transform(input_outputs, type_filter):
        return [
            InputOutputDTO.from_input_output(input_output)
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
    image: str
    entrypoints: List[EntrypointDTO]

    @classmethod
    def from_compute_block(cls, cb):
        return cls(
            name=cb.name,
            author=cb.author,
            description=cb.description,
            image=cb.docker_image,
            entrypoints=[
                EntrypointDTO.from_entrypoint(name, entrypoint)
                for name, entrypoint in cb.entrypoints.items()
            ]
        )


class CreateComputeBlockRequest(BaseModel):
    project_id: UUID
    cbc_url: str
    name: str
    custom_name: str
    description: str
    author: str
    image: str
    selected_entrypoint: EntrypointDTO
    x_pos: float
    y_pos: float

    @validator("cbc_url")
    def validate_cbc_url(cls, v):
        _validate_url(v)
        return v


class CreateComputeBlockResponse(BaseModel):
    id: Optional[UUID] = None
    name: str
    description: str
    author: str
    image: str
    selected_entrypoint: EntrypointDTO

    @classmethod
    def from_compute_block(cls, cb):
        inputs = [
            InputOutputDTO.from_input_output(io.name, io)
            for io in cb.selected_entrypoint.input_outputs
            if io.type == InputOutputType.INPUT
        ]

        outputs = [
            InputOutputDTO.from_input_output(io.name, io)
            for io in cb.selected_entrypoint.input_outputs
            if io.type == InputOutputType.OUTPUT
        ]

        return cls(
            id=cb.uuid,
            name=cb.name,
            author=cb.author,
            description=cb.description,
            image=cb.docker_image,
            selected_entrypoint=EntrypointDTO(
                id=cb.selected_entrypoint.uuid,  # TODO: is null somehow
                name=cb.selected_entrypoint.name,
                description=cb.selected_entrypoint.description,
                envs=cb.selected_entrypoint.envs,
                inputs=inputs,
                outputs=outputs
            )
        )
