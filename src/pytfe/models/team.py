from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from .organization_membership import OrganizationMembership
    from .user import User


class OrganizationAccess(BaseModel):
    """Organization access permissions for a team."""

    model_config = ConfigDict(populate_by_name=True)

    manage_policies: bool = False
    manage_policy_overrides: bool = False
    manage_workspaces: bool = False
    manage_vcs_settings: bool = False
    manage_providers: bool = False
    manage_modules: bool = False
    manage_run_tasks: bool = False
    manage_projects: bool = False
    read_workspaces: bool = False
    read_projects: bool = False
    manage_membership: bool = False
    manage_teams: bool = False
    manage_organization_access: bool = False
    access_secret_teams: bool = False
    manage_agent_pools: bool = False


class TeamPermissions(BaseModel):
    """Team permissions for the current user."""

    model_config = ConfigDict(populate_by_name=True)

    can_destroy: bool = False
    can_update_membership: bool = False


class Team(BaseModel):
    """Represents a Terraform Enterprise team."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str | None = None
    is_unified: bool = False
    organization_access: OrganizationAccess | None = None
    visibility: str | None = None
    permissions: TeamPermissions | None = None
    user_count: int = 0
    sso_team_id: str | None = None
    allow_member_token_management: bool = False

    # Relations
    users: list[User] | None = None
    organization_memberships: list[OrganizationMembership] | None = None


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    from .organization import Organization  # noqa: F401
    from .organization_membership import OrganizationMembership  # noqa: F401
    from .user import User  # noqa: F401

    Team.model_rebuild()


_rebuild_models()
