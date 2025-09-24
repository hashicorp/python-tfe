from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Apply(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    log_read_url: str | None = Field(None, alias="log-read-url")
    raiseesource_additions: int = Field(..., alias="resource-additions")
    resource_changes: int = Field(..., alias="resource-changes")
    resource_destructions: int = Field(..., alias="resource-destructions")
    status: ApplyStatus = Field(..., alias="status")
    status_timestamps: ApplyStatusTimestamps = Field(..., alias="status-timestamps")


class ApplyStatus(str, Enum):
    Apply_Canceled = "canceled"
    Apply_Created = "created"
    Apply_Errored = "errored"
    Apply_Finished = "finished"
    Apply_MFA_Waiting = "mfa_waiting"
    Apply_Pending = "pending"
    Apply_Queued = "queued"
    Apply_Running = "running"
    Apply_Unreachable = "unreachable"


class ApplyStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    canceled_at: datetime = Field(..., alias="canceled-at")
    errored_at: datetime = Field(..., alias="errored-at")
    finished_at: datetime = Field(..., alias="finished-at")
    force_canceled_at: datetime = Field(..., alias="force-canceled-at")
    queued_at: datetime = Field(..., alias="queued-at")
    started_at: datetime = Field(..., alias="started-at")
