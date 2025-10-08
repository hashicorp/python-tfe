from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .run import Run


class PolicyScope(str, Enum):
    """The scope of the policy check."""

    POLICY_SCOPE_ORGANIZATION = "organization"
    POLICY_SCOPE_WORKSPACE = "workspace"


class PolicyStatus(str, Enum):
    """The status of the policy check."""

    POLICY_CANCELED = "canceled"
    POLICY_ERRORED = "errored"
    POLICY_HARD_FAILED = "hard_failed"
    POLICY_OVERRIDDEN = "overridden"
    POLICY_PASSES = "passed"
    POLICY_PENDING = "pending"
    POLICY_QUEUED = "queued"
    POLICY_SOFT_FAILED = "soft_failed"
    POLICY_UNREACHABLE = "unreachable"


class PolicyCheckIncludeOpt(str, Enum):
    """A list of relations to include"""

    POLICY_CHECK_RUN_WORKSPACE = "run.workspace"
    POLICY_CHECK_RUN = "run"


class PolicyCheck(BaseModel):
    """PolicyCheck represents a Terraform Enterprise policy check."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    actions: PolicyActions | None = Field(None, alias="actions")
    permissions: PolicyPermissions | None = Field(None, alias="permissions")
    result: PolicyResult | None = Field(None, alias="result")
    scope: PolicyScope | None = Field(None, alias="scope")
    status: PolicyStatus | None = Field(None, alias="status")
    status_timestamps: PolicyStatusTimestamps | None = Field(
        None, alias="status-timestamps"
    )

    # Relations
    run: Run | None = Field(None, alias="run")


class PolicyActions(BaseModel):
    """PolicyActions represents the policy check actions."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    is_overridable: bool | None = Field(None, alias="is-overridable")


class PolicyPermissions(BaseModel):
    """PolicyPermissions represents the policy check permissions."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    can_override: bool | None = Field(None, alias="can-override")


class PolicyResult(BaseModel):
    """PolicyResult represents the complete policy check result"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    advisory_failed: int | None = Field(None, alias="advisory-failed")
    duration: int | None = Field(None, alias="duration")
    hard_failed: int | None = Field(None, alias="hard-failed")
    soft_failed: int | None = Field(None, alias="soft-failed")
    total_failed: int | None = Field(None, alias="total-failed")
    passed: int | None = Field(None, alias="passed")
    result: bool | None = Field(None, alias="result")
    sentinel: Any | None = Field(None, alias="sentinel")


class PolicyStatusTimestamps(BaseModel):
    """PolicyStatusTimestamps holds the timestamps for individual policy check statuses."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    errored_at: datetime | None = Field(None, alias="errored-at")
    hard_failed_at: datetime | None = Field(None, alias="hard-failed-at")
    passed_at: datetime | None = Field(None, alias="passed-at")
    queued_at: datetime | None = Field(None, alias="queued-at")
    soft_failed_at: datetime | None = Field(None, alias="soft-failed-at")


class PolicyCheckListOptions(BaseModel):
    """PolicyCheckListOptions represents the options for listing policy checks."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[PolicyCheckIncludeOpt] | None = Field(None, alias="include")
    page_number: int | None = Field(None, alias="page[number]")
    page_size: int | None = Field(None, alias="page[size]")


class PolicyCheckList(BaseModel):
    """PolicyCheckList represents a list of policy checks."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: list[PolicyCheck] = Field(default_factory=list, alias="items")
    current_page: int | None = Field(None, alias="current_page")
    total_pages: int | None = Field(None, alias="total_pages")
    prev_page: int | None = Field(None, alias="prev_page")
    next_page: int | None = Field(None, alias="next_page")
    total_count: int | None = Field(None, alias="total_count")
