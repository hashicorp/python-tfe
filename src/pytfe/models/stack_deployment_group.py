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
