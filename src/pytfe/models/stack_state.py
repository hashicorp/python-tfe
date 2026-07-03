# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .stack import Stack
from .stack_deployment_run import StackDeploymentRun


class StackStateComponent(BaseModel):
    """StackStateComponent represents a component entry within a stack state.

    This is distinct from :class:`StackComponent` (used in stack-configurations).
    The state variant carries per-instance tracking fields rather than config fields.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    address: str | None = Field(default=None, alias="address")
    component_address: str | None = Field(default=None, alias="component-address")
    instance_correlator: str | None = Field(default=None, alias="instance-correlator")
    component_correlator: str | None = Field(default=None, alias="component-correlator")
    resource_instance_count: int | None = Field(
        default=None, alias="resource-instance-count"
    )


class StackState(TFEModel):
    """StackState represents a captured state for a stack deployment.

    JSON:API type: ``stack-states``.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    generation: int | None = Field(default=None, alias="generation")
    status: str | None = Field(default=None, alias="status")
    deployment: str | None = Field(default=None, alias="deployment")
    components: list[StackStateComponent] = Field(
        default_factory=list, alias="components"
    )
    is_current: bool | None = Field(default=None, alias="is-current")
    resource_instance_count: int | None = Field(
        default=None, alias="resource-instance-count"
    )

    # Relations
    stack: Stack | None = Field(default=None, alias="stack")
    stack_deployment_run: StackDeploymentRun | None = Field(
        default=None, alias="stack-deployment-run"
    )


class StackStateListOptions(BaseModel):
    """StackStateListOptions represents the options for listing stack states."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
