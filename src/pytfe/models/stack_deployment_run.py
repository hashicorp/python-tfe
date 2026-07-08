# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .stack_deployment_group import StackDeploymentGroup


class DeploymentRunStatus(str, Enum):
    """DeploymentRunStatus represents the lifecycle status of a stack deployment run."""

    PENDING = "pending"
    PRE_DEPLOYING = "pre-deploying"
    PRE_DEPLOYING_PENDING_OPERATOR = "pre-deploying-pending-operator"
    ACQUIRING_LOCK = "acquiring-lock"
    DEPLOYING = "deploying"
    DEPLOYING_PENDING_OPERATOR = "deploying-pending-operator"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABANDONED = "abandoned"


class StackDeploymentRunIncludeOpt(str, Enum):
    """StackDeploymentRunIncludeOpt represents include options for stack deployment run endpoints.

    ``LATEST_DEPLOYMENT_RUN_FOR_DEPLOYMENT`` is only valid on read (show) endpoints;
    the remaining values are valid on both list and read.
    """

    STACK_DEPLOYMENT_GROUP = "stack_deployment_group"
    STACK_APPROVAL = "stack_approval"
    DESTROY_STACK_CONFIGURATION = "destroy_stack_configuration"
    BLOCKED_BY_DEPLOYMENT_GROUP = "blocked_by_deployment_group"
    LATEST_DEPLOYMENT_RUN_FOR_DEPLOYMENT = "latest_deployment_run_for_deployment"


class StackDeploymentRun(TFEModel):
    """StackDeploymentRun represents a single deployment run within a deployment group.

    JSON:API type: ``stack-deployment-runs``.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    deployment: str | None = Field(default=None, alias="deployment")
    status: DeploymentRunStatus | None = Field(default=None, alias="status")
    created_at: datetime | None = Field(default=None, alias="created-at")
    updated_at: datetime | None = Field(default=None, alias="updated-at")

    # Relations
    stack_deployment_group: StackDeploymentGroup | None = Field(
        default=None, alias="stack-deployment-group"
    )


class StackDeploymentRunListOptions(BaseModel):
    """StackDeploymentRunListOptions represents the options for listing stack deployment runs."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    include: list[StackDeploymentRunIncludeOpt] | None = None


class StackDeploymentRunReadOptions(BaseModel):
    """StackDeploymentRunReadOptions represents the options for reading a stack deployment run."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[StackDeploymentRunIncludeOpt] | None = None
