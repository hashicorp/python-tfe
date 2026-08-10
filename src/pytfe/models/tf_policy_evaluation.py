# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .policy_types import TfPolicyEvaluationStatus, TfPolicyStage


class TfPolicyEvaluationStatusTimestamps(BaseModel):
    """Per-state timestamps recorded as a tf-policy evaluation progresses."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    pending_at: datetime | None = Field(None, alias="pending-at")
    queued_at: datetime | None = Field(None, alias="queued-at")
    running_at: datetime | None = Field(None, alias="running-at")
    awaiting_override_at: datetime | None = Field(None, alias="awaiting-override-at")
    passed_at: datetime | None = Field(None, alias="passed-at")
    failed_at: datetime | None = Field(None, alias="failed-at")
    overridden_at: datetime | None = Field(None, alias="overridden-at")
    errored_at: datetime | None = Field(None, alias="errored-at")
    canceled_at: datetime | None = Field(None, alias="canceled-at")


class TfPolicyResultCount(BaseModel):
    """Aggregated result counts across all policy-set outcomes in an evaluation."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    advisory_failed: int | None = Field(None, alias="advisory-failed")
    mandatory_failed: int | None = Field(None, alias="mandatory-failed")
    passed: int | None = Field(None, alias="passed")
    errored: int | None = Field(None, alias="errored")
    unknown: int | None = Field(None, alias="unknown")


class TfPolicyEvaluationError(BaseModel):
    """Evaluation-level error object (``null`` when no error occurred)."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    type: str | None = Field(None, alias="type")
    summary: str | None = Field(None, alias="summary")
    detail: str | None = Field(None, alias="detail")


class TfPolicyEvaluationPermissions(BaseModel):
    """Caller permissions for a tf-policy evaluation."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    can_override: bool | None = Field(None, alias="can-override")


class TfPolicyEvaluationActions(BaseModel):
    """Available actions for a tf-policy evaluation."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    is_overridable: bool | None = Field(None, alias="is-overridable")


class TfPolicyEvaluation(TFEModel):
    """A tf-policy evaluation attached to a run stage."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    status: TfPolicyEvaluationStatus | None = Field(None, alias="status")
    stage_type: TfPolicyStage | None = Field(None, alias="stage-type")
    status_timestamps: TfPolicyEvaluationStatusTimestamps | None = Field(
        None, alias="status-timestamps"
    )
    result_count: TfPolicyResultCount | None = Field(None, alias="result-count")
    error: TfPolicyEvaluationError | None = Field(None, alias="error")
    permissions: TfPolicyEvaluationPermissions | None = Field(None, alias="permissions")
    actions: TfPolicyEvaluationActions | None = Field(None, alias="actions")
    created_at: datetime | None = Field(None, alias="created-at")
    updated_at: datetime | None = Field(None, alias="updated-at")


class TfPolicyEvaluationListOptions(BaseModel):
    """Options for listing tf-policy evaluations under a run."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]")
    page_number: int | None = Field(None, alias="page[number]")
    include: str | None = Field(None, alias="include")


class TfPolicyEvaluationOverrideOptions(BaseModel):
    """Options for overriding a tf-policy evaluation in ``awaiting_override`` status."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    comment: str | None = None
