from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from ..errors import ERR_INVALID_EMAIL, ERR_INVALID_ORG
from ..models.organization import Organization
from ..models.organization_membership import (
    OrganizationMembership,
    OrganizationMembershipCreateOptions,
    OrganizationMembershipListOptions,
    OrganizationMembershipReadOptions,
)
from ..models.team import Team
from ..models.user import User
from ..utils import valid_string_id
from ._base import _Service


def _valid_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    # Simple email validation pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def _validate_email_params(emails: list[str] | None) -> None:
    """Validate a list of email parameters."""
    if not emails:
        return
    for email in emails:
        if not _valid_email(email):
            raise ValueError(ERR_INVALID_EMAIL)


class OrganizationMemberships(_Service):
    """Organization memberships service for managing organization members."""

    def create(
        self,
        organization: str,
        options: OrganizationMembershipCreateOptions,
    ) -> OrganizationMembership:
        """Create an organization membership with the given options.

        Args:
            organization: The name of the organization
            options: The options for creating the organization membership

        Returns:
            The created OrganizationMembership

        Raises:
            ValueError: If organization name is invalid or options are invalid
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        # Validate email is provided
        if not options.email:
            raise ValueError("email is required")

        # Validate email format
        if not _valid_email(options.email):
            raise ValueError(ERR_INVALID_EMAIL)

        # Build the URL path
        path = f"/api/v2/organizations/{organization}/organization-memberships"

        # Build the request body
        body = {
            "data": {
                "type": "organization-memberships",
                "attributes": {
                    "email": options.email,
                },
            }
        }

        # Add teams relationship if provided
        if options.teams:
            body["data"]["relationships"] = {
                "teams": {
                    "data": [{"type": "teams", "id": team.id} for team in options.teams]
                }
            }

        # Make the POST request
        response = self.t.request("POST", path, json_body=body)
        data = response.json()

        return self._parse_membership(data["data"])

    def list(
        self,
        organization: str,
        options: OrganizationMembershipListOptions | None = None,
    ) -> Iterator[OrganizationMembership]:
        """List all the organization memberships of the given organization.

        Args:
            organization: The name of the organization
            options: Optional filters and pagination options

        Yields:
            OrganizationMembership instances one at a time

        Raises:
            ValueError: If organization name is invalid or email filters are invalid
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        # Validate options if provided
        if options and options.emails:
            _validate_email_params(options.emails)

        # Build the URL path
        path = f"/api/v2/organizations/{organization}/organization-memberships"

        # Build query parameters from options
        params: dict[str, Any] = {}
        if options:
            options_dict = options.model_dump(by_alias=True, exclude_none=True)

            # Handle include parameter - convert list to comma-separated string
            if "include" in options_dict and isinstance(options_dict["include"], list):
                options_dict["include"] = ",".join(
                    opt.value if hasattr(opt, "value") else str(opt)
                    for opt in options.include or []
                )

            # Handle emails filter - convert list to comma-separated string
            if "filter[email]" in options_dict and isinstance(
                options_dict["filter[email]"], list
            ):
                options_dict["filter[email]"] = ",".join(options_dict["filter[email]"])

            # Handle status filter - extract value from enum
            if "filter[status]" in options_dict:
                status_value = options_dict["filter[status]"]
                if hasattr(status_value, "value"):
                    options_dict["filter[status]"] = status_value.value

            params.update(options_dict)

        # Use the _list helper for automatic pagination
        for item in self._list(path, params=params):
            yield self._parse_membership(item)

    def read(self, organization_membership_id: str) -> OrganizationMembership:
        """Read an organization membership by its ID.

        Args:
            organization_membership_id: The ID of the organization membership to read

        Returns:
            The OrganizationMembership

        Raises:
            ValueError: If organization membership ID is invalid
            NotFound: If the resource is not found
        """
        return self.read_with_options(
            organization_membership_id, OrganizationMembershipReadOptions()
        )

    def read_with_options(
        self,
        organization_membership_id: str,
        options: OrganizationMembershipReadOptions | None = None,
    ) -> OrganizationMembership:
        """Read an organization membership by ID with options.

        Args:
            organization_membership_id: The ID of the organization membership to read
            options: Read options including include parameters

        Returns:
            The OrganizationMembership with requested included data

        Raises:
            ValueError: If organization membership ID is invalid
            NotFound: If the resource is not found
        """
        if not valid_string_id(organization_membership_id):
            raise ValueError("invalid organization membership ID")

        # Build the URL path
        path = f"/api/v2/organization-memberships/{organization_membership_id}"

        # Build query parameters from options
        params: dict[str, Any] = {}
        if options:
            options_dict = options.model_dump(by_alias=True, exclude_none=True)

            # Handle include parameter - convert list to comma-separated string
            if "include" in options_dict and isinstance(options_dict["include"], list):
                options_dict["include"] = ",".join(
                    opt.value if hasattr(opt, "value") else str(opt)
                    for opt in options.include or []
                )

            params.update(options_dict)

        # Make the GET request
        # NotFound exception will be raised by self.t.request if resource doesn't exist
        response = self.t.request("GET", path, params=params)
        data = response.json()
        return self._parse_membership(data["data"])

    def delete(self, organization_membership_id: str) -> None:
        """Delete an organization membership by its ID.

        Args:
            organization_membership_id: The ID of the organization membership to delete

        Raises:
            ValueError: If organization membership ID is invalid
        """
        if not valid_string_id(organization_membership_id):
            raise ValueError("invalid organization membership ID")

        # Build the URL path
        path = f"/api/v2/organization-memberships/{organization_membership_id}"

        # Make the DELETE request
        self.t.request("DELETE", path)

    def _parse_membership(self, data: dict[str, Any]) -> OrganizationMembership:
        """Parse a membership from API response data.

        Args:
            data: The raw API response data for a membership

        Returns:
            OrganizationMembership instance
        """
        membership_id = data.get("id", "")
        attributes = data.get("attributes", {})

        # Extract basic attributes
        status = attributes.get("status", "active")
        email = attributes.get("email", "")

        # Extract relationships if present
        relationships = data.get("relationships", {})

        # Parse organization relationship
        organization = None
        if "organization" in relationships:
            org_data = relationships["organization"].get("data")
            if org_data:
                organization = Organization(id=org_data.get("id"))

        # Parse user relationship
        user = None
        if "user" in relationships:
            user_data = relationships["user"].get("data")
            if user_data:
                user = User(id=user_data.get("id"))

        # Parse teams relationship
        teams = None
        if "teams" in relationships:
            teams_data = relationships["teams"].get("data", [])
            if teams_data:
                teams = [Team(id=team.get("id")) for team in teams_data]

        # Handle included data if present (for full user/org objects)
        # This would be populated when include options are used
        # For now, keeping it simple with just IDs

        return OrganizationMembership(
            id=membership_id,
            status=status,
            email=email,
            organization=organization,
            user=user,
            teams=teams,
        )
