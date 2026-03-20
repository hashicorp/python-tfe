from __future__ import annotations

from ..models.project import Project
from ..models.team import Team
from ..models.team_project_access import (
    ProjectSettingsPermissionType,
    ProjectTeamsPermissionType,
    ProjectVariableSetsPermissionType,
    TeamProjectAccess,
    TeamProjectAccessAddOptions,
    TeamProjectAccessProjectPermissions,
    TeamProjectAccessType,
    TeamProjectAccessWorkspacePermissions,
    WorkspaceRunsPermissionType,
    WorkspaceSentinelMocksPermissionType,
    WorkspaceStateVersionsPermissionType,
    WorkspaceVariablesPermissionType,
)
from ._base import _Service


class TeamProjectAccesses(_Service):
    def add(self, options: TeamProjectAccessAddOptions) -> TeamProjectAccess:
        """Add a team access for a project."""
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

        return TeamProjectAccess.model_validate(attrs)
