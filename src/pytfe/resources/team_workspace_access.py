# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidTeamIDError, InvalidWorkspaceIDError, TFEError
from ..models.team_workspace_access import (
    TeamWorkspaceAccess,
    TeamWorkspaceAccessAddOptions,
    TeamWorkspaceAccessUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class InvalidTeamWorkspaceAccessIDError(TFEError):
    """Raised when a team-workspace access id is missing or malformed."""

    def __init__(self, message: str = "invalid team workspace access id"):
        super().__init__(message)


def _parse(data: dict[str, Any]) -> TeamWorkspaceAccess:
    attributes = dict(data.get("attributes") or {})
    attributes["id"] = data.get("id", "")
    relationships = data.get("relationships") or {}
    team_data = (relationships.get("team") or {}).get("data") or {}
    workspace_data = (relationships.get("workspace") or {}).get("data") or {}
    if team_data.get("id"):
        attributes["team-id"] = team_data["id"]
    if workspace_data.get("id"):
        attributes["workspace-id"] = workspace_data["id"]
    return attach_jsonapi(TeamWorkspaceAccess.model_validate(attributes), data)


def _attributes_payload(model_dict: dict[str, Any]) -> dict[str, Any]:
    """Hyphenate snake_case attribute keys for JSON:API."""
    return {k.replace("_", "-"): v for k, v in model_dict.items() if v is not None}


class TeamWorkspaceAccesses(_Service):
    """Manage team access grants on workspaces (`/api/v2/team-workspaces`)."""

    def list(self, workspace_id: str) -> Iterator[TeamWorkspaceAccess]:
        """List team access grants for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).

        Returns:
            A single-use ``Iterator[TeamWorkspaceAccess]``. Wrap with ``list(...)``
            to materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for grant in client.team_workspace_accesses.list("ws-123"):
            ...     print(grant.id, grant.team_id, grant.access)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        path = "/api/v2/team-workspaces"
        params = {"filter[workspace][id]": workspace_id}
        for item in self._list(path, params=params):
            yield _parse(item)

    def read(self, team_workspace_access_id: str) -> TeamWorkspaceAccess:
        """Read a single team-workspace access grant by ID.

        Args:
            team_workspace_access_id: The team-workspace access ID
                (e.g. ``"twsa-xxxxxxxx"``).

        Returns:
            The :class:`TeamWorkspaceAccess`.

        Raises:
            InvalidTeamWorkspaceAccessIDError: If ``team_workspace_access_id`` is not
                a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> grant = client.team_workspace_accesses.read("twsa-123")
            >>> print(grant.workspace_id)
        """
        if not valid_string_id(team_workspace_access_id):
            raise InvalidTeamWorkspaceAccessIDError()
        r = self.t.request("GET", f"/api/v2/team-workspaces/{team_workspace_access_id}")
        return _parse((r.json() or {}).get("data") or {})

    def add(self, options: TeamWorkspaceAccessAddOptions) -> TeamWorkspaceAccess:
        """Add a team access grant to a workspace.

        Args:
            options: Team and workspace access settings, as a
                :class:`TeamWorkspaceAccessAddOptions`.

        Returns:
            The :class:`TeamWorkspaceAccess`.

        Raises:
            InvalidTeamIDError: If ``options.team_id`` is not a valid resource ID.
            InvalidWorkspaceIDError: If ``options.workspace_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TeamWorkspaceAccessAddOptions
            >>> from pytfe.models import TeamWorkspaceAccessType
            >>> grant = client.team_workspace_accesses.add(
            ...     TeamWorkspaceAccessAddOptions(
            ...         team_id="team-123", workspace_id="ws-123",
            ...         access=TeamWorkspaceAccessType.READ,
            ...     )
            ... )
        """
        if not valid_string_id(options.team_id):
            raise InvalidTeamIDError()
        if not valid_string_id(options.workspace_id):
            raise InvalidWorkspaceIDError()
        attrs = _attributes_payload(
            options.model_dump(
                by_alias=False,
                exclude={"team_id", "workspace_id"},
                exclude_none=True,
                mode="json",
            )
        )
        payload = {
            "data": {
                "type": "team-workspaces",
                "attributes": attrs,
                "relationships": {
                    "team": {"data": {"type": "teams", "id": options.team_id}},
                    "workspace": {
                        "data": {"type": "workspaces", "id": options.workspace_id}
                    },
                },
            }
        }
        r = self.t.request("POST", "/api/v2/team-workspaces", json_body=payload)
        return _parse((r.json() or {}).get("data") or {})

    def update(
        self,
        team_workspace_access_id: str,
        options: TeamWorkspaceAccessUpdateOptions,
    ) -> TeamWorkspaceAccess:
        """Update an existing team-workspace access grant.

        Args:
            team_workspace_access_id: The team-workspace access ID
                (e.g. ``"twsa-xxxxxxxx"``).
            options: Access update settings, as a
                :class:`TeamWorkspaceAccessUpdateOptions`.

        Returns:
            The :class:`TeamWorkspaceAccess`.

        Raises:
            InvalidTeamWorkspaceAccessIDError: If ``team_workspace_access_id`` is not
                a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TeamWorkspaceAccessType
            >>> from pytfe.models import TeamWorkspaceAccessUpdateOptions
            >>> grant = client.team_workspace_accesses.update(
            ...     "twsa-123",
            ...     TeamWorkspaceAccessUpdateOptions(
            ...         access=TeamWorkspaceAccessType.PLAN
            ...     ),
            ... )
        """
        if not valid_string_id(team_workspace_access_id):
            raise InvalidTeamWorkspaceAccessIDError()
        attrs = _attributes_payload(
            options.model_dump(by_alias=False, exclude_none=True, mode="json")
        )
        payload = {
            "data": {
                "type": "team-workspaces",
                "id": team_workspace_access_id,
                "attributes": attrs,
            }
        }
        r = self.t.request(
            "PATCH",
            f"/api/v2/team-workspaces/{team_workspace_access_id}",
            json_body=payload,
        )
        return _parse((r.json() or {}).get("data") or {})

    def remove(self, team_workspace_access_id: str) -> None:
        """Remove a team-workspace access grant.

        Args:
            team_workspace_access_id: The team-workspace access ID
                (e.g. ``"twsa-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidTeamWorkspaceAccessIDError: If ``team_workspace_access_id`` is not
                a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.team_workspace_accesses.remove("twsa-123")
        """
        if not valid_string_id(team_workspace_access_id):
            raise InvalidTeamWorkspaceAccessIDError()
        self.t.request(
            "DELETE",
            f"/api/v2/team-workspaces/{team_workspace_access_id}",
        )
        return None
