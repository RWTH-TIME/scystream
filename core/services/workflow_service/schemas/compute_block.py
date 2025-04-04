from uuid import UUID

from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, validator
from urllib.parse import urlparse

from services.workflow_service.models.input_output import (
    DataType,
    InputOutput,
    InputOutputType
)
from utils.config.environment import ENV


def _validate_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Insecure URL! Only HTTPs URLs are allowed.")
    if parsed.netloc not in ENV.TRUSTED_CBC_DOMAINS:
        raise ValueError("Untrusted Domain.")


def _get_io_data_type(type: str) -> str:
    data_type_map = {
        DataType.FILE.value: DataType.FILE.value,
        DataType.PGTABLE.value: DataType.PGTABLE.value,
    }
    return data_type_map.get(type, DataType.CUSTOM.value)


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
            data_type=(input_output.data_type),
            description=input_output.description or "",
            config=input_output.config or {}
        )

    @classmethod
    def from_sdk_input_output(cls, name: str, input_output):
        return cls(
            id=getattr(input_output, "uuid", None),
            name=name,
            data_type=_get_io_data_type(input_output.type),
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
    def from_sdk_entrypoint(cls, name: str, entrypoint):
        return cls(
            name=name,
            description=entrypoint.description,
            envs=entrypoint.envs or {},
            inputs=[
                InputOutputDTO.from_sdk_input_output(io_name, io_model)
                for io_name, io_model in (entrypoint.inputs or {}).items()
            ],
            outputs=[
                InputOutputDTO.from_sdk_input_output(io_name, io_model)
                for io_name, io_model in (entrypoint.outputs or {}).items()
            ],
        )


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
    def from_sdk_compute_block(cls, cb):
        return cls(
            name=cb.name,
            author=cb.author,
            description=cb.description,
            image=cb.docker_image,
            entrypoints=[
                EntrypointDTO.from_sdk_entrypoint(name, entrypoint)
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


class IDResponse(BaseModel):
    id: UUID


class PositionDTO(BaseModel):
    x: float
    y: float


class NodeDataDTO(BaseModel):
    id: UUID
    name: str
    custom_name: str
    description: str
    author: str
    image: str
    selected_entrypoint: EntrypointDTO


class NodeDTO(BaseModel):
    id: UUID
    position: PositionDTO
    type: Literal["computeBlock"]
    data: NodeDataDTO

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
            position=PositionDTO(
                x=cb.x_pos,
                y=cb.y_pos,
            ),
            type="computeBlock",
            data=NodeDataDTO(
                id=cb.uuid,
                name=cb.name,
                custom_name=cb.custom_name,
                description=cb.description,
                author=cb.author,
                image=cb.docker_image,
                selected_entrypoint=EntrypointDTO(
                    id=cb.selected_entrypoint.uuid,
                    name=cb.selected_entrypoint.name,
                    description=cb.selected_entrypoint.description,
                    envs=cb.selected_entrypoint.envs,
                    inputs=inputs,
                    outputs=outputs
                ),
            )
        )


class EdgeDTO(BaseModel):
    id: Optional[str] = None
    source: UUID
    target: UUID
    sourceHandle: UUID
    targetHandle: UUID

    @classmethod
    def from_block_dependencies(cls, bd):
        return cls(
            id=f"{bd.upstream_output_uuid}-{bd.downstream_input_uuid}",
            source=bd.upstream_block_uuid,
            targetHandle=bd.downstream_input_uuid,
            target=bd.downstream_block_uuid,
            sourceHandle=bd.upstream_output_uuid,
        )


class GetNodesByProjectResponse(BaseModel):
    blocks: List[NodeDTO]
    edges: List[EdgeDTO]


class UpdateInputOutputDTO(BaseModel):
    id: UUID
    config: Optional[Dict[str,
                          Optional[Union[str, int, float, List, bool]]]] = None


class UpdateEntrypointDTO(BaseModel):
    id: UUID
    inputs: Optional[List[UpdateInputOutputDTO]] = None
    outputs: Optional[List[UpdateInputOutputDTO]] = None
    envs: Dict[str, Optional[Union[str, int, float, List, bool]]] = None


class UpdateComputeBlockRequest(BaseModel):
    id: UUID
    custom_name: Optional[str] = None
    selected_entrypoint: Optional[UpdateEntrypointDTO] = None
    x_pos: Optional[float] = None
    y_pos: Optional[float] = None
