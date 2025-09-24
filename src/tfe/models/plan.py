from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ..models.plan_export import PlanExport


class PlanStatus(str, Enum):
    """The status of a plan."""

    PLAN_CANCELED = "canceled"
    PLAN_CREATED = "created"
    PLAN_ERRORED = "errored"
    PLAN_FINISHED = "finished"
    PLAN_MFA_WAITING = "mfa_waiting"
    PLAN_PENDING = "pending"
    PLAN_QUEUED = "queued"
    PLAN_RUNNING = "running"
    PLAN_UNREACHABLE = "unreachable"


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
    exports: list[PlanExport] = Field(..., alias="exports")


class PlanStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    canceled_at: datetime = Field(..., alias="canceled-at")
    errored_at: datetime = Field(..., alias="errored-at")
    finished_at: datetime = Field(..., alias="finished-at")
    force_canceled_at: datetime = Field(..., alias="force-canceled-at")
    queued_at: datetime = Field(..., alias="queued-at")
    started_at: datetime = Field(..., alias="started-at")
