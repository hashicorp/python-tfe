# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
import re
from collections.abc import Iterator
from typing import Any

from .._jsonapi import RelationMap, attach_jsonapi, parse_relationships
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

# Typed relations hydrated from ?include= (user, teams); organization is always
# present as a linkage ref. See OrgMembershipIncludeOpt.
_ORG_MEMBERSHIP_REL_MAP: RelationMap = {
    "organization": Organization,
    "user": User,
    "teams": Team,
}


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
        """Create an organization membership invitation.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Email address and optional teams, as a
                :class:`OrganizationMembershipCreateOptions`.

        Returns:
            The created :class:`OrganizationMembership`.

        Raises:
            ValueError: If ``organization`` or ``options.email`` is invalid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OrganizationMembershipCreateOptions
            >>> membership = client.organization_memberships.create(
            ...     "my-org", OrganizationMembershipCreateOptions(email="dev@example.com")
            ... )
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
        """List organization memberships in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional filters, includes, and pagination, as a
                :class:`OrganizationMembershipListOptions`.

        Returns:
            A single-use ``Iterator[OrganizationMembership]``. Wrap with
            ``list(...)`` to materialize the results or iterate more than once.

        Raises:
            ValueError: If ``organization`` or an email filter is invalid.
            TFEError: If the API request fails.

        Example:
            >>> for membership in client.organization_memberships.list("my-org"):
            ...     print(membership.id, membership.email)
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
            organization_membership_id: The organization membership ID
                (e.g. ``"ou-xxxxxxxx"``).

        Returns:
            The :class:`OrganizationMembership`.

        Raises:
            ValueError: If ``organization_membership_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> membership = client.organization_memberships.read("ou-abc123def456")
            >>> print(membership.email)
        """
        return self.read_with_options(
            organization_membership_id, OrganizationMembershipReadOptions()
        )

    def read_with_options(
        self,
        organization_membership_id: str,
        options: OrganizationMembershipReadOptions | None = None,
    ) -> OrganizationMembership:
        """Read an organization membership by its ID with options.

        Args:
            organization_membership_id: The organization membership ID
                (e.g. ``"ou-xxxxxxxx"``).
            options: Optional include controls, as a
                :class:`OrganizationMembershipReadOptions`.

        Returns:
            The :class:`OrganizationMembership`.

        Raises:
            ValueError: If ``organization_membership_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OrganizationMembershipReadOptions
            >>> membership = client.organization_memberships.read_with_options(
            ...     "ou-abc123def456", OrganizationMembershipReadOptions()
            ... )
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
        return self._parse_membership(data["data"], data.get("included"))

    def delete(self, organization_membership_id: str) -> None:
        """Delete an organization membership by its ID.

        Args:
            organization_membership_id: The organization membership ID
                (e.g. ``"ou-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``organization_membership_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.organization_memberships.delete("ou-abc123def456")
        """
        if not valid_string_id(organization_membership_id):
            raise ValueError("invalid organization membership ID")

        # Build the URL path
        path = f"/api/v2/organization-memberships/{organization_membership_id}"

        # Make the DELETE request
        self.t.request("DELETE", path)

    def _parse_membership(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> OrganizationMembership:
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

        # organization/user/teams are id-only stubs by default and are filled
        # from the JSON:API ``included`` array when requested via ?include=.
        rels = parse_relationships(
            data.get("relationships"), _ORG_MEMBERSHIP_REL_MAP, included=included
        )
        # Historical contract: an empty teams relation stays None (not []).
        if not rels.get("teams"):
            rels.pop("teams", None)

        return attach_jsonapi(
            OrganizationMembership(
                id=membership_id,
                status=status,
                email=email,
                **rels,
            ),
            data,
            included,
        )
