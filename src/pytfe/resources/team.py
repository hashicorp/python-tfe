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
