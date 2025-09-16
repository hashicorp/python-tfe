from __future__ import annotations

from pydantic import BaseModel

__all__ = [
    "Project",
]


class Project(BaseModel):
    id: str
    name: str
    organization: str