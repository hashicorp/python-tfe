from datetime import datetime
from unittest.mock import MagicMock, Mock
import io

import pytest

from pytfe import TFEClient, TFEConfig
from pytfe.errors import InvalidQueryRunIDError, InvalidWorkspaceIDError
from pytfe.models.query_run import (
    QueryRun,
    QueryRunActions,
    QueryRunCancelOptions,
    QueryRunCreateOptions,
    QueryRunForceCancelOptions,
    QueryRunIncludeOpt,
    QueryRunList,
    QueryRunListOptions,
    QueryRunReadOptions,
    QueryRunSource,
    QueryRunStatus,
    QueryRunStatusTimestamps,
    QueryRunVariable,
)


class TestQueryRunModels:
    """Test query run models and validation."""

    def test_query_run_model_basic(self):
        """Test basic QueryRun model creation."""
        query_run = QueryRun(
            id="query-test123",
            source=QueryRunSource.API,
            status=QueryRunStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert query_run.id == "query-test123"
        assert query_run.source == QueryRunSource.API
        assert query_run.status == QueryRunStatus.PENDING

    def test_query_run_status_enum(self):
        """Test QueryRunStatus enum values."""
        assert QueryRunStatus.PENDING == "pending"
        assert QueryRunStatus.QUEUED == "queued"
        assert QueryRunStatus.RUNNING == "running"
        assert QueryRunStatus.FINISHED == "finished"
        assert QueryRunStatus.ERRORED == "errored"
        assert QueryRunStatus.CANCELED == "canceled"

    def test_query_run_source_enum(self):
        """Test QueryRunSource enum values."""
        assert QueryRunSource.API == "tfe-api"

    def test_query_run_create_options(self):
        """Test QueryRunCreateOptions model."""
        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id="ws-test123",
        )
        assert options.source == QueryRunSource.API
        assert options.workspace_id == "ws-test123"

    def test_query_run_list_options(self):
        """Test QueryRunListOptions model."""
        options = QueryRunListOptions(
            page_number=2,
            page_size=50,
            include=[QueryRunIncludeOpt.CREATED_BY],
        )
        assert options.page_number == 2
        assert options.page_size == 50
        assert QueryRunIncludeOpt.CREATED_BY in options.include

    def test_query_run_actions(self):
        """Test QueryRunActions model."""
        actions = QueryRunActions(
            is_cancelable=True,
            is_force_cancelable=False,
        )
        assert actions.is_cancelable is True
        assert actions.is_force_cancelable is False


class TestQueryRunOperations:
    """Test query run operations."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        config = TFEConfig(address="https://test.terraform.io", token="test-token")
        return TFEClient(config)

    @pytest.fixture
    def mock_list_response(self):
        """Create a mock list response."""
        mock = Mock()
        mock.json.return_value = {
            "data": [
                {
                    "id": "query-test123",
                    "type": "queries",
                    "attributes": {
                        "source": "tfe-api",
                        "status": "finished",
                        "created-at": "2023-01-01T00:00:00Z",
                        "updated-at": "2023-01-01T00:05:00Z",
                        "log-read-url": "https://archivist.terraform.io/v1/object/...",
                    },
                }
            ],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "total-pages": 1,
                    "prev-page": None,
                    "next-page": None,
                    "total-count": 1,
                }
            },
        }
        return mock

    def test_list_query_runs(self, client, mock_list_response):
        """Test listing query runs."""
        client._transport.request = MagicMock(return_value=mock_list_response)

        result = client.query_runs.list("ws-test123")

        assert isinstance(result, QueryRunList)
        assert len(result.items) == 1
        assert result.items[0].id == "query-test123"
        assert result.items[0].source == QueryRunSource.API
        assert result.current_page == 1
        assert result.total_count == 1

        client._transport.request.assert_called_once_with(
            "GET", "/api/v2/workspaces/ws-test123/queries", params=None
        )

    def test_list_query_runs_with_options(self, client, mock_list_response):
        """Test listing query runs with options."""
        client._transport.request = MagicMock(return_value=mock_list_response)

        options = QueryRunListOptions(
            page_number=2,
            page_size=25,
            include=[QueryRunIncludeOpt.CREATED_BY],
        )
        result = client.query_runs.list("ws-test123", options)

        assert isinstance(result, QueryRunList)
        client._transport.request.assert_called_once_with(
            "GET",
            "/api/v2/workspaces/ws-test123/queries",
            params={
                "page[number]": 2,
                "page[size]": 25,
                "include": [QueryRunIncludeOpt.CREATED_BY],
            },
        )

    def test_list_invalid_workspace_id(self, client):
        """Test listing query runs with invalid workspace ID."""
        with pytest.raises(InvalidWorkspaceIDError):
            client.query_runs.list("")

    def test_create_query_run(self, client):
        """Test creating a query run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "query-new123",
                "type": "queries",
                "attributes": {
                    "source": "tfe-api",
                    "status": "pending",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:00:00Z",
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id="ws-test123",
        )
        result = client.query_runs.create(options)

        assert isinstance(result, QueryRun)
        assert result.id == "query-new123"
        assert result.source == QueryRunSource.API
        assert result.status == QueryRunStatus.PENDING

        # Verify the call was made with correct structure
        call_args = client._transport.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v2/queries"
        json_body = call_args[1]["json_body"]
        assert json_body["data"]["type"] == "queries"
        assert "relationships" in json_body["data"]
        assert json_body["data"]["relationships"]["workspace"]["data"]["id"] == "ws-test123"

    def test_read_query_run(self, client):
        """Test reading a query run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "query-test123",
                "type": "queries",
                "attributes": {
                    "source": "tfe-api",
                    "status": "finished",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:05:00Z",
                    "log-read-url": "https://archivist.terraform.io/v1/object/...",
                    "actions": {
                        "is-cancelable": False,
                        "is-force-cancelable": False,
                    },
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        result = client.query_runs.read("query-test123")

        assert isinstance(result, QueryRun)
        assert result.id == "query-test123"
        assert result.status == QueryRunStatus.FINISHED

        client._transport.request.assert_called_once_with(
            "GET", "/api/v2/queries/query-test123"
        )

    def test_read_query_run_with_options(self, client):
        """Test reading a query run with options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "query-test123",
                "type": "queries",
                "attributes": {
                    "source": "tfe-api",
                    "status": "finished",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:05:00Z",
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        options = QueryRunReadOptions(
            include=[QueryRunIncludeOpt.CREATED_BY, QueryRunIncludeOpt.CONFIGURATION_VERSION]
        )
        result = client.query_runs.read_with_options("query-test123", options)

        assert isinstance(result, QueryRun)
        assert result.id == "query-test123"

        client._transport.request.assert_called_once_with(
            "GET",
            "/api/v2/queries/query-test123",
            params={"include": [QueryRunIncludeOpt.CREATED_BY, QueryRunIncludeOpt.CONFIGURATION_VERSION]},
        )

    def test_read_invalid_query_run_id(self, client):
        """Test reading with invalid query run ID."""
        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.read("")

    def test_query_run_logs(self, client):
        """Test retrieving query run logs."""
        # Mock the read call first
        mock_read_response = Mock()
        mock_read_response.json.return_value = {
            "data": {
                "id": "query-test123",
                "type": "queries",
                "attributes": {
                    "source": "tfe-api",
                    "status": "finished",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:05:00Z",
                    "log-read-url": "https://archivist.terraform.io/v1/object/dmF1bHQ6djE6L...",
                },
            }
        }
        
        # Mock the logs fetch
        mock_logs_response = Mock()
        mock_logs_response.content = b"Starting query execution...\nQuery completed successfully."
        
        client._transport.request = MagicMock(side_effect=[mock_read_response, mock_logs_response])

        result = client.query_runs.logs("query-test123")

        assert isinstance(result, io.IOBase)
        log_content = result.read()
        assert b"Starting query execution" in log_content

        # Verify calls
        assert client._transport.request.call_count == 2

    def test_query_run_logs_no_url(self, client):
        """Test retrieving logs when no log URL is available."""
        mock_read_response = Mock()
        mock_read_response.json.return_value = {
            "data": {
                "id": "query-test123",
                "type": "queries",
                "attributes": {
                    "source": "tfe-api",
                    "status": "pending",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:00:00Z",
                },
            }
        }
        
        client._transport.request = MagicMock(return_value=mock_read_response)

        with pytest.raises(ValueError, match="does not have a log URL"):
            client.query_runs.logs("query-test123")

    def test_cancel_query_run(self, client):
        """Test canceling a query run."""
        mock_response = Mock()
        mock_response.status_code = 202
        client._transport.request = MagicMock(return_value=mock_response)

        client.query_runs.cancel("query-test123")

        client._transport.request.assert_called_once_with(
            "POST",
            "/api/v2/queries/query-test123/actions/cancel",
            json_body=None,
        )

    def test_cancel_query_run_with_options(self, client):
        """Test canceling a query run with options."""
        mock_response = Mock()
        mock_response.status_code = 202
        client._transport.request = MagicMock(return_value=mock_response)

        options = QueryRunCancelOptions(comment="Canceling for testing")
        client.query_runs.cancel("query-test123", options)

        call_args = client._transport.request.call_args
        assert call_args[0][1] == "/api/v2/queries/query-test123/actions/cancel"
        json_body = call_args[1]["json_body"]
        assert json_body["data"]["attributes"]["comment"] == "Canceling for testing"

    def test_force_cancel_query_run(self, client):
        """Test force canceling a query run."""
        mock_response = Mock()
        mock_response.status_code = 202
        client._transport.request = MagicMock(return_value=mock_response)

        client.query_runs.force_cancel("query-test123")

        client._transport.request.assert_called_once_with(
            "POST",
            "/api/v2/queries/query-test123/actions/force-cancel",
            json_body=None,
        )

    def test_cancel_invalid_query_run_id(self, client):
        """Test canceling with invalid query run ID."""
        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.cancel("")

    def test_force_cancel_invalid_query_run_id(self, client):
        """Test force canceling with invalid query run ID."""
        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.force_cancel("")
