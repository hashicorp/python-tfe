# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import InvalidOrgError, InvalidTeamIDError, InvalidTokenIDError
from ..models.organization import Organization
from ..models.team import Team
from ..models.team_token import (
    CreatedByChoice,
    TeamToken,
    TeamTokenCreateOptions,
    TeamTokenListOptions,
)
from ..models.user import User
from ..utils import valid_string_id
from ._base import _Service


class TeamTokens(_Service):
    """Service for managing team authentication tokens."""

    def create(self, team_id: str) -> TeamToken:
        """
        Create a new team token using the legacy creation behavior, which creates a token without a description
        or regenerates the existing, descriptionless token.
        """
        return self.create_with_options(team_id=team_id)

    def create_with_options(
        self,
        team_id: str,
        options: TeamTokenCreateOptions | None = None,
    ) -> TeamToken:
        """
        CreateWithOptions creates a team token, with options. If no description is provided, it uses the legacy
        creation behavior, which regenerates the descriptionless token if it already exists. Otherwise, it create
        a new token with the given unique description, allowing for the creation of multiple team tokens.
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()

        opts = options or TeamTokenCreateOptions()

        if opts.description:
            # New multi-token endpoint
            path = f"/api/v2/teams/{team_id}/authentication-tokens"
            payload_type = "authentication-tokens"
        else:
            # Legacy single-token endpoint
            path = f"/api/v2/teams/{team_id}/authentication-token"
            payload_type = "authentication-token"

        attributes: dict[str, Any] = opts.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude={"description"} if not opts.description else set(),
            mode="json",
        )

        payload = {
            "data": {
                "type": payload_type,
                "attributes": attributes,
            }
        }
        r = self.t.request("POST", path=path, json_body=payload)
        data = r.json().get("data", {})
        return self._team_token_from(data)

    def read(self, team_id: str) -> TeamToken:
        """Read the legacy (descriptionless) team token by team ID."""
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        r = self.t.request("GET", path=f"/api/v2/teams/{team_id}/authentication-token")
        data = r.json().get("data", {})
        return self._team_token_from(data)

    def read_by_id(self, token_id: str) -> TeamToken:
        """Read a team token by its token ID."""
        if not valid_string_id(token_id):
            raise InvalidTokenIDError()
        r = self.t.request("GET", path=f"/api/v2/authentication-tokens/{token_id}")
        data = r.json().get("data", {})
        return self._team_token_from(data)

    def list(
        self,
        organization: str,
        options: TeamTokenListOptions | None = None,
    ) -> Iterator[TeamToken]:
        """List all team tokens for the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        path = f"/api/v2/organizations/{organization}/team-tokens"
        params: dict[str, Any] = {}
        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.query:
                params["q"] = options.query
            if options.sort:
                params["sort"] = options.sort
        for item in self._list(path=path, params=params):
            yield self._team_token_from(item)

    def delete(self, team_id: str) -> None:
        """Delete the legacy team token by team ID."""
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        self.t.request("DELETE", path=f"/api/v2/teams/{team_id}/authentication-token")
        return None

    def delete_by_id(self, token_id: str) -> None:
        """Delete a team token by its token ID."""
        if not valid_string_id(token_id):
            raise InvalidTokenIDError()
        self.t.request("DELETE", path=f"/api/v2/authentication-tokens/{token_id}")
        return None

    def _team_token_from(self, data: dict[str, Any]) -> TeamToken:
        """Parse a TeamToken from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        relationships = data.get("relationships", {})

        team_data = relationships.get("team", {}).get("data")
        if team_data and team_data.get("id"):
            attrs["team"] = Team.model_construct(
                id=team_data["id"],
            )

        created_by_data = relationships.get("created-by", {}).get("data")
        if created_by_data and created_by_data.get("id"):
            if created_by_data.get("type") == "users":
                attrs["created-by"] = CreatedByChoice(
                    user=User.model_construct(id=created_by_data["id"])
                )
            elif created_by_data.get("type") == "teams":
                attrs["created-by"] = CreatedByChoice(
                    team=Team.model_construct(id=created_by_data["id"])
                )
            elif created_by_data.get("type") == "organizations":
                attrs["created-by"] = CreatedByChoice(
                    organization=Organization.model_construct(id=created_by_data["id"])
                )

        return TeamToken.model_validate(attrs)
