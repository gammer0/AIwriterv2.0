from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Scene(BaseModel):
    index: int
    text: str
    prompt: str


class GenerateResponse(BaseModel):
    scenes: List[Scene] = Field(default_factory=list)
    consistency_notes: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
