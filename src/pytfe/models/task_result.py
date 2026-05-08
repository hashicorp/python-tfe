# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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

    id: str
    status: TaskResultStatus = Field(..., alias="status")
    message: str = Field(..., alias="message")

    status_timestamps: TaskResultStatusTimestamps = Field(
        ..., alias="status-timestamps"
    )

    url: str = Field(..., alias="url")

    created_at: datetime = Field(..., alias="created-at")
    updated_at: datetime = Field(..., alias="updated-at")

    task_id: str = Field(..., alias="task-id")
    task_name: str = Field(..., alias="task-name")
    task_url: str = Field(..., alias="task-url")

    workspace_task_id: str = Field(..., alias="workspace-task-id")
    workspace_task_enforcement_level: TaskEnforcementLevel = Field(
        ..., alias="workspace-task-enforcement-level"
    )

    agent_pool_id: str | None = Field(None, alias="agent-pool-id")
    task_stage: dict | None = Field(None, alias="task-stage")
