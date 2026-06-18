# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import RequiredPlanError
from ..utils import valid_string_id
from ._base import TFEModel


class PlanExportDataType(str, Enum):
    """Export format. Currently only the Sentinel mock bundle is supported."""

    SENTINEL_MOCK_BUNDLE_V0 = "sentinel-mock-bundle-v0"


class PlanExportStatus(str, Enum):
    """Lifecycle status of a plan export."""

    CANCELED = "canceled"
    ERRORED = "errored"
    EXPIRED = "expired"
    FINISHED = "finished"
    PENDING = "pending"
    QUEUED = "queued"


class PlanExportStatusTimestamps(BaseModel):
    """Timestamps for plan-export status transitions.

    Only the timestamps for statuses the export has actually reached are
    returned, so every field is optional.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    canceled_at: datetime | None = Field(default=None, alias="canceled-at")
    errored_at: datetime | None = Field(default=None, alias="errored-at")
    expired_at: datetime | None = Field(default=None, alias="expired-at")
    finished_at: datetime | None = Field(default=None, alias="finished-at")
    queued_at: datetime | None = Field(default=None, alias="queued-at")


class PlanExport(TFEModel):
    """An export of Terraform plan data (e.g. a Sentinel mock bundle)."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    data_type: PlanExportDataType | None = Field(default=None, alias="data-type")
    status: PlanExportStatus | None = Field(default=None, alias="status")
    status_timestamps: PlanExportStatusTimestamps | None = Field(
        default=None, alias="status-timestamps"
    )


class PlanExportCreateOptions(BaseModel):
    """Options for exporting data from a finished plan."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )

    plan_id: str = Field(
        ..., description="ID of the finished plan to export (a `plans` resource)."
    )
    data_type: PlanExportDataType = Field(
        default=PlanExportDataType.SENTINEL_MOCK_BUNDLE_V0, alias="data-type"
    )

    @model_validator(mode="after")
    def valid(self) -> PlanExportCreateOptions:
        if not valid_string_id(self.plan_id):
            raise RequiredPlanError()
        return self
