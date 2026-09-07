# Copyright IBM Corp. 2025, 2026

from __future__ import annotations

from collections.abc import Iterator

from .._jsonapi import attach_jsonapi
from ..errors import InvalidTeamProjectAccessIDError
from ..models.project import Project
from ..models.team import Team
from ..models.team_project_access import (
    ProjectSettingsPermissionType,
    ProjectTeamsPermissionType,
    ProjectVariableSetsPermissionType,
    TeamProjectAccess,
    TeamProjectAccessAddOptions,
    TeamProjectAccessListOptions,
    TeamProjectAccessProjectPermissions,
    TeamProjectAccessType,
    TeamProjectAccessUpdateOptions,
    TeamProjectAccessWorkspacePermissions,
    WorkspaceRunsPermissionType,
    WorkspaceSentinelMocksPermissionType,
    WorkspaceStateVersionsPermissionType,
    WorkspaceVariablesPermissionType,
)
from ..utils import valid_string_id
from ._base import _Service


class TeamProjectAccesses(_Service):
    def add(self, options: TeamProjectAccessAddOptions) -> TeamProjectAccess:
        """Add team access for a project.

        Args:
            options: The team, project, and permissions, as a
                :class:`TeamProjectAccessAddOptions`.

        Returns:
            The created :class:`TeamProjectAccess`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Project, Team, TeamProjectAccessAddOptions
            >>> options = TeamProjectAccessAddOptions(
            ...     access="read", team=Team(id="team-1"), project=Project(id="prj-1")
            ... )
            >>> access = client.team_project_accesses.add(
            ...     options
            ... )
        """
        attributes = options.model_dump(
            by_alias=True, exclude_none=True, exclude={"team", "project"}
        )
        relationships = {
            "team": {"data": {"id": options.team.id, "type": "teams"}}
            if options.team
            else None,
            "project": {"data": {"id": options.project.id, "type": "projects"}}
            if options.project
            else None,
        }
        payload = {
            "data": {
                "attributes": attributes,
                "relationships": relationships,
                "type": "team-project-access",
            }
        }
        r = self.t.request(
            "POST",
            path="/api/v2/team-projects",
            json_body=payload,
        )
        data = r.json().get("data", {})
        return self._team_project_access_from(data)

    def _team_project_access_from(self, data: dict) -> TeamProjectAccess:
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        attrs["access"] = (
            TeamProjectAccessType(attrs.get("access")) if attrs.get("access") else None
        )

        if attrs.get("project-access"):
            project_access: dict[str, object] = {}
            project_access["project_variable_sets_permission"] = (
                ProjectVariableSetsPermissionType(
                    attrs.get("project-access").get("variable-sets")
                )
            )
            project_access["project_settings_permission"] = (
                ProjectSettingsPermissionType(
                    attrs.get("project-access").get("settings")
                )
            )
            project_access["project_teams_permission"] = ProjectTeamsPermissionType(
                attrs.get("project-access").get("teams")
            )
            attrs["project_access"] = (
                TeamProjectAccessProjectPermissions.model_validate(project_access)
            )
        if attrs.get("workspace-access"):
            workspace_access: dict[str, object] = {}
            workspace_access["runs"] = WorkspaceRunsPermissionType(
                attrs.get("workspace-access").get("runs")
            )
            workspace_access["sentinel_mocks"] = WorkspaceSentinelMocksPermissionType(
                attrs.get("workspace-access").get("sentinel-mocks")
            )
            workspace_access["state_versions"] = WorkspaceStateVersionsPermissionType(
                attrs.get("workspace-access").get("state-versions")
            )
            workspace_access["variables"] = WorkspaceVariablesPermissionType(
                attrs.get("workspace-access").get("variables")
            )
            workspace_access["run_tasks"] = attrs.get("workspace-access").get(
                "run-tasks"
            )
            workspace_access["move"] = attrs.get("workspace-access").get("move")
            workspace_access["locking"] = attrs.get("workspace-access").get("locking")
            workspace_access["delete"] = attrs.get("workspace-access").get("delete")
            workspace_access["create"] = attrs.get("workspace-access").get("create")
            attrs["workspace_access"] = (
                TeamProjectAccessWorkspacePermissions.model_validate(workspace_access)
            )

        relationships = data.get("relationships", {})
        team_data = relationships.get("team", {}).get("data", {})
        project_data = relationships.get("project", {}).get("data", {})
        attrs["team"] = Team(id=team_data.get("id")) if team_data else None
        attrs["project"] = Project(id=project_data.get("id")) if project_data else None

        return attach_jsonapi(TeamProjectAccess.model_validate(attrs), data)

    def update(
        self, team_project_access_id: str, options: TeamProjectAccessUpdateOptions
    ) -> TeamProjectAccess:
        """Update team access for a project.

        Args:
            team_project_access_id: The team project access ID (e.g.
                ``"tprj-xxxxxxxx"``).
            options: The permission fields to change, as a
                :class:`TeamProjectAccessUpdateOptions`.

        Returns:
            The updated :class:`TeamProjectAccess`.

        Raises:
            InvalidTeamProjectAccessIDError: If ``team_project_access_id`` is not a
                valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TeamProjectAccessUpdateOptions
            >>> options = TeamProjectAccessUpdateOptions(
            ...     access="write"
            ... )
            >>> access = client.team_project_accesses.update(
            ...     "tprj-123", options
            ... )
        """
        if not valid_string_id(team_project_access_id):
            raise InvalidTeamProjectAccessIDError()
        attributes = options.model_dump(by_alias=True, exclude_none=True)
        payload = {
            "data": {
                "attributes": attributes,
                "type": "team-project-access",
            }
        }
        r = self.t.request(
            "PATCH",
            path=f"/api/v2/team-projects/{team_project_access_id}",
            json_body=payload,
        )
        data = r.json().get("data", {})
        return self._team_project_access_from(data)

    def read(self, team_project_access_id: str) -> TeamProjectAccess:
        """Read team access for a project.

        Args:
            team_project_access_id: The team project access ID (e.g.
                ``"tprj-xxxxxxxx"``).

        Returns:
            The :class:`TeamProjectAccess`.

        Raises:
            InvalidTeamProjectAccessIDError: If ``team_project_access_id`` is not a
                valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> access = client.team_project_accesses.read("tprj-123")
            >>> print(access.access)
        """
        if not valid_string_id(team_project_access_id):
            raise InvalidTeamProjectAccessIDError()
        r = self.t.request(
            "GET",
            path=f"/api/v2/team-projects/{team_project_access_id}",
        )
        data = r.json().get("data", {})
        return self._team_project_access_from(data)

    def list(
        self, options: TeamProjectAccessListOptions
    ) -> Iterator[TeamProjectAccess]:
        """List team accesses for projects.

        Args:
            options: Required filters and pagination, as a
                :class:`TeamProjectAccessListOptions`.

        Returns:
            A single-use ``Iterator[TeamProjectAccess]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TeamProjectAccessListOptions
            >>> for access in client.team_project_accesses.list(
            ...     TeamProjectAccessListOptions(project_id="prj-123")
            ... ):
            ...     print(access.id)
        """
        params = options.model_dump(by_alias=True, exclude_none=True)
        path = "/api/v2/team-projects"
        for item in self._list(path, params=params):
            yield self._team_project_access_from(item)

    def remove(self, team_project_access_id: str) -> None:
        """Remove team access for a project.

        Args:
            team_project_access_id: The team project access ID (e.g.
                ``"tprj-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidTeamProjectAccessIDError: If ``team_project_access_id`` is not a
                valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.team_project_accesses.remove("tprj-123")
        """
        if not valid_string_id(team_project_access_id):
            raise InvalidTeamProjectAccessIDError()
        self.t.request(
            "DELETE",
            path=f"/api/v2/team-projects/{team_project_access_id}",
        )
        return None
