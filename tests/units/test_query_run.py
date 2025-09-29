from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from tfe import TFEClient, TFEConfig
from tfe.errors import InvalidOrgError, InvalidQueryRunIDError
from tfe.models.query_run import (
    QueryRun,
    QueryRunCancelOptions,
    QueryRunCreateOptions,
    QueryRunForceCancelOptions,
    QueryRunList,
    QueryRunListOptions,
    QueryRunLogs,
    QueryRunReadOptions,
    QueryRunResults,
    QueryRunStatus,
    QueryRunType,
)


class TestQueryRunModels:
    """Test query run models and validation."""

    def test_query_run_model_basic(self):
        """Test basic QueryRun model creation."""
        query_run = QueryRun(
            id="qr-test123",
            query="SELECT * FROM runs WHERE status = 'completed'",
            query_type=QueryRunType.FILTER,
            status=QueryRunStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert query_run.id == "qr-test123"
        assert query_run.query == "SELECT * FROM runs WHERE status = 'completed'"
        assert query_run.query_type == QueryRunType.FILTER
        assert query_run.status == QueryRunStatus.COMPLETED

    def test_query_run_status_enum(self):
        """Test QueryRunStatus enum values."""
        assert QueryRunStatus.PENDING == "pending"
        assert QueryRunStatus.RUNNING == "running"
        assert QueryRunStatus.COMPLETED == "completed"
        assert QueryRunStatus.ERRORED == "errored"
        assert QueryRunStatus.CANCELED == "canceled"

    def test_query_run_type_enum(self):
        """Test QueryRunType enum values."""
        assert QueryRunType.FILTER == "filter"
        assert QueryRunType.SEARCH == "search"
        assert QueryRunType.ANALYTICS == "analytics"

    def test_query_run_create_options(self):
        """Test QueryRunCreateOptions model."""
        options = QueryRunCreateOptions(
            query="SELECT * FROM workspaces",
            query_type=QueryRunType.SEARCH,
            organization_name="test-org",
            timeout_seconds=300,
            max_results=1000,
        )
        assert options.query == "SELECT * FROM workspaces"
        assert options.query_type == QueryRunType.SEARCH
        assert options.organization_name == "test-org"
        assert options.timeout_seconds == 300
        assert options.max_results == 1000

    def test_query_run_list_options(self):
        """Test QueryRunListOptions model."""
        options = QueryRunListOptions(
            page_number=2,
            page_size=50,
            query_type=QueryRunType.FILTER,
            status=QueryRunStatus.COMPLETED,
            organization_name="test-org",
        )
        assert options.page_number == 2
        assert options.page_size == 50
        assert options.query_type == QueryRunType.FILTER
        assert options.status == QueryRunStatus.COMPLETED
        assert options.organization_name == "test-org"


class TestQueryRunOperations:
    """Test query run operations."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        config = TFEConfig(address="https://test.terraform.io", token="test-token")
        return TFEClient(config)

    @pytest.fixture
    def mock_response(self):
        """Create a mock response."""
        mock = Mock()
        mock.json.return_value = {
            "data": [
                {
                    "id": "qr-test123",
                    "type": "query-runs",
                    "attributes": {
                        "query": "SELECT * FROM runs",
                        "query-type": "filter",
                        "status": "completed",
                        "results-count": 42,
                        "created-at": "2023-01-01T00:00:00Z",
                        "updated-at": "2023-01-01T00:05:00Z",
                        "started-at": "2023-01-01T00:01:00Z",
                        "finished-at": "2023-01-01T00:05:00Z",
                        "organization-name": "test-org",
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

    def test_list_query_runs(self, client, mock_response):
        """Test listing query runs."""
        client._transport.request = MagicMock(return_value=mock_response)

        result = client.query_runs.list("test-org")

        assert isinstance(result, QueryRunList)
        assert len(result.items) == 1
        assert result.items[0].id == "qr-test123"
        assert result.items[0].query == "SELECT * FROM runs"
        assert result.current_page == 1
        assert result.total_count == 1

        client._transport.request.assert_called_once_with(
            "GET", "/api/v2/organizations/test-org/query-runs", params=None
        )

    def test_list_query_runs_with_options(self, client, mock_response):
        """Test listing query runs with options."""
        client._transport.request = MagicMock(return_value=mock_response)

        options = QueryRunListOptions(
            page_number=2,
            page_size=25,
            query_type=QueryRunType.FILTER,
            status=QueryRunStatus.COMPLETED,
        )
        result = client.query_runs.list("test-org", options)

        assert isinstance(result, QueryRunList)
        client._transport.request.assert_called_once_with(
            "GET",
            "/api/v2/organizations/test-org/query-runs",
            params={
                "page[number]": 2,
                "page[size]": 25,
                "filter[query-type]": "filter",
                "filter[status]": "completed",
            },
        )

    def test_create_query_run(self, client):
        """Test creating a query run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "qr-new123",
                "type": "query-runs",
                "attributes": {
                    "query": "SELECT * FROM workspaces",
                    "query-type": "search",
                    "status": "pending",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:00:00Z",
                    "organization-name": "test-org",
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        options = QueryRunCreateOptions(
            query="SELECT * FROM workspaces",
            query_type=QueryRunType.SEARCH,
            organization_name="test-org",
            timeout_seconds=300,
        )
        result = client.query_runs.create("test-org", options)

        assert isinstance(result, QueryRun)
        assert result.id == "qr-new123"
        assert result.query == "SELECT * FROM workspaces"
        assert result.status == QueryRunStatus.PENDING

        client._transport.request.assert_called_once_with(
            "POST",
            "/api/v2/organizations/test-org/query-runs",
            json_body={
                "data": {
                    "attributes": {
                        "query": "SELECT * FROM workspaces",
                        "query-type": "search",
                        "organization-name": "test-org",
                        "timeout-seconds": 300,
                    },
                    "type": "query-runs",
                }
            },
        )

    def test_read_query_run(self, client):
        """Test reading a query run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "qr-test123",
                "type": "query-runs",
                "attributes": {
                    "query": "SELECT * FROM runs",
                    "query-type": "filter",
                    "status": "completed",
                    "results-count": 42,
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:05:00Z",
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        result = client.query_runs.read("qr-test123")

        assert isinstance(result, QueryRun)
        assert result.id == "qr-test123"
        assert result.status == QueryRunStatus.COMPLETED
        assert result.results_count == 42

        client._transport.request.assert_called_once_with(
            "GET", "/api/v2/query-runs/qr-test123"
        )

    def test_read_query_run_with_options(self, client):
        """Test reading a query run with options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "qr-test123",
                "type": "query-runs",
                "attributes": {
                    "query": "SELECT * FROM runs",
                    "query-type": "filter",
                    "status": "completed",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:05:00Z",
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        options = QueryRunReadOptions(include_results=True, include_logs=True)
        result = client.query_runs.read_with_options("qr-test123", options)

        assert isinstance(result, QueryRun)
        assert result.id == "qr-test123"

        client._transport.request.assert_called_once_with(
            "GET",
            "/api/v2/query-runs/qr-test123",
            params={"include[results]": True, "include[logs]": True},
        )

    def test_query_run_logs(self, client):
        """Test retrieving query run logs."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = (
            "Starting query execution...\nQuery completed successfully."
        )
        client._transport.request = MagicMock(return_value=mock_response)

        result = client.query_runs.logs("qr-test123")

        assert isinstance(result, QueryRunLogs)
        assert result.query_run_id == "qr-test123"
        assert "Starting query execution" in result.logs
        assert result.log_level == "info"

        client._transport.request.assert_called_once_with(
            "GET", "/api/v2/query-runs/qr-test123/logs"
        )

    def test_query_run_results(self, client):
        """Test retrieving query run results."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "results": [
                    {"id": "run-1", "status": "completed"},
                    {"id": "run-2", "status": "pending"},
                ],
                "total_count": 2,
                "truncated": False,
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        result = client.query_runs.results("qr-test123")

        assert isinstance(result, QueryRunResults)
        assert result.query_run_id == "qr-test123"
        assert len(result.results) == 2
        assert result.total_count == 2
        assert not result.truncated

        client._transport.request.assert_called_once_with(
            "GET", "/api/v2/query-runs/qr-test123/results"
        )

    def test_cancel_query_run(self, client):
        """Test canceling a query run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "qr-test123",
                "type": "query-runs",
                "attributes": {
                    "query": "SELECT * FROM runs",
                    "query-type": "filter",
                    "status": "canceled",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:02:00Z",
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        options = QueryRunCancelOptions(reason="User requested cancellation")
        result = client.query_runs.cancel("qr-test123", options)

        assert isinstance(result, QueryRun)
        assert result.id == "qr-test123"
        assert result.status == QueryRunStatus.CANCELED

        client._transport.request.assert_called_once_with(
            "POST",
            "/api/v2/query-runs/qr-test123/actions/cancel",
            json_body={
                "data": {
                    "attributes": {"reason": "User requested cancellation"},
                    "type": "query-runs",
                }
            },
        )

    def test_force_cancel_query_run(self, client):
        """Test force canceling a query run."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "qr-test123",
                "type": "query-runs",
                "attributes": {
                    "query": "SELECT * FROM runs",
                    "query-type": "filter",
                    "status": "canceled",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:02:00Z",
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        options = QueryRunForceCancelOptions(reason="Force cancel due to timeout")
        result = client.query_runs.force_cancel("qr-test123", options)

        assert isinstance(result, QueryRun)
        assert result.id == "qr-test123"
        assert result.status == QueryRunStatus.CANCELED

        client._transport.request.assert_called_once_with(
            "POST",
            "/api/v2/query-runs/qr-test123/actions/force-cancel",
            json_body={
                "data": {
                    "attributes": {"reason": "Force cancel due to timeout"},
                    "type": "query-runs",
                }
            },
        )


class TestQueryRunErrorHandling:
    """Test query run error handling."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        config = TFEConfig(address="https://test.terraform.io", token="test-token")
        return TFEClient(config)

    def test_invalid_organization_error(self, client):
        """Test invalid organization error."""
        with pytest.raises(InvalidOrgError):
            client.query_runs.list("")

        with pytest.raises(InvalidOrgError):
            client.query_runs.list(None)

    def test_invalid_query_run_id_error(self, client):
        """Test invalid query run ID error."""
        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.read("")

        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.read(None)

        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.logs("")

        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.results("")

        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.cancel("")

        with pytest.raises(InvalidQueryRunIDError):
            client.query_runs.force_cancel("")

    def test_create_query_run_validation_errors(self, client):
        """Test create query run validation errors."""
        with pytest.raises(InvalidOrgError):
            options = QueryRunCreateOptions(
                query="SELECT * FROM runs", query_type=QueryRunType.FILTER
            )
            client.query_runs.create("", options)


class TestQueryRunIntegration:
    """Test query run integration scenarios."""

    @pytest.fixture
    def client(self):
        """Create a test client with mocked transport."""
        from unittest.mock import MagicMock, patch

        # Mock the HTTPTransport to prevent any network calls during initialization
        with patch("tfe.client.HTTPTransport") as mock_transport_class:
            mock_transport_instance = MagicMock()
            mock_transport_class.return_value = mock_transport_instance

            config = TFEConfig(address="https://test.terraform.io", token="test-token")
            client = TFEClient(config)
            return client

    def test_full_query_run_workflow(self, client):
        """Test a complete query run workflow simulation."""
        # Use the already mocked transport from the fixture
        mock_transport = client._transport

        # 1. Create query run
        create_response = Mock()
        create_response.json.return_value = {
            "data": {
                "id": "qr-workflow123",
                "type": "query-runs",
                "attributes": {
                    "query": "SELECT * FROM runs WHERE status = 'completed'",
                    "query-type": "filter",
                    "status": "pending",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:00:00Z",
                    "organization-name": "test-org",
                },
            }
        }

        # 2. Read query run (running state)
        read_response = Mock()
        read_response.json.return_value = {
            "data": {
                "id": "qr-workflow123",
                "type": "query-runs",
                "attributes": {
                    "query": "SELECT * FROM runs WHERE status = 'completed'",
                    "query-type": "filter",
                    "status": "running",
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:01:00Z",
                    "started-at": "2023-01-01T00:01:00Z",
                },
            }
        }

        # 3. Read query run (completed state)
        completed_response = Mock()
        completed_response.json.return_value = {
            "data": {
                "id": "qr-workflow123",
                "type": "query-runs",
                "attributes": {
                    "query": "SELECT * FROM runs WHERE status = 'completed'",
                    "query-type": "filter",
                    "status": "completed",
                    "results-count": 15,
                    "created-at": "2023-01-01T00:00:00Z",
                    "updated-at": "2023-01-01T00:05:00Z",
                    "started-at": "2023-01-01T00:01:00Z",
                    "finished-at": "2023-01-01T00:05:00Z",
                },
            }
        }

        # 4. Get results
        results_response = Mock()
        results_response.json.return_value = {
            "data": {
                "results": [
                    {"id": f"run-{i}", "status": "completed"} for i in range(15)
                ],
                "total_count": 15,
                "truncated": False,
            }
        }

        mock_transport.request.side_effect = [
            create_response,
            read_response,
            completed_response,
            results_response,
        ]

        # Execute workflow
        options = QueryRunCreateOptions(
            query="SELECT * FROM runs WHERE status = 'completed'",
            query_type=QueryRunType.FILTER,
            organization_name="test-org",
        )

        # 1. Create
        query_run = client.query_runs.create("test-org", options)
        assert query_run.status == QueryRunStatus.PENDING

        # 2. Check status (running)
        query_run = client.query_runs.read(query_run.id)
        assert query_run.status == QueryRunStatus.RUNNING

        # 3. Check status (completed)
        query_run = client.query_runs.read(query_run.id)
        assert query_run.status == QueryRunStatus.COMPLETED
        assert query_run.results_count == 15

        # 4. Get results
        results = client.query_runs.results(query_run.id)
        assert len(results.results) == 15
        assert not results.truncated

        # Verify all calls were made
        assert mock_transport.request.call_count == 4
