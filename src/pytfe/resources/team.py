# Copyright IBM Corp. 2025, 2026

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import (
    ERR_INVALID_ORG,
    InvalidTeamIDError,
)
from ..models.organization_membership import OrganizationMembership
from ..models.team import (
    Team,
    TeamCreateOptions,
    TeamListOptions,
    TeamReadOptions,
    TeamUpdateOptions,
)
from ..models.user import User
from ..utils import valid_string_id
from ._base import _Service


class Teams(_Service):
    def list(
        self, organization: str, options: TeamListOptions | None = None
    ) -> Iterator[Team]:
        """List all teams in the given organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Pagination, filter, and include options, as a
                :class:`TeamListOptions`.

        Returns:
            A single-use ``Iterator[Team]``. Wrap with ``list(...)`` to materialize
            the results or iterate more than once.

        Raises:
            ValueError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> for team in client.teams.list("my-org"):
            ...     print(team.id, team.name)
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)
        params = (
            options.model_dump(by_alias=True, exclude_none=True, exclude={"include"})
            if options
            else {}
        )
        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])
        path = f"/api/v2/organizations/{organization}/teams"
        for item in self._list(path, params=params):
            yield self._team_from(item)

    def _team_from(
        self,
        data: dict,
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> Team:
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"users": User, "organization-memberships": OrganizationMembership},
                included=included,
            )
        )
        return attach_jsonapi(Team.model_validate(attrs), data, included)

    def create(self, organization: str, options: TeamCreateOptions) -> Team:
        """Create a new team in the given organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Team creation settings, as a :class:`TeamCreateOptions`.

        Returns:
            The :class:`Team`.

        Raises:
            ValueError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TeamCreateOptions
            >>> team = client.teams.create(
            ...     "my-org", TeamCreateOptions(name="platform")
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)
        attributes = options.model_dump(by_alias=True, exclude_none=True)
        payload = {"data": {"attributes": attributes, "type": "teams"}}
        r = self.t.request(
            "POST",
            path=f"/api/v2/organizations/{organization}/teams",
            json_body=payload,
        )
        data = r.json().get("data", {})
        return self._team_from(data)

    def update(self, team_id: str, options: TeamUpdateOptions) -> Team:
        """Update a team by its ID.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).
            options: Team update settings, as a :class:`TeamUpdateOptions`.

        Returns:
            The :class:`Team`.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TeamUpdateOptions
            >>> team = client.teams.update(
            ...     "team-789", TeamUpdateOptions(name="platform-admins")
            ... )
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        attributes = options.model_dump(by_alias=True, exclude_none=True)
        payload = {"data": {"attributes": attributes, "type": "teams"}}
        r = self.t.request(
            "PATCH",
            path=f"/api/v2/teams/{team_id}",
            json_body=payload,
        )
        data = r.json().get("data", {})
        return self._team_from(data)

    def read(self, team_id: str, options: TeamReadOptions | None = None) -> Team:
        """Read a single team by its ID.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).
            options: Include options, as a :class:`TeamReadOptions`.

        Returns:
            The :class:`Team`.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> team = client.teams.read("team-789")
            >>> print(team.name)
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        params: dict[str, str] = {}
        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])
        r = self.t.request(
            "GET",
            path=f"/api/v2/teams/{team_id}",
            params=params,
        )
        payload = r.json()
        return self._team_from(payload.get("data", {}), payload.get("included"))

    def delete(self, team_id: str) -> None:
        """Delete a team by its ID.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.teams.delete("team-789")
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        self.t.request(
            "DELETE",
            path=f"/api/v2/teams/{team_id}",
        )
        return None

    # ------------------------------------------------------------------
    # Team membership management
    # ------------------------------------------------------------------

    def add_users(self, team_id: str, usernames: builtins.list[str]) -> None:
        """Add users to a team by username.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).
            usernames: Usernames to add to the team (e.g. ``["alice", "bob"]``).

        Returns:
            None.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            ValueError: If ``usernames`` is empty or contains blank values.
            TFEError: If the API request fails.

        Example:
            >>> client.teams.add_users("team-789", ["alice", "bob"])
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        if not usernames:
            raise ValueError("at least one username is required")
        if any(not isinstance(u, str) or not u.strip() for u in usernames):
            raise ValueError("usernames must be non-empty strings")
        payload = {"data": [{"type": "users", "id": u} for u in usernames]}
        self.t.request(
            "POST",
            path=f"/api/v2/teams/{team_id}/relationships/users",
            json_body=payload,
        )
        return None

    def remove_users(self, team_id: str, usernames: builtins.list[str]) -> None:
        """Remove users from a team by username.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).
            usernames: Usernames to remove from the team (e.g. ``["alice"]``).

        Returns:
            None.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            ValueError: If ``usernames`` is empty or contains blank values.
            TFEError: If the API request fails.

        Example:
            >>> client.teams.remove_users("team-789", ["alice"])
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        if not usernames:
            raise ValueError("at least one username is required")
        if any(not isinstance(u, str) or not u.strip() for u in usernames):
            raise ValueError("usernames must be non-empty strings")
        payload = {"data": [{"type": "users", "id": u} for u in usernames]}
        self.t.request(
            "DELETE",
            path=f"/api/v2/teams/{team_id}/relationships/users",
            json_body=payload,
        )
        return None

    def add_organization_memberships(
        self, team_id: str, organization_membership_ids: builtins.list[str]
    ) -> None:
        """Add organization memberships to a team by membership ID.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).
            organization_membership_ids: Organization membership IDs to add
                (e.g. ``["ou-xxxxxxxx"]``).

        Returns:
            None.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            ValueError: If no organization membership IDs are supplied or one is
                invalid.
            TFEError: If the API request fails.

        Example:
            >>> client.teams.add_organization_memberships("team-789", ["ou-123"])
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        if not organization_membership_ids:
            raise ValueError("at least one organization membership id is required")
        if any(not valid_string_id(i) for i in organization_membership_ids):
            raise ValueError("invalid organization membership id")
        payload = {
            "data": [
                {"type": "organization-memberships", "id": i}
                for i in organization_membership_ids
            ]
        }
        self.t.request(
            "POST",
            path=f"/api/v2/teams/{team_id}/relationships/organization-memberships",
            json_body=payload,
        )
        return None

    def remove_organization_memberships(
        self, team_id: str, organization_membership_ids: builtins.list[str]
    ) -> None:
        """Remove organization memberships from a team by membership ID.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).
            organization_membership_ids: Organization membership IDs to remove
                (e.g. ``["ou-xxxxxxxx"]``).

        Returns:
            None.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            ValueError: If no organization membership IDs are supplied or one is
                invalid.
            TFEError: If the API request fails.

        Example:
            >>> client.teams.remove_organization_memberships("team-789", ["ou-123"])
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        if not organization_membership_ids:
            raise ValueError("at least one organization membership id is required")
        if any(not valid_string_id(i) for i in organization_membership_ids):
            raise ValueError("invalid organization membership id")
        payload = {
            "data": [
                {"type": "organization-memberships", "id": i}
                for i in organization_membership_ids
            ]
        }
        self.t.request(
            "DELETE",
            path=f"/api/v2/teams/{team_id}/relationships/organization-memberships",
            json_body=payload,
        )
        return None

    def list_users(self, team_id: str) -> Iterator[User]:
        """List the users that belong to a team.

        Implemented via ``GET /teams/{id}?include=users`` because the API has no
        dedicated paginated endpoint for team users.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).

        Returns:
            A single-use ``Iterator[User]``. Wrap with ``list(...)`` to materialize
            the results or iterate more than once.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for user in client.teams.list_users("team-789"):
            ...     print(user.username)
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        r = self.t.request(
            "GET",
            path=f"/api/v2/teams/{team_id}",
            params={"include": "users"},
        )
        payload = r.json() or {}
        included = payload.get("included") or []
        for inc in included:
            if inc.get("type") != "users":
                continue
            attrs = dict(inc.get("attributes") or {})
            attrs["id"] = inc.get("id")
            yield User.model_validate(attrs)

    def list_organization_memberships(
        self,
        team_id: str,
        *,
        status: str | None = None,
        is_service_account: bool | None = None,
        sort: str | None = None,
    ) -> Iterator[OrganizationMembership]:
        """List the organization memberships that belong to a team.

        Uses the dedicated paginated relationship endpoint and supports filtering
        by status, service-account flag, and sort.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).
            status: Optional membership status filter (e.g. ``"active"``).
            is_service_account: Optional service-account filter.
            sort: Optional sort expression (e.g. ``"email"``).

        Returns:
            A single-use ``Iterator[OrganizationMembership]``. Wrap with
            ``list(...)`` to materialize the results or iterate more than once.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> memberships = client.teams.list_organization_memberships(
            ...     "team-789", status="active"
            ... )
            >>> for membership in memberships:
            ...     print(membership.id)
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        params: dict[str, str] = {}
        if status is not None:
            params["filter[status]"] = status
        if is_service_account is not None:
            params["filter[is_service_account]"] = (
                "true" if is_service_account else "false"
            )
        if sort is not None:
            params["sort"] = sort
        path = f"/api/v2/teams/{team_id}/relationships/organization-memberships"
        for item in self._list(path, params=params):
            attrs = dict(item.get("attributes") or {})
            attrs["id"] = item.get("id")
            yield OrganizationMembership.model_validate(attrs)
