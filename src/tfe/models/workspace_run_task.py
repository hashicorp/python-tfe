from __future__ import annotations

from pydantic import BaseModel


class WorkspaceRunTask(BaseModel):
    id: str
