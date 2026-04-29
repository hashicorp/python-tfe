"""Unit tests for the PolicySets resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidNameError,
    InvalidOrgError,
    InvalidPolicySetIDError,
    RequiredNameError,
)
from pytfe.models.policy_set import (
    PolicySet,
    PolicySetCreateOptions,
    PolicySetListOptions,
    PolicySetReadOptions,
    PolicySetUpdateOptions,
)
from pytfe.models.policy_types import PolicyKind
from pytfe.resources.policy_set import PolicySets


class TestPolicySets:
    """Test the PolicySets service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a PolicySets service with mocked transport."""
        return PolicySets(mock_transport)

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _policy_set_data(
        ps_id: str = "ps-abc123",
        name: str = "example-policy-set",
        kind: str = "sentinel",
    ) -> dict:
        """Minimal JSON:API policy-set dict as returned by the API."""
        return {
            "id": ps_id,
            "type": "policy-sets",
            "attributes": {
                "name": name,
                "description": "A test policy set",
                "kind": kind,
                "global": False,
                "overridable": False,
                "agent-enabled": False,
                "policy-count": 0,
                "workspace-count": 0,
                "project-count": 0,
                "policy-tool-version": None,
                "policies-path": None,
                "created-at": "2024-01-01T00:00:00Z",
                "updated-at": "2024-01-01T00:00:00Z",
            },
            "relationships": {
                "organization": {"data": {"id": "org-test", "type": "organizations"}},
                "workspaces": {"data": []},
                "projects": {"data": []},
                "policies": {"data": []},
                "workspace-exclusions": {"data": []},
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # list()
    # ──────────────────────────────────────────────────────────────────────────

    def test_list_invalid_org_empty_string(self, service):
        """list() raises InvalidOrgError for an empty organization."""
        with pytest.raises(InvalidOrgError):
            list(service.list(""))

    def test_list_invalid_org_none(self, service):
        """list() raises InvalidOrgError for None organization."""
        with pytest.raises(InvalidOrgError):
            list(service.list(None))

    def test_list_returns_iterator_of_policy_sets(self, service):
        """list() returns an iterator that yields PolicySet objects."""
        raw = [
            self._policy_set_data("ps-1", "ps-one"),
            self._policy_set_data("ps-2", "ps-two"),
        ]
        service._list = Mock(return_value=raw)

        result = list(service.list("my-org"))

        assert len(result) == 2
        assert all(isinstance(ps, PolicySet) for ps in result)
        assert result[0].id == "ps-1"
        assert result[0].name == "ps-one"
        assert result[1].id == "ps-2"
        assert result[1].name == "ps-two"

    def test_list_hits_correct_endpoint(self, service):
        """list() calls _list with the correct path."""
        service._list = Mock(return_value=[])

        list(service.list("my-org"))

        service._list.assert_called_once()
        call_path = service._list.call_args[0][0]
        assert call_path == "/api/v2/organizations/my-org/policy-sets"

    def test_list_with_search_option_passes_param(self, service):
        """list() with a search option passes the correct params to _list."""
        service._list = Mock(return_value=[])
        options = PolicySetListOptions(search="my-prefix")

        list(service.list("my-org", options))

        service._list.assert_called_once()
        call_kwargs = service._list.call_args[1]
        assert call_kwargs.get("params", {}).get("search[name]") == "my-prefix"

    def test_list_with_kind_filter(self, service):
        """list() with a kind filter passes filter[kind] param."""
        service._list = Mock(return_value=[])
        options = PolicySetListOptions(kind=PolicyKind.OPA)

        list(service.list("my-org", options))

        service._list.assert_called_once()
        params = service._list.call_args[1].get("params", {})
        assert params.get("filter[kind]") == PolicyKind.OPA

    def test_list_page_number_stripped_from_params(self, service):
        """list() strips page[number] from params so _list handles pagination."""
        service._list = Mock(return_value=[])
        options = PolicySetListOptions(page_number=3, page_size=20)

        list(service.list("my-org", options))

        params = service._list.call_args[1].get("params", {})
        assert "page[number]" not in params
        assert params.get("page[size]") == 20

    # ──────────────────────────────────────────────────────────────────────────
    # read()
    # ──────────────────────────────────────────────────────────────────────────

    def test_read_invalid_id(self, service):
        """read() raises InvalidPolicySetIDError for an invalid ID."""
        with pytest.raises(InvalidPolicySetIDError):
            service.read("")

        with pytest.raises(InvalidPolicySetIDError):
            service.read(None)

    def test_read_hits_correct_endpoint(self, service, mock_transport):
        """read() calls GET /api/v2/policy-sets/{id}."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": self._policy_set_data("ps-abc123")}
        mock_transport.request.return_value = mock_response

        service.read("ps-abc123")

        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/policy-sets/ps-abc123",
            params=None,
        )

    def test_read_returns_policy_set(self, service, mock_transport):
        """read() parses and returns a PolicySet model."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": self._policy_set_data("ps-abc123", "my-ps", "sentinel")
        }
        mock_transport.request.return_value = mock_response

        result = service.read("ps-abc123")

        assert isinstance(result, PolicySet)
        assert result.id == "ps-abc123"
        assert result.name == "my-ps"
        assert result.kind == PolicyKind.SENTINEL

    def test_read_with_options_passes_include_param(self, service, mock_transport):
        """read_with_options() passes include param when provided."""
        from pytfe.models.policy_set import PolicySetIncludeOpt

        mock_response = Mock()
        mock_response.json.return_value = {"data": self._policy_set_data("ps-xyz")}
        mock_transport.request.return_value = mock_response

        options = PolicySetReadOptions(
            include=[PolicySetIncludeOpt.POLICY_SET_POLICIES]
        )
        service.read_with_options("ps-xyz", options)

        call_kwargs = mock_transport.request.call_args[1]
        assert call_kwargs.get("params") is not None

    # ──────────────────────────────────────────────────────────────────────────
    # create()
    # ──────────────────────────────────────────────────────────────────────────

    def test_create_invalid_org(self, service):
        """create() raises InvalidOrgError for an invalid organization."""
        options = PolicySetCreateOptions(name="valid-name")
        with pytest.raises(InvalidOrgError):
            service.create("", options)

    def test_create_missing_name(self, service):
        """create() raises RequiredNameError when name is empty."""
        options = PolicySetCreateOptions(name="")
        with pytest.raises((RequiredNameError, InvalidNameError)):
            service.create("my-org", options)

    def test_create_success(self, service, mock_transport):
        """create() POSTs to the correct endpoint and returns a PolicySet."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": self._policy_set_data("ps-new", "new-policy-set")
        }
        mock_transport.request.return_value = mock_response

        options = PolicySetCreateOptions(name="new-policy-set")
        result = service.create("my-org", options)

        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v2/organizations/my-org/policy-sets"

        assert isinstance(result, PolicySet)
        assert result.id == "ps-new"
        assert result.name == "new-policy-set"

    def test_create_payload_shape(self, service, mock_transport):
        """create() sends a correctly shaped JSON:API payload."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": self._policy_set_data("ps-123")}
        mock_transport.request.return_value = mock_response

        options = PolicySetCreateOptions(name="shaped-ps", kind=PolicyKind.OPA)
        service.create("my-org", options)

        payload = mock_transport.request.call_args[1]["json_body"]
        assert "data" in payload
        data = payload["data"]
        assert data["type"] == "policy-sets"
        assert "attributes" in data
        assert data["attributes"]["name"] == "shaped-ps"

    # ──────────────────────────────────────────────────────────────────────────
    # update()
    # ──────────────────────────────────────────────────────────────────────────

    def test_update_invalid_id(self, service):
        """update() raises InvalidPolicySetIDError for an invalid ID."""
        options = PolicySetUpdateOptions(name="new-name")
        with pytest.raises(InvalidPolicySetIDError):
            service.update("", options)

    def test_update_success(self, service, mock_transport):
        """update() PATCHes the correct endpoint and returns a PolicySet."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": self._policy_set_data("ps-abc123", "updated-name")
        }
        mock_transport.request.return_value = mock_response

        options = PolicySetUpdateOptions(name="updated-name")
        result = service.update("ps-abc123", options)

        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "/api/v2/policy-sets/ps-abc123"

        payload = call_args[1]["json_body"]
        assert payload["data"]["type"] == "policy-sets"
        assert payload["data"]["id"] == "ps-abc123"
        assert payload["data"]["attributes"]["name"] == "updated-name"

        assert isinstance(result, PolicySet)
        assert result.name == "updated-name"

    def test_update_no_attributes_raises(self, service):
        """update() raises ValueError when no attributes are provided."""
        options = PolicySetUpdateOptions()  # all None
        with pytest.raises(ValueError):
            service.update("ps-abc123", options)

    # ──────────────────────────────────────────────────────────────────────────
    # delete()
    # ──────────────────────────────────────────────────────────────────────────

    def test_delete_invalid_id(self, service):
        """delete() raises InvalidPolicySetIDError for an invalid ID."""
        with pytest.raises(InvalidPolicySetIDError):
            service.delete("")

        with pytest.raises(InvalidPolicySetIDError):
            service.delete(None)

    def test_delete_hits_correct_endpoint(self, service, mock_transport):
        """delete() calls DELETE /api/v2/policy-sets/{id}."""
        mock_transport.request.return_value = Mock()

        service.delete("ps-abc123")

        mock_transport.request.assert_called_once_with(
            "DELETE",
            "/api/v2/policy-sets/ps-abc123",
        )

    def test_delete_returns_none(self, service, mock_transport):
        """delete() returns None on success."""
        mock_transport.request.return_value = Mock()

        result = service.delete("ps-abc123")

        assert result is None
