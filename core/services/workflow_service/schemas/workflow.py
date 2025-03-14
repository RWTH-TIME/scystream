from pydantic import BaseModel
from typing import List, Dict
from enum import Enum


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
    missing_configs: Dict[str, List[str]]
