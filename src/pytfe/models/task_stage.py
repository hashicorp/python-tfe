# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from pytfe.models.policy_evaluation import PolicyEvaluation
from pytfe.models.task_result import TaskResult

if TYPE_CHECKING:
    from pytfe.models.run import Run


class Stage(str, Enum):
    pre_plan = "pre_plan"
    post_plan = "post_plan"
    pre_apply = "pre_apply"
    post_apply = "post_apply"


class TaskStageStatus(str, Enum):
    pending = "pending"
    running = "running"
    passed = "passed"
    failed = "failed"
    awaiting_override = "awaiting_override"
    canceled = "canceled"
    errored = "errored"
    unreachable = "unreachable"


class TaskStageStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    errored_at: datetime | None = Field(None, alias="errored-at")
    running_at: datetime | None = Field(None, alias="running-at")
    canceled_at: datetime | None = Field(None, alias="canceled-at")
    failed_at: datetime | None = Field(None, alias="failed-at")
    passed_at: datetime | None = Field(None, alias="passed-at")


class Permissions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    can_override_policy: bool | None = Field(None, alias="can-override-policy")
    can_override_tasks: bool | None = Field(None, alias="can-override-tasks")
    can_override: bool | None = Field(None, alias="can-override")


class Actions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    is_overridable: bool | None = Field(None, alias="is-overridable")


class TaskStage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str

    stage: Stage | None = Field(None, alias="stage")
    status: TaskStageStatus | None = Field(None, alias="status")
    status_timestamps: TaskStageStatusTimestamps | None = Field(
        None, alias="status-timestamps"
    )
    created_at: datetime | None = Field(None, alias="created-at")
    updated_at: datetime | None = Field(None, alias="updated-at")
    permissions: Permissions | None = Field(None, alias="permissions")
    actions: Actions | None = Field(None, alias="actions")

    # Relationships
    run: Run | None = Field(None, alias="run")
    task_results: list[TaskResult] | None = Field(None, alias="task-results")
    policy_evaluations: list[PolicyEvaluation] | None = Field(
        None, alias="policy-evaluations"
    )


def _rebuild_task_stage_model() -> None:
    TaskStage.model_rebuild(
        raise_errors=False,
        _types_namespace={
            "TaskResult": TaskResult,
            "PolicyEvaluation": PolicyEvaluation,
        },
    )


_rebuild_task_stage_model()
