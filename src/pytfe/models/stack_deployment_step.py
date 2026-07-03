# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .stack_deployment_run import StackDeploymentRun


class DeploymentStepStatus(str, Enum):
    """DeploymentStepStatus represents the lifecycle status of a stack deployment step."""

    BLOCKED = "blocked"
    ABANDONED = "abandoned"
    QUEUED = "queued"
    RUNNING = "running"
    PENDING_OPERATOR = "pending-operator"
    COMPLETED = "completed"
    FAILED = "failed"


class StackDeploymentStepArtifactType(str, Enum):
    """StackDeploymentStepArtifactType represents the types of downloadable artifacts for a step."""

    PLAN_DESCRIPTION = "plan-description"
    APPLY_DESCRIPTION = "apply-description"
    PLAN_DEBUG_LOG = "plan-debug-log"
    APPLY_DEBUG_LOG = "apply-debug-log"


class StackDeploymentStepIncludeOpt(str, Enum):
    """StackDeploymentStepIncludeOpt represents include options for stack deployment step endpoints."""

    STACK_APPROVAL = "stack_approval"
    STACK_APPROVAL_USER = "stack_approval.user"
    STACK_STATE = "stack_state"


class StackDeploymentStep(TFEModel):
    """StackDeploymentStep represents a single step within a stack deployment run.

    JSON:API type: ``stack-deployment-steps``.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    status: DeploymentStepStatus | None = Field(default=None, alias="status")
    operation_type: str | None = Field(default=None, alias="operation-type")
    created_at: datetime | None = Field(default=None, alias="created-at")
    updated_at: datetime | None = Field(default=None, alias="updated-at")

    # Relations
    stack_deployment_run: StackDeploymentRun | None = Field(
        default=None, alias="stack-deployment-run"
    )


class StackDeploymentStepListOptions(BaseModel):
    """StackDeploymentStepListOptions represents the options for listing stack deployment steps."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    include: list[StackDeploymentStepIncludeOpt] | None = None


class StackDeploymentStepReadOptions(BaseModel):
    """StackDeploymentStepReadOptions represents the options for reading a stack deployment step."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[StackDeploymentStepIncludeOpt] | None = None


class StackDiagnostic(TFEModel):
    """StackDiagnostic represents a diagnostic emitted during a stack deployment step.

    JSON:API type: ``stack-diagnostics``.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    severity: str | None = Field(default=None, alias="severity")
    summary: str | None = Field(default=None, alias="summary")
    detail: str | None = Field(default=None, alias="detail")
    diags: Any | None = Field(default=None, alias="diags")
    acknowledged: bool | None = Field(default=None, alias="acknowledged")
    acknowledged_at: datetime | None = Field(default=None, alias="acknowledged-at")
    created_at: datetime | None = Field(default=None, alias="created-at")


class StackDiagnosticListOptions(BaseModel):
    """StackDiagnosticListOptions represents the options for listing stack diagnostics."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
