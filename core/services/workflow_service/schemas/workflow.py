from pydantic import BaseModel
from typing import List, Dict


class WorfklowValidationError(BaseModel):
    project_id: str
    missing_configs: Dict[str, List[str]]
