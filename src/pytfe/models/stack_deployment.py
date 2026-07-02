# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .stack import Stack


class StackDeploymentIncludeOpt(str, Enum):
    """StackDeploymentIncludeOpt represents include options for stack deployment endpoints."""

    LATEST_DEPLOYMENT_RUN = "latest_deployment_run"
    LATEST_DEPLOYMENT_RUN_STACK_CONFIGURATION = (
        "latest_deployment_run.stack_configuration"
    )


class StackDeployment(TFEModel):
    """StackDeployment represents a deployment that belongs to a stack.

    JSON:API type: ``stack-deployments``.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    name: str | None = Field(default=None, alias="name")

    # Relations
    stack: Stack | None = Field(default=None, alias="stack")


class StackDeploymentListOptions(BaseModel):
    """StackDeploymentListOptions represents the options for listing stack deployments."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    include: list[StackDeploymentIncludeOpt] | None = None
