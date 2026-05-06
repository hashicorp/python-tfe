"""Unit tests for the team resource."""

from unittest.mock import Mock, patch

import pytest
from pytfe._http import HTTPTransport
from pytfe.errors import ERR_INVALID_ORG, InvalidTeamIDError
from pytfe.models import (
    Team,
    TeamCreateOptions,
    TeamIncludeOpt,
    TeamListOptions,
    TeamUpdateOptions,
)
from pytfe.resources.team import Teams


class TestTeams:
    """Test the Teams service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def teams_service(self, mock_transport):
        """Create a Teams service with mocked transport."""
        return Teams(mock_transport)

    def test_list_teams_validations(self, teams_service):
        """Test list method with invalid organization values."""

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            list(teams_service.list(""))

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            list(teams_service.list(None))

    def test_list_teams_success_without_options(self, teams_service):
        """Test successful list operation without options."""

        mock_data = [
            {
                "id": "team-123",
                "attributes": {
                    "name": "owners",
                    "visibility": "organization",
                    "is-unified": False,
                    "user-count": 2,
                    "allow-member-token-management": False,
                },
                "relationships": {},
            }
        ]

        with patch.object(teams_service, "_list") as mock_list:
            mock_list.return_value = iter(mock_data)

            result = list(teams_service.list("my-org"))

            mock_list.assert_called_once_with(
                "/api/v2/organizations/my-org/teams", params={}
            )

            assert len(result) == 1
            assert isinstance(result[0], Team)
            assert result[0].id == "team-123"
            assert result[0].name == "owners"
            assert result[0].visibility == "organization"
            assert result[0].user_count == 2

    def test_list_teams_with_options(self, teams_service):
        """Test successful list operation with list options."""

        with patch.object(teams_service, "_list") as mock_list:
            mock_list.return_value = iter([])

            options = TeamListOptions(
                page_size=10,
                query="owner",
                names=["owners", "admins"],
                include=[
                    TeamIncludeOpt.TEAM_USERS,
                    TeamIncludeOpt.TEAM_ORGANIZATION_MEMBERSHIPS,
                ],
            )

            result = list(teams_service.list("my-org", options))

            mock_list.assert_called_once_with(
                "/api/v2/organizations/my-org/teams",
                params={
                    "page[size]": 10,
                    "q": "owner",
                    "filter[names]": ["owners", "admins"],
                    "include": "users,organization-memberships",
                },
            )
            assert len(result) == 0

    def test_create_team_validations(self, teams_service):
        """Test create method validations."""

        options = TeamCreateOptions(name="platform", visibility="organization")

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            teams_service.create("", options)

    def test_create_team_success(self, teams_service, mock_transport):
        """Test successful create operation."""

        mock_response_data = {
            "data": {
                "id": "team-456",
                "attributes": {
                    "name": "platform",
                    "visibility": "organization",
                    "is-unified": False,
                    "user-count": 0,
                    "allow-member-token-management": True,
                },
                "relationships": {},
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = TeamCreateOptions(
            name="platform",
            visibility="organization",
            allow_member_token_management=True,
        )

        result = teams_service.create("my-org", options)

        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/organizations/my-org/teams",
            json_body={
                "data": {
                    "attributes": {
                        "name": "platform",
                        "visibility": "organization",
                        "allow-member-token-management": True,
                    },
                    "type": "teams",
                }
            },
        )

        assert isinstance(result, Team)
        assert result.id == "team-456"
        assert result.name == "platform"
        assert result.visibility == "organization"

    def test_update_team_validations(self, teams_service):
        """Test update method validations."""

        options = TeamUpdateOptions(name="new-name", visibility="organization")

        with pytest.raises(InvalidTeamIDError):
            teams_service.update("", options)

    def test_update_team_success(self, teams_service, mock_transport):
        """Test successful update operation."""

        mock_response_data = {
            "data": {
                "id": "team-789",
                "attributes": {
                    "name": "platform-admins",
                    "visibility": "secret",
                    "is-unified": False,
                    "user-count": 1,
                    "allow-member-token-management": False,
                },
                "relationships": {},
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = TeamUpdateOptions(name="platform-admins", visibility="secret")

        result = teams_service.update("team-789", options)

        mock_transport.request.assert_called_once_with(
            "PATCH",
            path="/api/v2/teams/team-789",
            json_body={
                "data": {
                    "attributes": {
                        "name": "platform-admins",
                        "visibility": "secret",
                    },
                    "type": "teams",
                }
            },
        )

        assert isinstance(result, Team)
        assert result.id == "team-789"
        assert result.name == "platform-admins"
        assert result.visibility == "secret"

    def test_read_team_validations(self, teams_service):
        """Test read method validations."""

        with pytest.raises(InvalidTeamIDError):
            teams_service.read("")

    def test_read_team_success(self, teams_service, mock_transport):
        """Test successful read operation."""

        mock_response_data = {
            "data": {
                "id": "team-789",
                "attributes": {
                    "name": "platform-admins",
                    "visibility": "secret",
                    "is-unified": False,
                    "user-count": 1,
                    "allow-member-token-management": False,
                },
                "relationships": {},
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        result = teams_service.read("team-789")

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/teams/team-789",
        )

        assert isinstance(result, Team)
        assert result.id == "team-789"
        assert result.name == "platform-admins"

    def test_delete_team_validations(self, teams_service):
        """Test delete method validations."""

        with pytest.raises(InvalidTeamIDError):
            teams_service.delete("")

    def test_delete_team_success(self, teams_service, mock_transport):
        """Test successful delete operation."""

        result = teams_service.delete("team-789")

        mock_transport.request.assert_called_once_with(
            "DELETE",
            path="/api/v2/teams/team-789",
        )
        assert result is None
