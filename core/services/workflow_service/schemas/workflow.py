from pydantic import BaseModel
from enum import Enum

from services.workflow_service.schemas.compute_block import ConfigType


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
