# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .configuration_version import IngressAttributes
from .stack import Stack


class StackConfigurationStatus(str, Enum):
    """StackConfigurationStatus represents the status of a stack configuration."""

    PENDING = "pending"
    QUEUED = "queued"
    PREPARING = "preparing"
    COMPLETED = "completed"
    FAILED = "failed"


class StackComponent(BaseModel):
    """StackComponent represents a stack component, specified by configuration"""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    name: str = Field(alias="name", default="")
    correlator: str = Field(alias="correlator", default="")
    expanded: bool | None = Field(alias="expanded", default=None)
    removed: bool | None = Field(alias="removed", default=None)


class StackConfigurationSource(str, Enum):
    """StackConfigurationSource controls how configuration content is sourced."""

    MANUAL = "manual"
    FETCH = "fetch"
    REUSE = "reuse"


class StackConfigurationIncludeOps(str, Enum):
    """StackConfigurationIncludeOps represents include options for stack configuration endpoints."""

    INGRESS_ATTRIBUTES = "ingress_attributes"
    STACK_DIAGNOSTICS = "stack_diagnostics"


class StackConfiguration(TFEModel):
    """StackConfiguration represents a snapshot of a stack's configuration."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    status: StackConfigurationStatus | None = Field(default=None, alias="status")
    sequence_number: int | None = Field(default=None, alias="sequence-number")
    components: list[StackComponent] = Field(default_factory=list, alias="components")
    preparing_event_stream_url: str = Field(
        default="", alias="preparing-event-stream-url"
    )
    created_at: datetime | None = Field(default=None, alias="created-at")
    updated_at: datetime | None = Field(default=None, alias="updated-at")
    speculative: bool | None = Field(default=None, alias="speculative")

    # Relations
    stack: Stack | None = Field(default=None, alias="stack")
    ingress_attributes: IngressAttributes | None = Field(
        default=None, alias="ingress-attributes"
    )


class StackConfigurationCreateOptions(BaseModel):
    """Options for creating a stack configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    speculative_enabled: bool = Field(default=False, alias="speculative")
    destroy_all: bool = Field(default=False, alias="destroy-all")
    selected_deployments: list[str] | None = Field(
        default=None, alias="selected-deployments"
    )


class StackConfigurationListOptions(BaseModel):
    """Options for listing stack configurations."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    include: list[StackConfigurationIncludeOps] | None = None


class StackConfigurationReadOptions(BaseModel):
    """Options for reading a stack configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[StackConfigurationIncludeOps] | None = None
