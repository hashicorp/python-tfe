from __future__ import annotations

from pydantic import BaseModel, Field

from .organization import ExecutionMode


class Workspace(BaseModel):
    id: str
    name: str
    organization: str
    execution_mode: ExecutionMode | None = None
    project_id: str | None = None
    tags: list[str] = Field(default_factory=list)
