from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PlanStatus(str, Enum):
    Plan_Canceled = "canceled"
    Plan_Created = "created"
    Plan_Errored = "errored"
    Plan_Finished = "finished"
    Plan_MFA_Waiting = "mfa_waiting"
    Plan_Pending = "pending"
    Plan_Queued = "queued"
    Plan_Running = "running"
    Plan_Unreachable = "unreachable"


class Plan(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    has_changes: bool = Field(..., alias="has-changes")
    generated_configuration: bool = Field(..., alias="generated-configuration")
    log_read_url: str = Field(..., alias="log-read-url")
    resource_additions: int = Field(..., alias="resource-additions")
    resource_changes: int = Field(..., alias="resource-changes")
    resource_destructions: int = Field(..., alias="resource-destructions")
    resource_imports: int = Field(..., alias="resource-imports")
    status: PlanStatus = Field(..., alias="status")
    status_timestamps: PlanStatusTimestamps = Field(..., alias="status-timestamps")

    # Relations
    # exports: list[PlanExport] = Field(..., alias="exports")


class PlanStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    canceled_at: datetime = Field(..., alias="canceled-at")
    errored_at: datetime = Field(..., alias="errored-at")
    finished_at: datetime = Field(..., alias="finished-at")
    force_canceled_at: datetime = Field(..., alias="force-canceled-at")
    queued_at: datetime = Field(..., alias="queued-at")
    started_at: datetime = Field(..., alias="started-at")
