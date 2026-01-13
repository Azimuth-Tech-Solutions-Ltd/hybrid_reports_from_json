from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict

class ModelInfo(BaseModel):
    provider: str
    model_name: str
    temperature: float

class SectionOutput(BaseModel):
    section_name: str
    version: str
    model: ModelInfo
    data: Dict[str, Any]
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

