from uuid import UUID
from pydantic import BaseModel
from enum import Enum

from services.workflow_service.schemas.compute_block import (
    ConfigType,
    InputOutputDTO,
    BaseInputOutputDTO,
    replace_minio_host
)


class WorkflowStatus(Enum):
    RUNNING = "RUNNING"
    IDLE = "IDLE",
    FINISHED = "FINISHED"
    FAILED = "FAILED"

    @classmethod
    def from_airflow_state(cls, airflow_state: str) -> "WorkflowStatus":
        state_mapping = {
            "running": cls.RUNNING,
            "success": cls.FINISHED,
            "failed": cls.FAILED
        }
        return state_mapping.get(airflow_state.lower(), cls.IDLE)


class WorfklowValidationError(BaseModel):
    project_id: str
    missing_configs: dict[str, list[str]]


# Workflow Configuration
class WorkflowEnvsWithBlockInfo(BaseModel):
    block_uuid: UUID
    block_custom_name: str | None = None
    envs: ConfigType


class UpdateWorkflowConfigurations(BaseModel):
    project_name: str | None = None
    envs: list[WorkflowEnvsWithBlockInfo] | None = None
    ios: list[BaseInputOutputDTO] | None = None


class InputOutputWithBlockInfo(InputOutputDTO):
    block_uuid: UUID
    block_custom_name: str

    @classmethod
    def from_input_output(
        cls,
        name: str,
        input_output,
        block_id: UUID,
        block_name: str,
        presigned_url: str | None = None,
    ):
        return cls(
            id=getattr(input_output, "uuid", None),
            name=name,
            type=input_output.type,
            data_type=input_output.data_type,
            description=input_output.description or "",
            config=input_output.config or {},
            presigned_url=replace_minio_host(url=presigned_url),
            block_uuid=block_id,
            block_custom_name=block_name,
        )


class GetWorkflowConfigurationResponse(BaseModel):
    envs: list[WorkflowEnvsWithBlockInfo]
    workflow_inputs: list[InputOutputWithBlockInfo]
    workflow_intermediates: list[InputOutputWithBlockInfo]
    workflow_outputs: list[InputOutputWithBlockInfo]


# Worklow Templates:
class WorkflowTemplateMetaData(BaseModel):
    file_identifier: str
    name: str
    description: str


class DependsOn(BaseModel):
    block: str
    output: str


class Input(BaseModel):
    identifier: str
    settings: ConfigType | None = None
    depends_on: DependsOn | None = None


class Output(BaseModel):
    identifier: str
    settings: ConfigType | None = None


class Block(BaseModel):
    name: str
    repo_url: str
    entrypoint: str
    settings: ConfigType | None = None
    inputs: list[Input] | None = None
    outputs: list[Output] | None = None


class PipelineMetadata(BaseModel):
    name: str
    description: str


class WorkflowTemplate(BaseModel):
    file_identifier: str
    pipeline: PipelineMetadata
    blocks: list[Block]
