from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .policy_types import PolicyKind


class PolicyEvaluationStatus(str, Enum):
    """PolicyEvaluationStatus is an enum that represents all possible statuses for a policy evaluation"""

    POLICYEVALUATIONPASSED = "passed"
    POLICYEVALUATIONFAILED = "failed"
    POLICYEVALUATIONPENDING = "pending"
    POLICYEVALUATIONRUNNING = "running"
    POLICYEVALUATIONCANCELED = "canceled"
    POLICYEVALUATIONERRORED = "errored"
    POLICYEVALUATIONUNREACHABLE = "unreachable"
    POLICYEVALUATIONOVERRIDDEN = "overridden"


class PolicyEvaluation(BaseModel):
    """PolicyEvaluation represents the policy evaluations that are part of the task stage."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    status: PolicyEvaluationStatus | None = Field(None, alias="status")
    policy_kind: PolicyKind | None = Field(None, alias="policy-kind")
    status_timestamp: PolicyEvaluationStatusTimestamps | None = Field(
        None, alias="status-timestamp"
    )
    result_count: PolicyResultCount | None = Field(None, alias="result-count")
    created_at: datetime | None = Field(None, alias="created-at")
    updated_at: datetime | None = Field(None, alias="updated-at")

    # The task stage the policy evaluation belongs to
    policy_attachable: PolicyAttachable | None = Field(None, alias="policy-attachable")


class PolicyEvaluationStatusTimestamps(BaseModel):
    """PolicyEvaluationStatusTimestamps represents the set of timestamps recorded for a policy evaluation"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    passed_at: datetime | None = Field(None, alias="passed-at")
    failed_at: datetime | None = Field(None, alias="failed-at")
    running_at: datetime | None = Field(None, alias="running-at")
    canceled_at: datetime | None = Field(None, alias="canceled-at")
    errored_at: datetime | None = Field(None, alias="errored-at")


class PolicyAttachable(BaseModel):
    """The task stage the policy evaluation belongs to"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    type: str | None = Field(None, alias="type")


class PolicyResultCount(BaseModel):
    """PolicyResultCount represents the count of the policy results"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    advisory_failed: int | None = Field(None, alias="advisory-failed")
    mandatory_failed: int | None = Field(None, alias="mandatory-failed")
    passed: int | None = Field(None, alias="passed")
    errored: int | None = Field(None, alias="errored")


class PolicyEvaluationListOptions(BaseModel):
    """PolicyEvaluationListOptions represents the options for listing policy evaluations"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]")
