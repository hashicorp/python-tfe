from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ApplyStatus(str, Enum):
    APPLY_CANCELED = "canceled"
    APPLY_CREATED = "created"
    APPLY_ERRORED = "errored"
    APPLY_FINISHED = "finished"
    APPLY_MFA_WAITING = "mfa_waiting"
    APPLY_PENDING = "pending"
    APPLY_QUEUED = "queued"
    APPLY_RUNNING = "running"
    APPLY_UNREACHABLE = "unreachable"


class Apply(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    log_read_url: str | None = Field(None, alias="log-read-url")
    resource_additions: int | None = Field(None, alias="resource-additions")
    resource_changes: int | None = Field(None, alias="resource-changes")
    resource_destructions: int | None = Field(None, alias="resource-destructions")
    resource_imports: int | None = Field(None, alias="resource-imports")
    status: ApplyStatus | None = Field(None, alias="status")
    status_timestamps: ApplyStatusTimestamps | None = Field(
        None, alias="status-timestamps"
    )


class ApplyStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    canceled_at: datetime | None = Field(None, alias="canceled-at")
    errored_at: datetime | None = Field(None, alias="errored-at")
    finished_at: datetime | None = Field(None, alias="finished-at")
    force_canceled_at: datetime | None = Field(None, alias="force-canceled-at")
    queued_at: datetime | None = Field(None, alias="queued-at")
    started_at: datetime | None = Field(None, alias="started-at")
