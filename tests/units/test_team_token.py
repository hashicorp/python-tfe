# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the team_token module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidOrgError, InvalidTeamIDError, InvalidTokenIDError
from pytfe.models.team import Team
from pytfe.models.team_token import (
    CreatedByChoice,
    TeamToken,
    TeamTokenCreateOptions,
    TeamTokenListOptions,
)
from pytfe.models.user import User
from pytfe.resources.team_token import TeamTokens


class TestTeamTokens:
    """Test the TeamTokens service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a TeamTokens service with mocked transport."""
        return TeamTokens(mock_transport)

    @pytest.fixture
    def token_api_data(self):
        """Typical API response for a single team token (user created-by)."""
        return {
            "id": "at-abc123",
            "type": "authentication-tokens",
            "attributes": {
                "created-at": "2026-05-01T10:00:00.000Z",
                "last-used-at": None,
                "description": "My token",
                "token": "secret-token-value",
                "expired-at": "2027-05-01T10:00:00.000Z",
            },
            "relationships": {
                "team": {"data": {"id": "team-xyz789", "type": "teams"}},
                "created-by": {"data": {"id": "user-111", "type": "users"}},
            },
        }

    @pytest.fixture
    def token_api_data_team_creator(self):
        """API response where the token was created by a team."""
        return {
            "id": "at-team001",
            "type": "authentication-tokens",
            "attributes": {
                "created-at": "2026-05-01T10:00:00.000Z",
                "last-used-at": None,
                "description": None,
                "token": None,
                "expired-at": None,
            },
            "relationships": {
                "team": {"data": {"id": "team-xyz789", "type": "teams"}},
                "created-by": {"data": {"id": "team-abc", "type": "teams"}},
            },
        }

    # ── Model tests ──────────────────────────────────────────────────────────

    def test_team_token_model_fields(self):
        """TeamToken model stores all fields."""
        t = TeamToken(id="at-abc123", description="My token", token="secret")
        assert t.id == "at-abc123"
        assert t.description == "My token"
        assert t.token == "secret"

    def test_team_token_defaults(self):
        """TeamToken optional fields default to None."""
        t = TeamToken(id="at-min")
        assert t.description is None
        assert t.token is None
        assert t.expired_at is None
        assert t.last_used_at is None
        assert t.team is None
        assert t.created_by is None

    def test_create_options_defaults(self):
        """TeamTokenCreateOptions defaults all fields to None."""
        opts = TeamTokenCreateOptions()
        assert opts.description is None
        assert opts.expired_at is None

    def test_create_options_with_description(self):
        """TeamTokenCreateOptions stores description."""
        opts = TeamTokenCreateOptions(description="CI token")
        assert opts.description == "CI token"

    def test_create_options_serializes_with_aliases(self):
        """TeamTokenCreateOptions serialises with API aliases."""
        from datetime import datetime, timezone

        expiry = datetime(2027, 1, 1, tzinfo=timezone.utc)
        opts = TeamTokenCreateOptions(description="Test", expired_at=expiry)
        dumped = opts.model_dump(by_alias=True, exclude_none=True)
        assert dumped["description"] == "Test"
        assert "expired-at" in dumped

    def test_list_options(self):
        """TeamTokenListOptions stores pagination and filter params."""
        opts = TeamTokenListOptions(page_size=10, query="my-team", sort="expired-at")
        assert opts.page_size == 10
        assert opts.query == "my-team"
        assert opts.sort == "expired-at"

    def test_created_by_choice_user(self):
        """CreatedByChoice can hold a User."""
        u = User(id="user-123")
        choice = CreatedByChoice(user=u)
        assert choice.user.id == "user-123"
        assert choice.team is None
        assert choice.organization is None

    def test_created_by_choice_team(self):
        """CreatedByChoice can hold a Team."""
        t = Team(id="team-abc")
        choice = CreatedByChoice(team=t)
        assert choice.team.id == "team-abc"
        assert choice.user is None

    # ── Parser tests ─────────────────────────────────────────────────────────

    def test_team_token_from_full_data(self, service, token_api_data):
        """_team_token_from parses attributes and typed relation stubs."""
        result = service._team_token_from(token_api_data)

        assert isinstance(result, TeamToken)
        assert result.id == "at-abc123"
        assert result.description == "My token"
        assert result.token == "secret-token-value"

        # team relation is a typed Team stub
        assert isinstance(result.team, Team)
        assert result.team.id == "team-xyz789"

        # created_by is a CreatedByChoice wrapping a User stub
        assert isinstance(result.created_by, CreatedByChoice)
        assert isinstance(result.created_by.user, User)
        assert result.created_by.user.id == "user-111"

    def test_team_token_from_team_creator(self, service, token_api_data_team_creator):
        """_team_token_from handles team-type created-by relation."""
        result = service._team_token_from(token_api_data_team_creator)

        assert isinstance(result.team, Team)
        assert isinstance(result.created_by, CreatedByChoice)
        assert isinstance(result.created_by.team, Team)
        assert result.created_by.team.id == "team-abc"

    def test_team_token_from_no_relationships(self, service):
        """_team_token_from handles missing relationship data."""
        data = {
            "id": "at-min",
            "attributes": {"description": None, "token": None},
            "relationships": {},
        }
        result = service._team_token_from(data)

        assert result.id == "at-min"
        assert result.team is None
        assert result.created_by is None

    def test_team_token_from_null_relationship_data(self, service):
        """_team_token_from handles null data inside relationship."""
        data = {
            "id": "at-null",
            "attributes": {},
            "relationships": {
                "team": {"data": None},
                "created-by": {"data": None},
            },
        }
        result = service._team_token_from(data)
        assert result.team is None
        assert result.created_by is None

    # ── Resource method tests ─────────────────────────────────────────────────

    def test_create_legacy_success(self, service, mock_transport, token_api_data):
        """create() without description uses legacy endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": token_api_data}
        mock_transport.request.return_value = mock_response

        result = service.create(team_id="team-xyz789")

        args, kwargs = mock_transport.request.call_args
        assert args[0] == "POST"
        assert kwargs["path"] == "/api/v2/teams/team-xyz789/authentication-token"
        assert kwargs["json_body"]["data"]["type"] == "authentication-token"
        assert isinstance(result, TeamToken)
        assert result.id == "at-abc123"

    def test_create_with_description_uses_new_endpoint(
        self, service, mock_transport, token_api_data
    ):
        """create_with_options() with description uses the multi-token endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": token_api_data}
        mock_transport.request.return_value = mock_response

        opts = TeamTokenCreateOptions(description="CI token")
        service.create_with_options(team_id="team-xyz789", options=opts)

        args, kwargs = mock_transport.request.call_args
        assert kwargs["path"] == "/api/v2/teams/team-xyz789/authentication-tokens"
        assert kwargs["json_body"]["data"]["type"] == "authentication-tokens"

    def test_create_with_options_invalid_team_id(self, service):
        """create_with_options() raises InvalidTeamIDError for a bad team ID."""
        with pytest.raises(InvalidTeamIDError):
            service.create_with_options(team_id="not valid!")

    def test_create_invalid_team_id(self, service):
        """create() raises InvalidTeamIDError for a bad team ID."""
        with pytest.raises(InvalidTeamIDError):
            service.create(team_id="not valid!")

    def test_read_success(self, service, mock_transport, token_api_data):
        """read() GETs the legacy endpoint and returns a TeamToken."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": token_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read(team_id="team-xyz789")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/teams/team-xyz789/authentication-token"
        )
        assert isinstance(result, TeamToken)
        assert result.id == "at-abc123"

    def test_read_invalid_team_id(self, service):
        """read() raises InvalidTeamIDError for a bad team ID."""
        with pytest.raises(InvalidTeamIDError):
            service.read(team_id="bad id")

    def test_read_by_id_success(self, service, mock_transport, token_api_data):
        """read_by_id() GETs the correct path and returns a TeamToken."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": token_api_data}
        mock_transport.request.return_value = mock_response

        result = service.read_by_id(token_id="at-abc123")

        mock_transport.request.assert_called_once_with(
            "GET", path="/api/v2/authentication-tokens/at-abc123"
        )
        assert isinstance(result, TeamToken)

    def test_read_by_id_invalid_token_id(self, service):
        """read_by_id() raises InvalidTokenIDError for a bad token ID."""
        with pytest.raises(InvalidTokenIDError):
            service.read_by_id(token_id="not valid!")

    def test_list_success(self, service, token_api_data):
        """list() yields TeamToken objects from paginated results."""
        service._list = Mock(return_value=[token_api_data])

        results = list(service.list(organization="my-org"))

        service._list.assert_called_once_with(
            path="/api/v2/organizations/my-org/team-tokens",
            params={},
        )
        assert len(results) == 1
        assert isinstance(results[0], TeamToken)
        assert results[0].id == "at-abc123"

    def test_list_with_options(self, service, token_api_data):
        """list() passes pagination and filter params."""
        service._list = Mock(return_value=[token_api_data])

        opts = TeamTokenListOptions(page_size=5, query="my-team", sort="expired-at")
        list(service.list(organization="my-org", options=opts))

        _, kwargs = service._list.call_args
        assert kwargs["params"]["page[size]"] == 5
        assert kwargs["params"]["q"] == "my-team"
        assert kwargs["params"]["sort"] == "expired-at"

    def test_list_empty(self, service):
        """list() returns empty iterator when no tokens exist."""
        service._list = Mock(return_value=[])
        results = list(service.list(organization="my-org"))
        assert results == []

    def test_list_invalid_org(self, service):
        """list() raises InvalidOrgError for a bad organization name."""
        with pytest.raises(InvalidOrgError):
            list(service.list(organization="not valid!"))

    def test_delete_success(self, service, mock_transport):
        """delete() DELETEs the legacy token endpoint."""
        result = service.delete(team_id="team-xyz789")

        mock_transport.request.assert_called_once_with(
            "DELETE", path="/api/v2/teams/team-xyz789/authentication-token"
        )
        assert result is None

    def test_delete_invalid_team_id(self, service):
        """delete() raises InvalidTeamIDError for a bad team ID."""
        with pytest.raises(InvalidTeamIDError):
            service.delete(team_id="bad id")

    def test_delete_by_id_success(self, service, mock_transport):
        """delete_by_id() DELETEs by token ID."""
        result = service.delete_by_id(token_id="at-abc123")

        mock_transport.request.assert_called_once_with(
            "DELETE", path="/api/v2/authentication-tokens/at-abc123"
        )
        assert result is None

    def test_delete_by_id_invalid_token_id(self, service):
        """delete_by_id() raises InvalidTokenIDError for a bad token ID."""
        with pytest.raises(InvalidTokenIDError):
            service.delete_by_id(token_id="not valid!")
