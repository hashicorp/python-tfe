from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .organization import Organization
    from .team import Team
    from .user import User


class OrganizationMembershipStatus(str, Enum):
    """Organization membership status enum."""

    ACTIVE = "active"
    INVITED = "invited"


class OrgMembershipIncludeOpt(str, Enum):
    """Include options for organization membership queries."""

    USER = "user"
    TEAMS = "teams"


class OrganizationMembership(BaseModel):
    """Represents a Terraform Enterprise organization membership."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    status: OrganizationMembershipStatus
    email: str

    # Relations
    organization: Organization | None = None
    user: User | None = None
    teams: list[Team] | None = None


class OrganizationMembershipListOptions(BaseModel):
    """Options for listing organization memberships."""

    model_config = ConfigDict(populate_by_name=True)

    # Pagination
    page_number: int | None = Field(None, alias="page[number]")
    page_size: int | None = Field(None, alias="page[size]")

    # Include related resources
    include: list[OrgMembershipIncludeOpt] | None = None

    # Filters
    emails: list[str] | None = Field(None, alias="filter[email]")
    status: OrganizationMembershipStatus | None = Field(None, alias="filter[status]")
    query: str | None = Field(None, alias="q")


class OrganizationMembershipReadOptions(BaseModel):
    """Options for reading an organization membership."""

    model_config = ConfigDict(populate_by_name=True)

    # Include related resources
    include: list[OrgMembershipIncludeOpt] | None = None


class OrganizationMembershipCreateOptions(BaseModel):
    """Options for creating an organization membership."""

    model_config = ConfigDict(populate_by_name=True)

    # Required
    email: str

    # Optional: A list of teams to add the user to
    teams: list[Team] | None = None


# Rebuild models after all definitions to resolve forward references
def _rebuild_models() -> None:
    """Rebuild models to resolve forward references."""
    try:
        from .organization import Organization  # noqa: F401
        from .team import Team  # noqa: F401
        from .user import User  # noqa: F401

        OrganizationMembership.model_rebuild()
        OrganizationMembershipCreateOptions.model_rebuild()
    except Exception:
        # If rebuild fails, models will still work at runtime
        pass


_rebuild_models()
