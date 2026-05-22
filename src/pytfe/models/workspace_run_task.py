# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..errors import InvalidRunTaskIDError
from .workspace import Workspace


def _normalize_stage_value(value: str) -> str:
    """Normalize stage names to the API's underscore format."""
    return value.replace("-", "_")


class WorkspaceRunTaskStage(str, Enum):
    PRE_PLAN = "pre_plan"
    POST_PLAN = "post_plan"
    PRE_APPLY = "pre_apply"
    POST_APPLY = "post_apply"


class WorkspaceRunTaskEnforcementLevel(str, Enum):
    ADVISORY = "advisory"
    MANDATORY = "mandatory"


class RunTaskReference(BaseModel):
    """Reference model for run task relationships."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str = Field(..., description="Run task ID")


class WorkspaceRunTask(BaseModel):
    """Workspace run task model."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    enforcement_level: WorkspaceRunTaskEnforcementLevel | None = Field(
        default=None, validation_alias="enforcement-level"
    )
    stages: list[WorkspaceRunTaskStage] = Field(
        default_factory=list, validation_alias="stages"
    )
    run_task: RunTaskReference | None = Field(
        default=None, validation_alias="run-task"
    )
    workspace: Workspace | None = Field(
        default=None, validation_alias="workspace"
    )

    @field_validator("stages", mode="before")
    @classmethod
    def normalize_stages(
        cls, value: list[str | WorkspaceRunTaskStage] | None
    ) -> list[str]:
        if value is None:
            return []
        return [
            _normalize_stage_value(item.value if isinstance(item, WorkspaceRunTaskStage) else item)
            for item in value
        ]


class WorkspaceRunTaskListOptions(BaseModel):
    """Options for listing workspace run tasks."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")


class WorkspaceRunTaskCreateOptions(BaseModel):
    """Options for creating a workspace run task."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    type: str = Field(default="workspace-tasks")
    enforcement_level: WorkspaceRunTaskEnforcementLevel = Field(
        ..., alias="enforcement-level"
    )
    run_task: RunTaskReference = Field(..., alias="run-task")
    stages: list[WorkspaceRunTaskStage] | None = Field(default=None, alias="stages")

    @field_validator("run_task", mode="before")
    @classmethod
    def normalize_run_task(
        cls, value: RunTaskReference | dict | str
    ) -> RunTaskReference | dict | str:
        if isinstance(value, RunTaskReference):
            return value
        if isinstance(value, str):
            return RunTaskReference(id=value)
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            return RunTaskReference(id=value["id"])
        return value

    def validate_for_create(self) -> None:
        """Validate create options."""
        if not self.run_task.id:
            raise InvalidRunTaskIDError()

    @field_validator("stages", mode="before")
    @classmethod
    def normalize_stages(
        cls, value: list[str | WorkspaceRunTaskStage] | None
    ) -> list[str] | None:
        if value is None:
            return None
        return [
            _normalize_stage_value(item.value if isinstance(item, WorkspaceRunTaskStage) else item)
            for item in value
        ]


class WorkspaceRunTaskUpdateOptions(BaseModel):
    """Options for updating a workspace run task."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    type: str = Field(default="workspace-tasks")
    enforcement_level: WorkspaceRunTaskEnforcementLevel | None = Field(
        default=None, alias="enforcement-level"
    )
    stages: list[WorkspaceRunTaskStage] | None = Field(default=None, alias="stages")

    @field_validator("stages", mode="before")
    @classmethod
    def normalize_stages(
        cls, value: list[str | WorkspaceRunTaskStage] | None
    ) -> list[str] | None:
        if value is None:
            return None
        return [
            _normalize_stage_value(
                item.value if isinstance(item, WorkspaceRunTaskStage) else item
            )
            for item in value
        ]

