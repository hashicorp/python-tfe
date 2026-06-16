# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel

if TYPE_CHECKING:
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
    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    errored_at: datetime | None = Field(None, alias="errored-at")
    running_at: datetime | None = Field(None, alias="running-at")
    canceled_at: datetime | None = Field(None, alias="canceled-at")
    failed_at: datetime | None = Field(None, alias="failed-at")
    passed_at: datetime | None = Field(None, alias="passed-at")


class TaskResult(TFEModel):
    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

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
    # relations
    task_stage: TaskStage | None = Field(None, alias="task-stage")
