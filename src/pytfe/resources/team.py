from __future__ import annotations

from collections.abc import Iterator

from ..errors import (
    ERR_INVALID_ORG,
    InvalidTeamIDError,
)
from ..models.organization_membership import OrganizationMembership
from ..models.team import (
    Team,
    TeamCreateOptions,
    TeamListOptions,
    TeamUpdateOptions,
)
from ..models.user import User
from ..utils import valid_string_id
from ._base import _Service


class Teams(_Service):
    def list(
        self, organization: str, options: TeamListOptions | None = None
    ) -> Iterator[Team]:
        """List all teams in the given organization."""
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

    def _team_from(self, data: dict) -> Team:
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        relationships = data.get("relationships", {})

        users_data = relationships.get("users", {}).get("data", [])
        attrs["users"] = [
            User.model_validate({"id": user_data.get("id")})
            for user_data in users_data
            if user_data.get("id")
        ]
        attrs["organization-memberships"] = [
            OrganizationMembership.model_validate({"id": om_data.get("id")})
            for om_data in relationships.get("organization-memberships", {}).get(
                "data", []
            )
            if om_data.get("id")
        ]

        return Team.model_validate(attrs)

    def create(self, organization: str, options: TeamCreateOptions) -> Team:
        """Create a new team in the given organization."""
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
        """Update a team by its ID."""
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

    def read(self, team_id: str) -> Team:
        """Read a single team by its ID."""
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        r = self.t.request(
            "GET",
            path=f"/api/v2/teams/{team_id}",
        )
        data = r.json().get("data", {})
        return self._team_from(data)

    def delete(self, team_id: str) -> None:
        """Delete a team by its ID."""
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

    def add_users(self, team_id: str, usernames: list[str]) -> None:
        """Add users to a team by username.
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

    def remove_users(self, team_id: str, usernames: list[str]) -> None:
        """Remove users from a team by username."""
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
        self, team_id: str, organization_membership_ids: list[str]
    ) -> None:
        """Add users to a team by organization membership id."""
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
        self, team_id: str, organization_membership_ids: list[str]
    ) -> None:
        """Remove users from a team by organization membership id."""
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

        Implemented via ``GET /teams/{id}?include=users`` — the API has no
        dedicated paginated endpoint for team users, so all results arrive
        in a single response. The signature still returns an iterator to
        stay consistent with the other ``list_*`` methods in the SDK; wrap
        the result in ``list(...)`` if you need a materialized list.
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

        Uses the dedicated paginated endpoint
        ``GET /teams/{id}/relationships/organization-memberships`` so
        callers get server-side pagination, filtering by status /
        service-account flag, and sort.
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
