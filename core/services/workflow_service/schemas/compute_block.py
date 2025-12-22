from uuid import UUID

from enum import Enum
from typing import Literal
from pydantic import BaseModel, validator, model_validator
from urllib.parse import urlparse

from services.workflow_service.models.input_output import (
    DataType,
    InputOutput,
    InputOutputType
)
from utils.config.environment import ENV
from utils.config.defaults import get_file_cfg_defaults_dict

ConfigType = dict[str, str | int | float | list | bool | None]


class BlockStatus(Enum):
    SUCCESS = "SUCCESS"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    SCHEDULED = "SCHEDULED"
    IDLE = "IDLE"

    @classmethod
    def from_airflow_state(cls, airflow_state: str | None) -> "BlockStatus":
        if airflow_state is None:
            return cls.IDLE
        state_mapping = {
            "success": cls.SUCCESS,
            "running": cls.RUNNING,
            "failed": cls.FAILED,
            "scheduled": cls.SCHEDULED,
        }

        return state_mapping.get(airflow_state.lower(), cls.IDLE)


def _validate_url(url: str):
    if url.startswith("git@"):
        return

    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(
            "Insecure URL! Only HTTPS or SSH git URLs are allowed.")


def _get_io_data_type(type: str) -> str:
    data_type_map = {
        DataType.FILE.value: DataType.FILE.value,
        DataType.PGTABLE.value: DataType.PGTABLE.value,
    }
    return data_type_map.get(type, DataType.CUSTOM.value)


def replace_minio_host(url: str | None) -> str | None:
    if url:
        defaults = get_file_cfg_defaults_dict("placeholder")
        default_minio_url = f"{defaults.get("S3_HOST")}:{
            defaults.get("S3_PORT")}"
        """
        The client can never use the presigned url with the default minio
        host. Therefore we replace the default minio host, if it exists in
        the presigned url,with the externally reachable url of the data
        minio.
        """
        return url.replace(default_minio_url, ENV.EXTERNAL_URL_DATA_S3)
    return url

# Inputs & Outputs


class BaseIODTO(BaseModel):
    id: UUID | None = None
    name: str | None = None
    data_type: DataType

    @classmethod
    def from_input_output(cls, io):
        return cls(
            id=io.uuid,
            name=io.name,
            data_type=io.data_type
        )


class InputOutputDTO(BaseIODTO):
    name: str
    type: InputOutputType | None = None
    description: str | None = None
    config: ConfigType
    presigned_url: str | None = None
    selected_file_b64: str | None = None
    selected_file_type: str | None = None

    @model_validator(mode="after")
    def validate_selected_file_fields(self):
        if self.selected_file_b64 and not self.selected_file_type:
            raise ValueError(
                """
                selected_file_type must be set if selected_file_b64 is provided
                """
            )
        return self

    @classmethod
    def from_input_output(
            cls,
            name: str,
            input_output,
            presigned_url: str | None = None,
    ):
        return cls(
            id=getattr(input_output, "uuid", None),
            name=name,
            type=input_output.type,
            data_type=(input_output.data_type),
            description=input_output.description or "",
            config=input_output.config or {},
            presigned_url=replace_minio_host(url=presigned_url),
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


# Entrypoint

class BaseEntrypointDTO(BaseModel):
    id: UUID | None = None
    name: str
    inputs: list[BaseIODTO]
    outputs: list[BaseIODTO]


class EntrypointDTO(BaseEntrypointDTO):
    id: UUID | None = None
    name: str
    description: str
    inputs: list[InputOutputDTO]
    outputs: list[InputOutputDTO]
    envs: ConfigType

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


# Node:

class PositionDTO(BaseModel):
    x: float
    y: float


class BaseNodeDataDTO(BaseModel):
    id: UUID
    name: str
    custom_name: str
    description: str
    author: str
    image: str
    status: BlockStatus = BlockStatus.IDLE

    @validator("status")
    def set_status(cls, status):
        return status or BlockStatus.IDLE


class SimpleNodeDataDTO(BaseNodeDataDTO):
    selected_entrypoint: BaseEntrypointDTO


class NodeDataDTO(BaseNodeDataDTO):
    selected_entrypoint: EntrypointDTO


class BaseNodeDTO(BaseModel):
    id: UUID
    position: PositionDTO
    type: Literal["computeBlock"] = "computeBlock"


class SimpleNodeDTO(BaseNodeDTO):
    data: SimpleNodeDataDTO

    @classmethod
    def from_compute_block(
            cls,
            cb,
            status: BlockStatus = BlockStatus.IDLE
    ):
        return cls(
            id=cb.uuid,
            position=PositionDTO(
                x=cb.x_pos,
                y=cb.y_pos,
            ),
            type="computeBlock",
            data=SimpleNodeDataDTO(
                id=cb.uuid,
                name=cb.name,
                custom_name=cb.custom_name,
                description=cb.description,
                author=cb.author,
                image=cb.docker_image,
                selected_entrypoint=BaseEntrypointDTO(
                    id=cb.selected_entrypoint.uuid,
                    name=cb.selected_entrypoint.name,
                    inputs=[
                        BaseIODTO.from_input_output(io)
                        for io in cb.selected_entrypoint.input_outputs
                        if io.type == InputOutputType.INPUT
                    ],
                    outputs=[
                        BaseIODTO.from_input_output(io)
                        for io in cb.selected_entrypoint.input_outputs
                        if io.type == InputOutputType.OUTPUT
                    ]
                ),
                status=status
            ),
        )


class NodeDTO(BaseNodeDTO):
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


# Edge:

class EdgeDTO(BaseModel):
    id: str | None = None
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


# Requests & Responses:

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
    entrypoints: list[EntrypointDTO]

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


class GetNodesByProjectResponse(BaseModel):
    blocks: list[SimpleNodeDTO]
    edges: list[EdgeDTO]


class BaseInputOutputDTO(BaseModel):
    id: UUID
    config: ConfigType | None = None
    selected_file_b64: str | None = None
    selected_file_type: str | None = None

    @model_validator(mode="after")
    def validate_selected_file_fields(self):
        if self.selected_file_b64 and not self.selected_file_type:
            raise ValueError(
                """
                selected_file_type must be set if selected_file_b64 is provided
                """
            )
        return self


class UpdateInputOutputResponseDTO(BaseInputOutputDTO):
    type: InputOutputType
    entrypoint_id: UUID
    presigned_url: str | None = None

    @classmethod
    def from_input_output(cls, input_output, presigned_url: str | None = None):
        return cls(
            id=input_output.uuid,
            type=input_output.type,
            entrypoint_id=input_output.entrypoint_uuid,
            config=input_output.config or {},
            presigned_url=replace_minio_host(url=presigned_url)
        )


class UpdateComputeBlockDTO(BaseModel):
    id: UUID
    envs: ConfigType | None = None
    custom_name: str | None = None
    x_pos: float | None = None
    y_pos: float | None = None
