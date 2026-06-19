# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
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
        """Create or regenerate a legacy descriptionless team token.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).

        Returns:
            The created :class:`TeamToken`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> token = client.team_tokens.create("team-8U4yZ6bYbDZYQ1GH")
            >>> print(token.token)
        """
        return self.create_with_options(team_id=team_id)

    def create_with_options(
        self,
        team_id: str,
        options: TeamTokenCreateOptions | None = None,
    ) -> TeamToken:
        """Create a team token with optional description and expiry.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).
            options: Optional token attributes, as a :class:`TeamTokenCreateOptions`.

        Returns:
            The created :class:`TeamToken`.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TeamTokenCreateOptions
            >>> token = client.team_tokens.create_with_options(
            ...     "team-8U4yZ6bYbDZYQ1GH",
            ...     TeamTokenCreateOptions(description="CI deploy token"),
            ... )
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
        """Read the legacy descriptionless team token by team ID.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).

        Returns:
            The :class:`TeamToken`.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> token = client.team_tokens.read("team-8U4yZ6bYbDZYQ1GH")
            >>> print(token.id)
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        r = self.t.request("GET", path=f"/api/v2/teams/{team_id}/authentication-token")
        data = r.json().get("data", {})
        return self._team_token_from(data)

    def read_by_id(self, token_id: str) -> TeamToken:
        """Read a team token by its token ID.

        Args:
            token_id: The authentication token ID (e.g. ``"at-xxxxxxxx"``).

        Returns:
            The :class:`TeamToken`.

        Raises:
            InvalidTokenIDError: If ``token_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> token = client.team_tokens.read_by_id("at-abc123")
            >>> print(token.description)
        """
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
        """List team tokens in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional filters and page size, as a :class:`TeamTokenListOptions`.

        Returns:
            A single-use ``Iterator[TeamToken]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TeamTokenListOptions
            >>> tokens = client.team_tokens.list(
            ...     "my-org", TeamTokenListOptions(query="platform")
            ... )
            >>> for token in tokens:
            ...     print(token.id, token.description)
        """
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
        """Delete the legacy descriptionless team token by team ID.

        Args:
            team_id: The team ID (e.g. ``"team-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidTeamIDError: If ``team_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.team_tokens.delete("team-8U4yZ6bYbDZYQ1GH")
        """
        if not valid_string_id(team_id):
            raise InvalidTeamIDError()
        self.t.request("DELETE", path=f"/api/v2/teams/{team_id}/authentication-token")
        return None

    def delete_by_id(self, token_id: str) -> None:
        """Delete a team token by its token ID.

        Args:
            token_id: The authentication token ID (e.g. ``"at-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidTokenIDError: If ``token_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.team_tokens.delete_by_id("at-abc123")
        """
        if not valid_string_id(token_id):
            raise InvalidTokenIDError()
        self.t.request("DELETE", path=f"/api/v2/authentication-tokens/{token_id}")
        return None

    def _team_token_from(self, data: dict[str, Any]) -> TeamToken:
        """Parse a TeamToken from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        relationships = data.get("relationships", {})

        # Simple relations via the shared helper; created-by is polymorphic below.
        attrs.update(parse_relationships(relationships, {"team": Team}))

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

        return attach_jsonapi(TeamToken.model_validate(attrs), data)
