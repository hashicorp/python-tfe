from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ..models.common import Pagination
from .run_task import Stage, TaskEnforcementLevel

if TYPE_CHECKING:
    from .run_task import RunTask
    from .workspace import Workspace


class RunTaskRelationshipData(BaseModel):
    """Data for a run task relationship."""

    type: str = "tasks"
    id: str


class RunTaskRelationship(BaseModel):
    """Relationship to a run task."""

    data: RunTaskRelationshipData


class WorkspaceRunTask(BaseModel):
    """A workspace run task represents the association between a run task and a workspace."""

    id: str
    type: str = "workspace-tasks"
    enforcement_level: TaskEnforcementLevel
    # Deprecated: Use stages property instead
    stage: Stage | None = None
    # List of stages for the task
    stages: list[Stage] | None = None
    created_at: str | None = None
    updated_at: str | None = None

    # Relationships
    workspace: Workspace | None = None
    run_task: RunTask | None = None


class WorkspaceRunTaskList(BaseModel):
    """A list of workspace run tasks."""

    data: list[WorkspaceRunTask] = Field(default_factory=list)
    pagination: Pagination | None = None


class WorkspaceRunTaskCreateOptions(BaseModel):
    """Options for creating a workspace run task."""

    type: str = "workspace-tasks"
    enforcement_level: TaskEnforcementLevel
    # Deprecated: Use stages property instead
    stage: Stage | None = None
    # Optional: The stages to run the task in
    stages: list[Stage] | None = None
    run_task: RunTaskRelationship


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


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    from .run_task import RunTask  # noqa: F401
    from .workspace import Workspace  # noqa: F401

    WorkspaceRunTask.model_rebuild()


_rebuild_models()
