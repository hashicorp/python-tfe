from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ..models.common import Pagination

if TYPE_CHECKING:
    from .run_task import RunTask, Stage, TaskEnforcementLevel
    from .workspace import Workspace


class WorkspaceRunTask(BaseModel):
    """Represents a run task attached to a workspace."""

    id: str
    enforcement_level: TaskEnforcementLevel | None = None
    # Deprecated: Use stages property instead
    stage: Stage | None = None
    stages: list[Stage] = Field(default_factory=list)

    # Relationships
    run_task: RunTask | None = None
    workspace: Workspace | None = None


class WorkspaceRunTaskList(BaseModel):
    """Represents a list of workspace run tasks."""

    items: list[WorkspaceRunTask] = Field(default_factory=list)
    pagination: Pagination | None = None


class WorkspaceRunTaskListOptions(BaseModel):
    """Options for listing workspace run tasks."""

    page_number: int | None = None
    page_size: int | None = None


class WorkspaceRunTaskCreateOptions(BaseModel):
    """Options for creating a workspace run task."""

    type: str = Field(default="workspace-tasks")
    enforcement_level: TaskEnforcementLevel
    run_task: RunTask  # Required
    # Deprecated: Use stages property instead
    stage: Stage | None = None
    stages: list[Stage] | None = None


class WorkspaceRunTaskUpdateOptions(BaseModel):
    """Options for updating a workspace run task."""

    type: str = Field(default="workspace-tasks")
    enforcement_level: TaskEnforcementLevel | None = None
    # Deprecated: Use stages property instead
    stage: Stage | None = None
    stages: list[Stage] | None = None


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    try:
        from .run_task import RunTask, Stage, TaskEnforcementLevel  # noqa: F401
        from .workspace import Workspace  # noqa: F401

        WorkspaceRunTask.model_rebuild()
        WorkspaceRunTaskCreateOptions.model_rebuild()
        WorkspaceRunTaskUpdateOptions.model_rebuild()
    except Exception:
        # Models will rebuild later when first used
        pass


_rebuild_models()
