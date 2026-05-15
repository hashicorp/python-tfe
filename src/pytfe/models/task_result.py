# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    # Imported only for type checking to avoid a circular import:
    # task_stage.py already imports TaskResult.
    from pytfe.models.task_stage import TaskStage


class TaskResultStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    pending = "pending"
    running = "running"
    unreachable = "unreachable"
    errored = "errored"


class TaskEnforcementLevel(str, Enum):
    advisory = "advisory"
    mandatory = "mandatory"


class TaskResultStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    errored_at: datetime | None = Field(None, alias="errored-at")
    running_at: datetime | None = Field(None, alias="running-at")
    canceled_at: datetime | None = Field(None, alias="canceled-at")
    failed_at: datetime | None = Field(None, alias="failed-at")
    passed_at: datetime | None = Field(None, alias="passed-at")


class TaskResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # All non-id fields are optional so JSON:API relationship references
    # ({id, type} only) can be hydrated as TaskResult stubs without raising
    # "field required" validation errors.
    id: str
    status: TaskResultStatus | None = Field(None, alias="status")
    message: str | None = Field(None, alias="message")

    status_timestamps: TaskResultStatusTimestamps | None = Field(
        None, alias="status-timestamps"
    )

    url: str | None = Field(None, alias="url")

    created_at: datetime | None = Field(None, alias="created-at")
    updated_at: datetime | None = Field(None, alias="updated-at")

    task_id: str | None = Field(None, alias="task-id")
    task_name: str | None = Field(None, alias="task-name")
    task_url: str | None = Field(None, alias="task-url")

    workspace_task_id: str | None = Field(None, alias="workspace-task-id")
    workspace_task_enforcement_level: TaskEnforcementLevel | None = Field(
        None, alias="workspace-task-enforcement-level"
    )

    agent_pool_id: str | None = Field(None, alias="agent-pool-id")
    # Forward-referenced to avoid circular import; resolved lazily below.
    task_stage: TaskStage | None = Field(None, alias="task-stage")

    @classmethod
    def model_validate(cls, *args: Any, **kwargs: Any) -> TaskResult:
        # Ensure the TaskStage forward reference is resolved before validating.
        # The import-time rebuild may run while task_stage.py is still
        # partially loaded (circular import), in which case we retry here.
        if not getattr(cls, "__pydantic_complete__", True):
            _rebuild_task_result_model()
        return super().model_validate(*args, **kwargs)


def _rebuild_task_result_model() -> None:
    # Resolve the TaskStage forward reference once both modules are loaded.
    try:
        from pytfe.models.task_stage import TaskStage

        TaskResult.model_rebuild(
            raise_errors=False,
            _types_namespace={"TaskStage": TaskStage},
        )
    except Exception:
        # TaskStage not yet importable during partial init; safe to skip.
        pass


_rebuild_task_result_model()
