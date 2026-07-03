# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .stack_configuration import StackConfiguration


class DeploymentGroupStatus(str, Enum):
    """DeploymentGroupStatus represents the status of a stack deployment group."""

    PENDING = "pending"
    DEPLOYING = "deploying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABANDONED = "abandoned"


class StackDeploymentGroup(TFEModel):
    """StackDeploymentGroup represents a group of deployment runs for a single deployment.

    JSON:API type: ``stack-deployment-groups``.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    name: str | None = Field(default=None, alias="name")
    status: DeploymentGroupStatus | None = Field(default=None, alias="status")
    created_at: datetime | None = Field(default=None, alias="created-at")
    updated_at: datetime | None = Field(default=None, alias="updated-at")

    # Relations
    stack_configuration: StackConfiguration | None = Field(
        default=None, alias="stack-configuration"
    )


class StackDeploymentGroupListOptions(BaseModel):
    """StackDeploymentGroupListOptions represents the options for listing stack deployment groups."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")


class StackDeploymentGroupRerunOptions(BaseModel):
    """StackDeploymentGroupRerunOptions represents options for rerunning a failed deployment group.

    At least one deployment name must be specified.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    deployments: list[str] = Field(default_factory=list)


class StackDeploymentGroupStatusCounts(BaseModel):
    """StackDeploymentGroupStatusCounts represents the run status counts within a deployment group summary."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    pending: int = Field(default=0, alias="pending")
    pre_deploying: int = Field(default=0, alias="pre-deploying")
    # go-tfe uses "pending-operator" as the wire alias for this field
    pre_deploying_pending_operator: int = Field(default=0, alias="pending-operator")
    acquiring_lock: int = Field(default=0, alias="acquiring-lock")
    deploying: int = Field(default=0, alias="deploying")
    succeeded: int = Field(default=0, alias="succeeded")
    failed: int = Field(default=0, alias="failed")
    abandoned: int = Field(default=0, alias="abandoned")


class StackDeploymentGroupSummary(TFEModel):
    """StackDeploymentGroupSummary represents a lightweight, rolled-up view of a deployment group.

    JSON:API type: ``stack-deployment-group-summaries``.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    name: str | None = Field(default=None, alias="name")
    status: str | None = Field(default=None, alias="status")
    status_counts: StackDeploymentGroupStatusCounts | None = Field(
        default=None, alias="status-counts"
    )

    # Relations
    stack_deployment_group: StackDeploymentGroup | None = Field(
        default=None, alias="stack-deployment-group"
    )


class StackDeploymentGroupSummaryListOptions(BaseModel):
    """StackDeploymentGroupSummaryListOptions represents the options for listing stack deployment group summaries."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
