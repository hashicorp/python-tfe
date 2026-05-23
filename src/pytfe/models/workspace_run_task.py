# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import InvalidRunTaskIDError
from .run_task import (
    RunTask,
    Stage,
    TaskEnforcementLevel,
)
from .workspace import Workspace


class WorkspaceRunTask(BaseModel):
    """Workspace run task model."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    enforcement_level: TaskEnforcementLevel | None = Field(
        default=None, validation_alias="enforcement-level"
    )
    stages: list[Stage] = Field(default_factory=list, alias="stages")
    run_task: RunTask | None = Field(default=None, alias="task")
    workspace: Workspace | None = Field(default=None, alias="workspace")


class WorkspaceRunTaskListOptions(BaseModel):
    """Options for listing workspace run tasks."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")


class WorkspaceRunTaskCreateOptions(BaseModel):
    """Options for creating a workspace run task."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    type: str = Field(default="workspace-tasks")
    enforcement_level: TaskEnforcementLevel = Field(..., alias="enforcement-level")
    run_task: RunTask = Field(..., alias="task")
    stages: list[Stage] | None = Field(default=None, alias="stages")

    @model_validator(mode="after")
    def valid(self) -> WorkspaceRunTaskCreateOptions:
        """Validate the options for creating a workspace run task."""
        if not self.run_task.id:
            raise InvalidRunTaskIDError()
        return self


class WorkspaceRunTaskUpdateOptions(BaseModel):
    """Options for updating a workspace run task."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    type: str = Field(default="workspace-tasks")
    enforcement_level: TaskEnforcementLevel | None = Field(
        default=None, alias="enforcement-level"
    )
    stages: list[Stage] | None = Field(default=None, alias="stages")


# WorkspaceRunTask is now fully defined; rebuild RunTask so Pydantic can
# resolve the forward reference in RunTask.workspace_run_tasks.
RunTask.model_rebuild(raise_errors=False)
