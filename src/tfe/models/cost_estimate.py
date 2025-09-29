from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CostEstimate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    delta_monthly_cost: str = Field(..., alias="delta-monthly-cost")
    error_message: str = Field(..., alias="error-message")
    matched_resources_count: int = Field(..., alias="matched-resources-count")
    prior_monthly_cost: str = Field(..., alias="prior-monthly-cost")
    proposed_monthly_cost: str = Field(..., alias="proposed-monthly-cost")
    resources_count: int = Field(..., alias="resources-count")
    status: CostEstimateStatus = Field(..., alias="status")
    status_timestamps: CostEstimateStatusTimestamps = Field(
        ..., alias="status-timestamps"
    )
    unmatched_resources_count: int = Field(..., alias="unmatched-resources-count")


class CostEstimateStatus(str, Enum):
    Cost_Estimate_Canceled = "canceled"
    Cost_Estimate_Errored = "errored"
    Cost_Estimate_Finished = "finished"
    Cost_Estimate_Pending = "pending"
    Cost_Estimate_Queued = "queued"
    Cost_Estimate_Skipped_Due_To_Targeting = "skipped_due_to_targeting"


class CostEstimateStatusTimestamps(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    canceled_at: datetime = Field(..., alias="canceled-at")
    errored_at: datetime = Field(..., alias="errored-at")
    finished_at: datetime = Field(..., alias="finished-at")
    queued_at: datetime = Field(..., alias="queued-at")
    skipped_due_to_targeting_at: datetime = Field(
        ..., alias="skipped-due-to-targeting-at"
    )
