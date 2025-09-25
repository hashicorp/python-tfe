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
    has_changes: bool | None = Field(None, alias="has-changes")
    generated_configuration: bool | None = Field(None, alias="generated-configuration")
    log_read_url: str | None = Field(None, alias="log-read-url")
    resource_additions: int | None = Field(None, alias="resource-additions")
    resource_changes: int | None = Field(None, alias="resource-changes")
    resource_destructions: int | None = Field(None, alias="resource-destructions")
    resource_imports: int | None = Field(None, alias="resource-imports")
    status: PlanStatus | None = Field(None, alias="status")
    status_timestamps: PlanStatusTimestamps | None = Field(
        None, alias="status-timestamps"
    )

    # Relations
    exports: list[PlanExport] | None = Field(None, alias="exports")


class PlanStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    canceled_at: datetime | None = Field(None, alias="canceled-at")
    errored_at: datetime | None = Field(None, alias="errored-at")
    finished_at: datetime | None = Field(None, alias="finished-at")
    force_canceled_at: datetime | None = Field(None, alias="force-canceled-at")
    queued_at: datetime | None = Field(None, alias="queued-at")
    started_at: datetime | None = Field(None, alias="started-at")
