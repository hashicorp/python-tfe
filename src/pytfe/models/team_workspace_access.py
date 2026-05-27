# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TeamWorkspaceAccessType(str, Enum):
    READ = "read"
    PLAN = "plan"
    WRITE = "write"
    ADMIN = "admin"
    CUSTOM = "custom"


class TeamWorkspaceRunsPermission(str, Enum):
    READ = "read"
    PLAN = "plan"
    APPLY = "apply"


class TeamWorkspaceVariablesPermission(str, Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"


class TeamWorkspaceStateVersionsPermission(str, Enum):
    NONE = "none"
    READ_OUTPUTS = "read-outputs"
    READ = "read"
    WRITE = "write"


class TeamWorkspaceSentinelMocksPermission(str, Enum):
    NONE = "none"
    READ = "read"


class TeamWorkspaceAccess(BaseModel):
    """A team's access grant on a workspace (`/api/v2/team-workspaces/{id}`)."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    access: TeamWorkspaceAccessType | None = None
    runs: TeamWorkspaceRunsPermission | None = None
    variables: TeamWorkspaceVariablesPermission | None = None
    state_versions: TeamWorkspaceStateVersionsPermission | None = Field(
        default=None, alias="state-versions"
    )
    sentinel_mocks: TeamWorkspaceSentinelMocksPermission | None = Field(
        default=None, alias="sentinel-mocks"
    )
    workspace_locking: bool | None = Field(default=None, alias="workspace-locking")
    run_tasks: bool | None = Field(default=None, alias="run-tasks")
    policy_overrides: bool | None = Field(default=None, alias="policy-overrides")

    # Relationships (populated from the JSON:API ``relationships`` block).
    team_id: str | None = Field(default=None, alias="team-id")
    workspace_id: str | None = Field(default=None, alias="workspace-id")


class TeamWorkspaceAccessAddOptions(BaseModel):
    """Options for adding a team access grant on a workspace."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    team_id: str
    workspace_id: str
    access: TeamWorkspaceAccessType
    runs: TeamWorkspaceRunsPermission | None = None
    variables: TeamWorkspaceVariablesPermission | None = None
    state_versions: TeamWorkspaceStateVersionsPermission | None = None
    sentinel_mocks: TeamWorkspaceSentinelMocksPermission | None = None
    workspace_locking: bool | None = None
    run_tasks: bool | None = None
    policy_overrides: bool | None = None


class TeamWorkspaceAccessUpdateOptions(BaseModel):
    """Options for updating an existing team access grant."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    access: TeamWorkspaceAccessType | None = None
    runs: TeamWorkspaceRunsPermission | None = None
    variables: TeamWorkspaceVariablesPermission | None = None
    state_versions: TeamWorkspaceStateVersionsPermission | None = None
    sentinel_mocks: TeamWorkspaceSentinelMocksPermission | None = None
    workspace_locking: bool | None = None
    run_tasks: bool | None = None
    policy_overrides: bool | None = None
