"""Unit tests for the state_versions module."""

from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import NotFound
from pytfe.models.state_version import (
    StateVersion,
    StateVersionCreateOptions,
    StateVersionCurrentOptions,
    StateVersionIncludeOpt,
    StateVersionListOptions,
    StateVersionReadOptions,
    StateVersionStatus,
)
from pytfe.models.state_version_output import StateVersionOutputsListOptions
from pytfe.resources.state_versions import StateVersions


class TestStateVersions:
    """Test the StateVersions service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def state_versions_service(self, mock_transport):
        """Create a StateVersions service with mocked transport."""
        return StateVersions(mock_transport)

    def test_list_state_versions_iterator(self, state_versions_service):
        """Test list() returns an iterator of StateVersion models."""
        mock_items = [
            {
                "id": "sv-1",
                "type": "state-versions",
                "attributes": {
                    "created-at": "2024-01-01T00:00:00Z",
                    "serial": 9,
                    "state-version": 4,
                    "status": "finalized",
                    "hosted-state-download-url": "https://example.com/download-1",
                    "hosted-json-state-download-url": "https://example.com/json-download-1",
                    "resources-processed": True,
                    "terraform-version": "1.7.5",
                },
                "relationships": {
                    "workspace": {"data": {"id": "ws-123", "type": "workspaces"}},
                    "run": {"data": {"id": "run-123", "type": "runs"}},
                },
                "links": {"self": "/api/v2/state-versions/sv-1"},
            },
            {
                "id": "sv-2",
                "type": "state-versions",
                "attributes": {
                    "created-at": "2024-01-02T00:00:00Z",
                    "serial": 10,
                    "state-version": 4,
                    "status": "pending",
                },
                "relationships": {
                    "workspace": {"data": {"id": "ws-123", "type": "workspaces"}},
                },
                "links": {"self": "/api/v2/state-versions/sv-2"},
            },
        ]

        with patch.object(state_versions_service, "_list") as mock_list:
            mock_list.return_value = mock_items

            options = StateVersionListOptions(
                page_size=2,
                organization="demo-org",
                workspace="demo-ws",
            )
            result = list(state_versions_service.list(options))

            mock_list.assert_called_once()
            call_args = mock_list.call_args
            assert call_args[0][0].startswith("/api/v2/state-versions?")
            params = call_args[1]["params"]
            assert params["page[size]"] == 2
            assert params["filter[organization][name]"] == "demo-org"
            assert params["filter[workspace][name]"] == "demo-ws"

            assert len(result) == 2
            assert all(isinstance(item, StateVersion) for item in result)
            assert result[0].id == "sv-1"
            assert result[0].status == StateVersionStatus.FINALIZED
            assert result[1].id == "sv-2"
            assert result[1].status == StateVersionStatus.PENDING

    def test_read_state_version_invalid_id(self, state_versions_service):
        """Test read() with invalid state version id."""
        with pytest.raises(ValueError, match="invalid state version id"):
            state_versions_service.read("")

    def test_read_state_version_success(self, state_versions_service, mock_transport):
        """Test successful read() operation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "sv-read-1",
                "type": "state-versions",
                "attributes": {
                    "created-at": "2024-01-01T00:00:00Z",
                    "serial": 9,
                    "state-version": 4,
                    "status": "finalized",
                    "hosted-state-download-url": "https://example.com/download",
                    "resources-processed": True,
                },
                "relationships": {
                    "workspace": {"data": {"id": "ws-123", "type": "workspaces"}},
                    "run": {"data": {"id": "run-123", "type": "runs"}},
                },
                "links": {"self": "/api/v2/state-versions/sv-read-1"},
            }
        }
        mock_transport.request.return_value = mock_response

        result = state_versions_service.read("sv-read-1")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/state-versions/sv-read-1"
        )
        assert result.id == "sv-read-1"
        assert result.status == StateVersionStatus.FINALIZED
        assert result.hosted_state_download_url == "https://example.com/download"

    def test_read_with_options_success(self, state_versions_service, mock_transport):
        """Test successful read_with_options() operation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "sv-read-2",
                "type": "state-versions",
                "attributes": {
                    "created-at": "2024-01-01T00:00:00Z",
                    "status": "pending",
                },
                "relationships": {
                    "outputs": {
                        "data": [{"id": "wsout-1", "type": "state-version-outputs"}]
                    }
                },
            }
        }
        mock_transport.request.return_value = mock_response

        options = StateVersionReadOptions(
            include=[StateVersionIncludeOpt.OUTPUTS, StateVersionIncludeOpt.RUN]
        )
        result = state_versions_service.read_with_options("sv-read-2", options)

        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/state-versions/sv-read-2",
            params={"include": "outputs,run"},
        )
        assert result.id == "sv-read-2"
        assert result.status == StateVersionStatus.PENDING

    def test_read_current_with_options_success(
        self, state_versions_service, mock_transport
    ):
        """Test successful read_current_with_options() operation.

        Mock payload shape follows docs sample for:
        GET /api/v2/workspaces/:workspace_id/current-state-version
        """
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "sv-current-1",
                "type": "state-versions",
                "attributes": {
                    "created-at": "2024-01-01T00:00:00Z",
                    "serial": 9,
                    "status": "finalized",
                    "resources-processed": True,
                },
                "relationships": {
                    "workspace": {"data": {"id": "ws-123", "type": "workspaces"}},
                    "created-by": {"data": {"id": "user-123", "type": "users"}},
                },
            }
        }
        mock_transport.request.return_value = mock_response

        options = StateVersionCurrentOptions(
            include=[StateVersionIncludeOpt.CREATED_BY]
        )
        result = state_versions_service.read_current_with_options("ws-123", options)

        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/workspaces/ws-123/current-state-version",
            params={"include": "created_by"},
        )
        assert result.id == "sv-current-1"

    def test_create_state_version_success(self, state_versions_service, mock_transport):
        """Test successful create() operation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "sv-new-1",
                "type": "state-versions",
                "attributes": {
                    "created-at": "2024-01-01T00:00:00Z",
                    "status": "pending",
                    "hosted-state-upload-url": "https://example.com/upload",
                    "hosted-json-state-upload-url": "https://example.com/json-upload",
                    "serial": 10,
                },
                "links": {"self": "/api/v2/state-versions/sv-new-1"},
            }
        }
        mock_transport.request.return_value = mock_response

        options = StateVersionCreateOptions(serial=10, md5="abc123")

        with patch.object(
            state_versions_service, "_resolve_workspace_id", return_value="ws-123"
        ):
            result = state_versions_service.create("my-workspace", options)

        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/workspaces/ws-123/state-versions",
            json_body={
                "data": {
                    "type": "state-versions",
                    "attributes": {
                        "serial": 10,
                        "md5": "abc123",
                    },
                }
            },
        )
        assert result.id == "sv-new-1"
        assert result.status == StateVersionStatus.PENDING

    def test_download_state_version_not_found_when_url_missing(
        self, state_versions_service
    ):
        """Test download() raises NotFound if signed download URL is missing."""
        sv = StateVersion(
            id="sv-404",
            created_at="2024-01-01T00:00:00Z",
            status=StateVersionStatus.FINALIZED,
            hosted_state_download_url=None,
        )

        with patch.object(state_versions_service, "read", return_value=sv):
            with pytest.raises(NotFound, match="download url not available"):
                state_versions_service.download("sv-404")

    def test_download_state_version_success(
        self, state_versions_service, mock_transport
    ):
        """Test successful download() operation using signed URL."""
        sv = StateVersion(
            id="sv-dl-1",
            created_at="2024-01-01T00:00:00Z",
            status=StateVersionStatus.FINALIZED,
            hosted_state_download_url="https://example.com/signed-download",
        )
        mock_response = Mock()
        mock_response.content = b"{}"
        mock_transport.request.return_value = mock_response

        with patch.object(state_versions_service, "read", return_value=sv):
            result = state_versions_service.download("sv-dl-1")

        mock_transport.request.assert_called_once_with(
            "GET",
            "https://example.com/signed-download",
            allow_redirects=True,
            headers={"Accept": "application/json"},
        )
        assert result == b"{}"

    def test_list_outputs_success(self, state_versions_service):
        """Test successful list_outputs() iterator operation."""
        mock_items = [
            {
                "id": "wsout-1",
                "attributes": {
                    "name": "vpc_id",
                    "sensitive": False,
                    "type": "string",
                    "value": "vpc-123",
                },
            }
        ]

        with patch.object(state_versions_service, "_list") as mock_list:
            mock_list.return_value = mock_items

            options = StateVersionOutputsListOptions(page_size=5)
            result = list(state_versions_service.list_outputs("sv-outputs-1", options))

            mock_list.assert_called_once_with(
                "/api/v2/state-versions/sv-outputs-1/outputs",
                params={"page[size]": 5},
            )
            assert len(result) == 1
            assert result[0].id == "wsout-1"
