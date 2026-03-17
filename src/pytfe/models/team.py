from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import ERR_REQUIRED_NAME, EmptyTeamNameError
from .organization_membership import OrganizationMembership
from .user import User


class OrganizationAccess(BaseModel):
    """Organization access permissions for a team."""

    model_config = ConfigDict(populate_by_name=True)

    manage_policies: bool = Field(default=False, alias="manage-policies")
    manage_policy_overrides: bool = Field(
        default=False, alias="manage-policy-overrides"
    )
    manage_workspaces: bool = Field(default=False, alias="manage-workspaces")
    manage_vcs_settings: bool = Field(default=False, alias="manage-vcs-settings")
    manage_providers: bool = Field(default=False, alias="manage-providers")
    manage_modules: bool = Field(default=False, alias="manage-modules")
    manage_run_tasks: bool = Field(default=False, alias="manage-run-tasks")
    manage_projects: bool = Field(default=False, alias="manage-projects")
    read_workspaces: bool = Field(default=False, alias="read-workspaces")
    read_projects: bool = Field(default=False, alias="read-projects")
    manage_membership: bool = Field(default=False, alias="manage-membership")
    manage_teams: bool = Field(default=False, alias="manage-teams")
    manage_organization_access: bool = Field(
        default=False, alias="manage-organization-access"
    )
    access_secret_teams: bool = Field(default=False, alias="access-secret-teams")
    manage_agent_pools: bool = Field(default=False, alias="manage-agent-pools")


class TeamPermissions(BaseModel):
    """Team permissions for the current user."""

    model_config = ConfigDict(populate_by_name=True)

    can_destroy: bool = Field(alias="can-destroy")
    can_update_membership: bool = Field(alias="can-update-membership")


class Team(BaseModel):
    """Represents a Terraform Enterprise team."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str | None = Field(default=None, alias="name")
    is_unified: bool = Field(default=False, alias="is-unified")
    organization_access: OrganizationAccess | None = Field(
        default=None, alias="organization-access"
    )
    visibility: str | None = Field(default=None, alias="visibility")
    permissions: TeamPermissions | None = Field(default=None, alias="permissions")
    user_count: int = Field(default=0, alias="user-count")
    sso_team_id: str | None = Field(default=None, alias="sso-team-id")
    # AllowMemberTokenManagement is false for TFE versions older than v202408
    allow_member_token_management: bool = Field(
        default=False, alias="allow-member-token-management"
    )

    # Relations
    users: list[User] = Field(alias="users", default_factory=list)
    organization_memberships: list[OrganizationMembership] = Field(
        alias="organization-memberships", default_factory=list
    )


class TeamIncludeOpt(str, Enum):
    """TeamIncludeOpt represents the available options for include query params."""

    TEAM_USERS = "users"
    TEAM_ORGANIZATION_MEMBERSHIPS = "organization-memberships"


class TeamListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]")
    include: list[TeamIncludeOpt] | None = Field(None, alias="include")
    names: list[str] | None = Field(None, alias="filter[names]")
    query: str | None = Field(None, alias="q")

    @model_validator(mode="after")
    def valid(self) -> TeamListOptions:
        """Validate the options."""

        if self.names is not None and any(not name for name in self.names):
            raise EmptyTeamNameError()

        return self


class OrganizationAccessOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    manage_policies: bool | None = Field(default=False, alias="manage-policies")
    manage_policy_overrides: bool | None = Field(
        default=False, alias="manage-policy-overrides"
    )
    manage_workspaces: bool | None = Field(default=False, alias="manage-workspaces")
    manage_vcs_settings: bool | None = Field(default=False, alias="manage-vcs-settings")
    manage_providers: bool | None = Field(default=False, alias="manage-providers")
    manage_modules: bool | None = Field(default=False, alias="manage-modules")
    manage_run_tasks: bool | None = Field(default=False, alias="manage-run-tasks")
    manage_projects: bool | None = Field(default=False, alias="manage-projects")
    read_workspaces: bool | None = Field(default=False, alias="read-workspaces")
    read_projects: bool | None = Field(default=False, alias="read-projects")
    manage_membership: bool | None = Field(default=False, alias="manage-membership")
    manage_teams: bool | None = Field(default=False, alias="manage-teams")
    manage_organization_access: bool | None = Field(
        default=False, alias="manage-organization-access"
    )
    access_secret_teams: bool | None = Field(default=False, alias="access-secret-teams")
    manage_agent_pools: bool | None = Field(default=False, alias="manage-agent-pools")


class TeamCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="name")
    sso_team_id: str | None = Field(default=None, alias="sso-team-id")
    organization_access: OrganizationAccessOptions | None = Field(
        default=None, alias="organization-access"
    )
    visibility: str | None = Field(alias="visibility")
    allow_member_token_management: bool | None = Field(
        default=None, alias="allow-member-token-management"
    )

    @model_validator(mode="after")
    def valid(self) -> TeamCreateOptions:
        """Validate the options."""
        if not self.name:
            raise ValueError(ERR_REQUIRED_NAME)
        return self


class TeamUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str = "teams"
    name: str | None = Field(default=None, alias="name")
    sso_team_id: str | None = Field(default=None, alias="sso-team-id")
    organization_access: OrganizationAccessOptions | None = Field(
        default=None, alias="organization-access"
    )
    visibility: str | None = Field(alias="visibility")
    allow_member_token_management: bool | None = Field(
        default=None, alias="allow-member-token-management"
    )
