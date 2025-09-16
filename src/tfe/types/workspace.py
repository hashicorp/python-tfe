from __future__ import annotations

from typing import TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .execution import ExecutionMode

__all__ = [
    "Workspace",
]


class Workspace(BaseModel):
    id: str
    name: str
    organization: str
    execution_mode: ExecutionMode | None = None
    project_id: str | None = None
    tags: list[str] = Field(default_factory=list)