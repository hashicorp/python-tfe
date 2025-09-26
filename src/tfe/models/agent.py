"""Agent and Agent Pool models for the Python TFE SDK.

This module contains Pydantic models for Terraform Enterprise/Cloud agents and agent pools,
including all necessary option classes for CRUD operations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status enumeration."""

    IDLE = "idle"
    BUSY = "busy"
    UNKNOWN = "unknown"


class AgentPoolAllowedWorkspacePolicy(str, Enum):
    """Agent pool allowed workspace policy enumeration."""

    ALL_WORKSPACES = "all-workspaces"
    SPECIFIC_WORKSPACES = "specific-workspaces"


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

    id: str
    name: str | None = None
    created_at: datetime | None = None
    organization_scoped: bool | None = None
    allowed_workspace_policy: AgentPoolAllowedWorkspacePolicy | None = None
    agent_count: int = 0

    # Relations
    organization: Any | None = None  # Organization type from main types
    workspaces: list[Any] = Field(default_factory=list)  # Workspace types
    agents: list[Agent] = Field(default_factory=list)


# Agent Pool Options


class AgentPoolListOptions(BaseModel):
    """Options for listing agent pools."""

    # Pagination options
    page_number: int | None = None
    page_size: int | None = None
    # Optional: Include related resources
    include: list[str] | None = None
    # Optional: Filter by allowed workspace policy
    allowed_workspace_policy: AgentPoolAllowedWorkspacePolicy | None = None


class AgentPoolCreateOptions(BaseModel):
    """Options for creating an agent pool."""

    # Required: A name to identify the agent pool
    name: str
    # Optional: Whether the agent pool is organization scoped
    organization_scoped: bool | None = None
    # Optional: Allowed workspace policy
    allowed_workspace_policy: AgentPoolAllowedWorkspacePolicy | None = None


class AgentPoolUpdateOptions(BaseModel):
    """Options for updating an agent pool."""

    # Optional: A name to identify the agent pool
    name: str | None = None
    # Optional: Whether the agent pool is organization scoped
    organization_scoped: bool | None = None
    # Optional: Allowed workspace policy
    allowed_workspace_policy: AgentPoolAllowedWorkspacePolicy | None = None


class AgentPoolReadOptions(BaseModel):
    """Options for reading an agent pool."""

    # Optional: Include related resources
    include: list[str] | None = None


# Agent Pool Workspace Assignment Options


class AgentPoolAssignToWorkspacesOptions(BaseModel):
    """Options for assigning an agent pool to workspaces."""

    workspace_ids: list[str] = Field(default_factory=list)


class AgentPoolRemoveFromWorkspacesOptions(BaseModel):
    """Options for removing an agent pool from workspaces."""

    workspace_ids: list[str] = Field(default_factory=list)


# Agent Options


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
