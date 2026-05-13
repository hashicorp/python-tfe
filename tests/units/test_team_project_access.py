# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the team_project_access module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidTeamProjectAccessIDError
from pytfe.models.project import Project
from pytfe.models.team import Team
from pytfe.models.team_project_access import (
    ProjectSettingsPermissionType,
    ProjectTeamsPermissionType,
    ProjectVariableSetsPermissionType,
    TeamProjectAccess,
    TeamProjectAccessAddOptions,
    TeamProjectAccessListOptions,
    TeamProjectAccessProjectPermissionsOptions,
    TeamProjectAccessType,
    TeamProjectAccessUpdateOptions,
    TeamProjectAccessWorkspacePermissionsOptions,
    WorkspaceRunsPermissionType,
    WorkspaceSentinelMocksPermissionType,
    WorkspaceStateVersionsPermissionType,
    WorkspaceVariablesPermissionType,
)
from pytfe.resources.team_project_access import TeamProjectAccesses


class TestTeamProjectAccesses:
    """Test the TeamProjectAccesses service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def team_project_accesses_service(self, mock_transport):
        """Create a TeamProjectAccesses service with mocked transport."""
        return TeamProjectAccesses(mock_transport)

    @pytest.fixture
    def team_project_access_response_data(self):
        """Return sample API response data for team project access."""
        return {
            "id": "tprj-123",
            "attributes": {
                "access": "custom",
                "project-access": {
                    "settings": "update",
                    "teams": "manage",
                    "variable-sets": "read",
                },
                "workspace-access": {
                    "runs": "plan",
                    "sentinel-mocks": "none",
                    "state-versions": "read-outputs",
                    "variables": "write",
                    "run-tasks": True,
                    "move": False,
                    "locking": True,
                    "delete": False,
                    "create": True,
                },
            },
            "relationships": {
                "team": {"data": {"id": "team-123", "type": "teams"}},
                "project": {"data": {"id": "prj-123", "type": "projects"}},
            },
        }

    def test_add_team_project_access_success(
        self,
        team_project_accesses_service,
        mock_transport,
        team_project_access_response_data,
    ):
        """Test successful add operation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": team_project_access_response_data}
        mock_transport.request.return_value = mock_response

        options = TeamProjectAccessAddOptions(
            access=TeamProjectAccessType.TEAM_PROJECT_ACCESS_CUSTOM,
            team=Team(id="team-123"),
            project=Project(id="prj-123"),
            project_access=TeamProjectAccessProjectPermissionsOptions(
                settings=ProjectSettingsPermissionType.PROJECT_SETTINGS_PERMISSION_UPDATE,
                teams=ProjectTeamsPermissionType.PROJECT_TEAMS_PERMISSION_MANAGE,
                variable_sets=ProjectVariableSetsPermissionType.PROJECT_VARIABLE_SETS_PERMISSION_READ,
            ),
            workspace_access=TeamProjectAccessWorkspacePermissionsOptions(
                runs=WorkspaceRunsPermissionType.WORKSPACE_RUNS_PERMISSION_PLAN,
                sentinel_mocks=WorkspaceSentinelMocksPermissionType.WORKSPACE_SENTINEL_MOCKS_PERMISSION_NONE,
                state_versions=WorkspaceStateVersionsPermissionType.WORKSPACE_STATE_VERSIONS_PERMISSION_READ_OUTPUTS,
                variables=WorkspaceVariablesPermissionType.WORKSPACE_VARIABLES_PERMISSION_WRITE,
                create=True,
                delete=False,
                locking=True,
                move=False,
                run_tasks=True,
            ),
        )

        result = team_project_accesses_service.add(options)

        mock_transport.request.assert_called_once()
        assert isinstance(result, TeamProjectAccess)
        assert result.id == "tprj-123"
        assert result.access == TeamProjectAccessType.TEAM_PROJECT_ACCESS_CUSTOM
        assert result.team.id == "team-123"
        assert result.project.id == "prj-123"

    def test_read_team_project_access_success(
        self,
        team_project_accesses_service,
        mock_transport,
        team_project_access_response_data,
    ):
        """Test successful read operation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": team_project_access_response_data}
        mock_transport.request.return_value = mock_response

        result = team_project_accesses_service.read("tprj-123")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/team-projects/tprj-123"
        )
        assert isinstance(result, TeamProjectAccess)
        assert result.id == "tprj-123"
        assert result.workspace_access.run_tasks is True

    def test_read_team_project_access_invalid_id(self, team_project_accesses_service):
        """Test read operation with invalid team project access ID."""
        with pytest.raises(InvalidTeamProjectAccessIDError):
            team_project_accesses_service.read("")

    def test_update_team_project_access_success(
        self,
        team_project_accesses_service,
        mock_transport,
        team_project_access_response_data,
    ):
        """Test successful update operation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": team_project_access_response_data}
        mock_transport.request.return_value = mock_response

        options = TeamProjectAccessUpdateOptions(
            access=TeamProjectAccessType.TEAM_PROJECT_ACCESS_CUSTOM,
            workspace_access=TeamProjectAccessWorkspacePermissionsOptions(
                run_tasks=True
            ),
        )

        result = team_project_accesses_service.update("tprj-123", options)

        mock_transport.request.assert_called_once()
        assert isinstance(result, TeamProjectAccess)
        assert result.id == "tprj-123"

    def test_update_team_project_access_invalid_id(self, team_project_accesses_service):
        """Test update operation with invalid team project access ID."""
        options = TeamProjectAccessUpdateOptions(
            access=TeamProjectAccessType.TEAM_PROJECT_ACCESS_READ
        )

        with pytest.raises(InvalidTeamProjectAccessIDError):
            team_project_accesses_service.update("", options)

    def test_list_team_project_accesses_success(
        self,
        team_project_accesses_service,
        team_project_access_response_data,
    ):
        """Test successful list operation."""
        team_project_accesses_service._list = Mock(
            return_value=[team_project_access_response_data]
        )

        options = TeamProjectAccessListOptions(page_size=10, Project_id="prj-123")

        result_iter = team_project_accesses_service.list(options)
        items = list(result_iter)

        team_project_accesses_service._list.assert_called_once_with(
            "/api/v2/team-projects",
            params={"page[size]": 10, "filter[project][id]": "prj-123"},
        )
        assert len(items) == 1
        assert isinstance(items[0], TeamProjectAccess)
        assert items[0].id == "tprj-123"

    def test_remove_team_project_access_success(
        self,
        team_project_accesses_service,
        mock_transport,
    ):
        """Test successful remove operation."""
        result = team_project_accesses_service.remove("tprj-123")

        mock_transport.request.assert_called_once_with(
            "DELETE", path="/api/v2/team-projects/tprj-123"
        )
        assert result is None

    def test_remove_team_project_access_invalid_id(self, team_project_accesses_service):
        """Test remove operation with invalid team project access ID."""
        with pytest.raises(InvalidTeamProjectAccessIDError):
            team_project_accesses_service.remove("")
