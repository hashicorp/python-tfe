# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# Reuse, do NOT duplicate
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
    model_config = ConfigDict(populate_by_name=True)

    errored_at: Optional[datetime] = Field(None, alias="errored-at")
    running_at: Optional[datetime] = Field(None, alias="running-at")
    canceled_at: Optional[datetime] = Field(None, alias="canceled-at")
    failed_at: Optional[datetime] = Field(None, alias="failed-at")
    passed_at: Optional[datetime] = Field(None, alias="passed-at")


class TaskResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str

    status: Optional[TaskResultStatus] = Field(None, alias="status")
    message: Optional[str] = Field(None, alias="message")

    status_timestamps: Optional[TaskResultStatusTimestamps] = Field(
        None, alias="status-timestamps"
    )

    url: Optional[str] = Field(None, alias="url")

    created_at: Optional[datetime] = Field(None, alias="created-at")
    updated_at: Optional[datetime] = Field(None, alias="updated-at")

    task_id: Optional[str] = Field(None, alias="task-id")
    task_name: Optional[str] = Field(None, alias="task-name")
    task_url: Optional[str] = Field(None, alias="task-url")

    workspace_task_id: Optional[str] = Field(None, alias="workspace-task-id")
    workspace_task_enforcement_level: Optional[TaskEnforcementLevel] = Field(
        None, alias="workspace-task-enforcement-level"
    )

    agent_pool_id: Optional[str] = Field(None, alias="agent-pool-id")

    # Relation (matches Go: *TaskStage)
    task_stage: Optional[TaskStage] = Field(None, alias="task-stage")