# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Agent and Agent Pool models for the Python TFE SDK.

This module contains Pydantic models for Terraform Enterprise/Cloud agents and agent pools,
including all necessary option classes for CRUD operations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import (
    InvalidNameError,
    RequiredNameError,
)
from ..utils import valid_string, valid_string_id
from .organization import Organization
from .workspace import Workspace

if TYPE_CHECKING:
    from .project import Project


class AgentStatus(str, Enum):
    """Agent status enumeration."""

    IDLE = "idle"
    BUSY = "busy"
    UNKNOWN = "unknown"


class Agent(BaseModel):
    """Agent represents a Terraform Enterprise agent."""

    id: str
    name: str | None = None
    status: AgentStatus | None = None
    version: str | None = None
    last_ping_at: datetime | None = None
    ip_address: str | None = None

    # Relations
    agent_pool: AgentPool | None = None


class AgentPool(BaseModel):
    """Agent Pool represents a Terraform Enterprise agent pool."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    name: str | None = Field(default=None, alias="name")
    created_at: datetime | None = Field(default=None, alias="created-at")
    organization_scoped: bool | None = Field(default=None, alias="organization-scoped")
    agent_count: int | None = Field(default=None, alias="agent-count")

    # Relations
    organization: Organization | None = Field(default=None, alias="organization")
    workspaces: list[Workspace] = Field(default_factory=list, alias="workspaces")
    agents: list[Agent] = Field(default_factory=list)
    allowed_workspaces: list[Workspace] = Field(
        default_factory=list, alias="allowed-workspaces"
    )
    excluded_workspaces: list[Workspace] = Field(
        default_factory=list, alias="excluded-workspaces"
    )
    allowed_projects: list[Project] = Field(
        default_factory=list, alias="allowed-projects"
    )


class AgentPoolIncludeOpt(str, Enum):
    AGENT_POOL_WORKSPACES = "workspaces"


class AgentPoolListOptions(BaseModel):
    """Options for listing agent pools."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    # Optional: Include related resources
    include: list[AgentPoolIncludeOpt] | None = Field(default=None, alias="include")
    query: str | None = Field(default=None, alias="q")
    allowed_workspace_name: str | None = Field(
        default=None, alias="filter[allowed_workspaces][name]"
    )
    allowed_project_name: str | None = Field(
        default=None, alias="filter[allowed_projects][name]"
    )
    sort: str | None = Field(default=None, alias="sort")


class AgentPoolCreateOptions(BaseModel):
    """Options for creating an agent pool."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Required: A name to identify the agent pool
    name: str = Field(alias="name")
    organization_scoped: bool | None = Field(default=None, alias="organization-scoped")
    allowed_workspace_ids: list[str] | None = Field(
        default=None, alias="allowed-workspaces"
    )
    excluded_workspace_ids: list[str] | None = Field(
        default=None, alias="excluded-workspaces"
    )
    allowed_project_ids: list[str] | None = Field(
        default=None, alias="allowed-projects"
    )

    @model_validator(mode="after")
    def valid(self) -> AgentPoolCreateOptions:
        """Validate the options for creating an agent pool."""
        if not valid_string(self.name):
            raise RequiredNameError()
        if not valid_string_id(self.name):
            raise InvalidNameError()

        return self


class AgentPoolUpdateOptions(BaseModel):
    """Options for updating an agent pool."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Optional: A name to identify the agent pool
    name: str | None = Field(default=None, alias="name")
    organization_scoped: bool | None = Field(default=None, alias="organization-scoped")
    allowed_workspace_ids: list[str] | None = Field(
        default=None, alias="allowed-workspaces"
    )
    excluded_workspace_ids: list[str] | None = Field(
        default=None, alias="excluded-workspaces"
    )
    allowed_project_ids: list[str] | None = Field(
        default=None, alias="allowed-projects"
    )

    @model_validator(mode="after")
    def valid(self) -> AgentPoolUpdateOptions:
        """Validate the options for updating an agent pool."""
        if self.name is not None and not valid_string_id(self.name):
            raise InvalidNameError()

        return self


class AgentPoolReadOptions(BaseModel):
    """Options for reading an agent pool."""

    # Optional: Include related resources
    include: list[AgentPoolIncludeOpt] | None = Field(default=None, alias="include")


class AgentPoolAssignToWorkspacesOptions(BaseModel):
    """Options for assigning an agent pool to workspaces."""

    workspace_ids: list[str] = Field(default_factory=list)


class AgentPoolRemoveFromWorkspacesOptions(BaseModel):
    """Options for removing an agent pool from workspaces."""

    workspace_ids: list[str] = Field(default_factory=list)


class AgentPoolAssignToProjectsOptions(BaseModel):
    """Options for assigning an agent pool to projects."""

    project_ids: list[str] = Field(default_factory=list)


class AgentListOptions(BaseModel):
    """Options for listing agents."""

    # Pagination options
    page_number: int | None = None
    page_size: int | None = None
    # Optional: Filter by status
    status: AgentStatus | None = None


class AgentReadOptions(BaseModel):
    """Options for reading an agent."""

    # Optional: Include related resources
    include: list[str] | None = None


# Agent Token Options


class AgentTokenCreateOptions(BaseModel):
    """Options for creating an agent token."""

    # Required: A description for the token
    description: str


class AgentToken(BaseModel):
    """Agent Token represents an authentication token for agents."""

    id: str
    description: str | None = None
    created_at: datetime | None = None
    last_used_at: datetime | None = None
    token: str | None = None  # Only returned on creation

    # Relations
    agent_pool: AgentPool | None = None


class AgentTokenListOptions(BaseModel):
    """Options for listing agent tokens."""

    # Pagination options
    page_number: int | None = None
    page_size: int | None = None
