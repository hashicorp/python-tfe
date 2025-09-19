from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from ..types import Pagination
from .workspace import Workspace


class RunTrigger(BaseModel):
    id: str
    type: str = Field(default="run-triggers")
    created_at: datetime
    sourceable_name: str
    workspace_name: str

    sourceable: Workspace
    sourceable_choice: SourceableChoice
    workspace: Workspace


class RunTriggerListOptions(BaseModel):
    page_number: int | None = Field(default=1)
    page_size: int | None = Field(default=20)
    run_trigger_type: RunTriggerFilterOp
    include: list[RunTriggerIncludeOp] | None = Field(default_factory=list)


class RunTriggerCreateOptions(BaseModel):
    type: str = Field(default="run-triggers")
    sourceable: Workspace


class RunTriggerList(BaseModel):
    items: list[RunTrigger]
    pagination: Pagination


class SourceableChoice(BaseModel):
    workspace: Workspace


class RunTriggerFilterOp(str, Enum):
    RUN_TRIGGER_OUTBOUND = "outbound"
    RUN_TRIGGER_INBOUND = "inbound"


class RunTriggerIncludeOp(str, Enum):
    RUN_TRIGGER_WORKSPACE = "workspace"
    RUN_TRIGGER_SOURCEABLE = "sourceable"
