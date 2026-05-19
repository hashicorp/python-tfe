# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..errors import InvalidRunTaskIDError


def _normalize_stage_value(value: str) -> str:
    """Normalize stage names to the API's underscore format."""
    return value.replace("-", "_")


class WorkspaceRunTaskRunTask(BaseModel):
    """Relationship model for run task references."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Run task ID")


class WorkspaceRunTaskWorkspace(BaseModel):
    """Relationship model for workspace references."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Workspace ID")


class WorkspaceRunTask(BaseModel):
    """Workspace run task model."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    enforcement_level: str | None = Field(None, alias="enforcement-level")
    stage: str | None = Field(None, alias="stage")
    stages: list[str] = Field(default_factory=list, alias="stages")
    run_task: WorkspaceRunTaskRunTask | None = Field(None, alias="run-task")
    workspace: WorkspaceRunTaskWorkspace | None = Field(None, alias="workspace")

    @field_validator("stage", mode="before")
    @classmethod
    def normalize_stage(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_stage_value(value)

    @field_validator("stages", mode="before")
    @classmethod
    def normalize_stages(cls, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return [_normalize_stage_value(item) for item in value]


class WorkspaceRunTaskListOptions(BaseModel):
    """Options for listing workspace run tasks."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    page_number: int | None = Field(default=None, alias="page[number]")
    page_size: int | None = Field(default=None, alias="page[size]")


class WorkspaceRunTaskCreateOptions(BaseModel):
    """Options for creating a workspace run task."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: str = Field(default="workspace-tasks")
    enforcement_level: str = Field(..., alias="enforcement-level")
    run_task: WorkspaceRunTaskRunTask = Field(..., alias="run-task")
    stage: str | None = Field(default=None, alias="stage")
    stages: list[str] | None = Field(default=None, alias="stages")

    def validate_for_create(self) -> None:
        """Validate create options."""
        if not self.run_task.id:
            raise InvalidRunTaskIDError()

    @field_validator("stage", mode="before")
    @classmethod
    def normalize_stage(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_stage_value(value)

    @field_validator("stages", mode="before")
    @classmethod
    def normalize_stages(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [_normalize_stage_value(item) for item in value]


class WorkspaceRunTaskUpdateOptions(BaseModel):
    """Options for updating a workspace run task."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: str = Field(default="workspace-tasks")
    enforcement_level: str | None = Field(default=None, alias="enforcement-level")
    stages: list[str] | None = Field(default=None, alias="stages")
