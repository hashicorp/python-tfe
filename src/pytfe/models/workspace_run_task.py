from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ..models.common import Pagination


class Stage(str, Enum):
    """Task stage options."""

    PRE_PLAN = "pre_plan"
    POST_PLAN = "post_plan"
    PRE_APPLY = "pre_apply"
    POST_APPLY = "post_apply"


class TaskEnforcementLevel(str, Enum):
    """Task enforcement level options."""

    ADVISORY = "advisory"
    MANDATORY = "mandatory"


class WorkspaceRunTask(BaseModel):
    """A workspace run task represents the association between a run task and a workspace."""

    id: str
    type: str = "workspace-tasks"
    enforcement_level: TaskEnforcementLevel
    stage: Stage
    created_at: str | None = None
    updated_at: str | None = None

    # Relationships
    workspace: dict[str, Any] | None = None
    run_task: dict[str, Any] | None = None


class WorkspaceRunTaskList(BaseModel):
    """A list of workspace run tasks."""

    data: list[WorkspaceRunTask] = Field(default_factory=list)
    pagination: Pagination | None = None


class WorkspaceRunTaskCreateOptions(BaseModel):
    """Options for creating a workspace run task."""

    type: str = "workspace-tasks"
    enforcement_level: TaskEnforcementLevel
    stage: Stage | None = None
    run_task: dict[str, Any]  # {"data": {"type": "tasks", "id": "task-123"}}


class WorkspaceRunTaskUpdateOptions(BaseModel):
    """Options for updating a workspace run task."""

    type: str = "workspace-tasks"
    enforcement_level: TaskEnforcementLevel | None = None
    # Deprecated: Use stages property instead
    stage: Stage | None = None
    # Optional: The stages to run the task in
    stages: list[Stage] | None = None


class WorkspaceRunTaskListOptions(BaseModel):
    """Options for listing workspace run tasks."""

    # Pagination
    page_number: int | None = None
    page_size: int | None = None

    # Includes
    include: list[WorkspaceRunTaskIncludeOpt] | None = None


class WorkspaceRunTaskReadOptions(BaseModel):
    """Options for reading a workspace run task."""

    # Includes
    include: list[WorkspaceRunTaskIncludeOpt] | None = None


class WorkspaceRunTaskIncludeOpt(str, Enum):
    """Include options for workspace run task API calls."""

    RUN_TASK = "run_task"
    WORKSPACE = "workspace"
