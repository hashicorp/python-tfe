"""
Comprehensive unit tests for query run operations in the Python TFE SDK.

This test suite covers all query run methods including:
1. list() - List query runs for a workspace with pagination
2. create() - Create new query runs
3. read() - Read query run details
4. read_with_options() - Read with include options
5. logs() - Retrieve query run logs
6. cancel() - Cancel a query run
7. force_cancel() - Force cancel a query run

Usage:
    pytest tests/units/test_query_run.py -v
"""

from unittest.mock import Mock, patch

import pytest

from pytfe.errors import InvalidQueryRunIDError, InvalidWorkspaceIDError
from pytfe.models import (
    QueryRun,
    QueryRunCreateOptions,
    QueryRunIncludeOpt,
    QueryRunListOptions,
    QueryRunReadOptions,
    QueryRunSource,
    QueryRunStatus,
    QueryRunStatusTimestamps,
    QueryRunVariable,
)
from pytfe.resources.query_run import QueryRuns

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_transport():
    """Create a mock HTTPTransport."""
    return Mock()


@pytest.fixture
def query_runs_service(mock_transport):
    """Create a QueryRuns service with mocked transport."""
    return QueryRuns(mock_transport)


@pytest.fixture
def sample_query_run_data():
    """Sample query run data from API."""
    return {
        "id": "qr-123abc456def",
        "type": "queries",
        "attributes": {
            "source": "tfe-api",
            "status": "finished",
            "created-at": "2024-01-15T10:00:00Z",
            "updated-at": "2024-01-15T10:05:00Z",
            "canceled-at": None,
            "log-read-url": "https://app.terraform.io/api/v2/queries/qr-123abc456def/logs",
            "status-timestamps": {
                "queued-at": "2024-01-15T10:00:00Z",
                "running-at": "2024-01-15T10:01:00Z",
                "finished-at": "2024-01-15T10:05:00Z",
            },
            "variables": [
                {"key": "environment", "value": "production"},
                {"key": "region", "value": "us-east-1"},
            ],
            "actions": {
                "is-cancelable": True,
                "is-force-cancelable": False,
            },
        },
        "relationships": {
            "workspace": {"data": {"id": "ws-abc123", "type": "workspaces"}},
            "configuration-version": {
                "data": {"id": "cv-def456", "type": "configuration-versions"}
            },
            "created-by": {"data": {"id": "user-123", "type": "users"}},
        },
    }


@pytest.fixture
def sample_query_run_list_response(sample_query_run_data):
    """Sample query run list response."""
    return {
        "data": [
            sample_query_run_data,
            {
                "id": "qr-789ghi012jkl",
                "type": "queries",
                "attributes": {
                    "source": "tfe-api",
                    "status": "running",
                    "created-at": "2024-01-15T11:00:00Z",
                    "updated-at": "2024-01-15T11:02:00Z",
                    "canceled-at": None,
                    "log-read-url": None,
                    "status-timestamps": {
                        "queued-at": "2024-01-15T11:00:00Z",
                        "running-at": "2024-01-15T11:01:00Z",
                    },
                    "variables": [],
                    "actions": {
                        "is-cancelable": True,
                        "is-force-cancelable": False,
                    },
                },
            },
        ],
        "meta": {
            "pagination": {
                "current-page": 1,
                "page-size": 20,
                "total-pages": 1,
                "total-count": 2,
            }
        },
        "links": {"next": None},
    }


# ============================================================================
# List Operations Tests
# ============================================================================


class TestQueryRunsList:
    """Test suite for query run list operations."""

    def test_list_basic(
        self, query_runs_service, mock_transport, sample_query_run_list_response
    ):
        """Test basic query run listing."""
        mock_response = Mock()
        mock_response.json.return_value = sample_query_run_list_response
        mock_transport.request.return_value = mock_response

        workspace_id = "ws-abc123"
        query_runs = list(query_runs_service.list(workspace_id))

        # Verify the request
        mock_transport.request.assert_called_with(
            "GET",
            f"/api/v2/workspaces/{workspace_id}/queries",
            params={"page[number]": 1, "page[size]": 100},
        )

        # Verify the results
        assert len(query_runs) == 2

        # Check first query run
        qr1 = query_runs[0]
        assert qr1.id == "qr-123abc456def"
        assert qr1.status == QueryRunStatus.FINISHED
        assert qr1.source == QueryRunSource.API
        assert qr1.log_read_url is not None
        assert len(qr1.variables) == 2
        assert qr1.variables[0].key == "environment"
        assert qr1.variables[0].value == "production"

        # Check second query run
        qr2 = query_runs[1]
        assert qr2.id == "qr-789ghi012jkl"
        assert qr2.status == QueryRunStatus.RUNNING
        assert qr2.log_read_url is None
        assert len(qr2.variables) == 0

    def test_list_with_options(
        self, query_runs_service, mock_transport, sample_query_run_list_response
    ):
        """Test list with options."""
        mock_response = Mock()
        mock_response.json.return_value = sample_query_run_list_response
        mock_transport.request.return_value = mock_response

        workspace_id = "ws-abc123"
        options = QueryRunListOptions(
            page_number=1,
            page_size=10,
            include=[
                QueryRunIncludeOpt.CREATED_BY,
                QueryRunIncludeOpt.CONFIGURATION_VERSION,
            ],
        )

        query_runs = list(query_runs_service.list(workspace_id, options))

        # Verify the request includes options
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == f"/api/v2/workspaces/{workspace_id}/queries"
        params = call_args[1]["params"]
        assert params["page[number]"] == 1
        assert params["page[size]"] == 10
        assert params["include"] == "created_by,configuration_version"

        assert len(query_runs) == 2

    def test_list_invalid_workspace_id(self, query_runs_service):
        """Test list with invalid workspace ID."""
        with pytest.raises(InvalidWorkspaceIDError):
            list(query_runs_service.list(""))

        with pytest.raises(InvalidWorkspaceIDError):
            list(query_runs_service.list(None))


# ============================================================================
# Create Operations Tests
# ============================================================================


class TestQueryRunsCreate:
    """Test suite for query run create operations."""

    def test_create_basic(
        self, query_runs_service, mock_transport, sample_query_run_data
    ):
        """Test basic query run creation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_query_run_data}
        mock_transport.request.return_value = mock_response

        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id="ws-abc123",
            configuration_version_id="cv-def456",
        )

        result = query_runs_service.create(options)

        # Verify the request
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v2/queries"

        json_body = call_args[1]["json_body"]
        assert json_body["data"]["type"] == "queries"
        assert json_body["data"]["attributes"]["source"] == "tfe-api"
        assert (
            json_body["data"]["relationships"]["workspace"]["data"]["id"] == "ws-abc123"
        )
        assert (
            json_body["data"]["relationships"]["configuration-version"]["data"]["id"]
            == "cv-def456"
        )

        # Verify the result
        assert isinstance(result, QueryRun)
        assert result.id == "qr-123abc456def"
        assert result.status == QueryRunStatus.FINISHED
        assert result.source == QueryRunSource.API

    def test_create_with_variables(
        self, query_runs_service, mock_transport, sample_query_run_data
    ):
        """Test query run creation with variables."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_query_run_data}
        mock_transport.request.return_value = mock_response

        variables = [
            QueryRunVariable(key="environment", value="production"),
            QueryRunVariable(key="region", value="us-east-1"),
        ]

        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id="ws-abc123",
            configuration_version_id="cv-def456",
            variables=variables,
        )

        result = query_runs_service.create(options)

        # Verify variables in request
        call_args = mock_transport.request.call_args
        json_body = call_args[1]["json_body"]
        assert "variables" in json_body["data"]["attributes"]
        assert len(json_body["data"]["attributes"]["variables"]) == 2

        # Verify result
        assert result.id == "qr-123abc456def"
        assert len(result.variables) == 2


# ============================================================================
# Read Operations Tests
# ============================================================================


class TestQueryRunsRead:
    """Test suite for query run read operations."""

    def test_read_success(
        self, query_runs_service, mock_transport, sample_query_run_data
    ):
        """Test successful query run read."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_query_run_data}
        mock_transport.request.return_value = mock_response

        result = query_runs_service.read("qr-123abc456def")

        # Verify the request
        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/queries/qr-123abc456def"
        )

        # Verify the result
        assert isinstance(result, QueryRun)
        assert result.id == "qr-123abc456def"
        assert result.status == QueryRunStatus.FINISHED
        assert result.source == QueryRunSource.API
        assert result.log_read_url is not None

    def test_read_invalid_id(self, query_runs_service):
        """Test read with invalid query run ID."""
        with pytest.raises(InvalidQueryRunIDError):
            query_runs_service.read("")

        with pytest.raises(InvalidQueryRunIDError):
            query_runs_service.read(None)

    def test_read_with_options_success(
        self, query_runs_service, mock_transport, sample_query_run_data
    ):
        """Test read with options."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_query_run_data}
        mock_transport.request.return_value = mock_response

        options = QueryRunReadOptions(
            include=[
                QueryRunIncludeOpt.CREATED_BY,
                QueryRunIncludeOpt.CONFIGURATION_VERSION,
            ]
        )

        result = query_runs_service.read_with_options("qr-123abc456def", options)

        # Verify the request includes options
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/api/v2/queries/qr-123abc456def"
        params = call_args[1]["params"]
        assert params["include"] == "created_by,configuration_version"

        # Verify the result
        assert result.id == "qr-123abc456def"


# ============================================================================
# Logs Operations Tests
# ============================================================================


class TestQueryRunsLogs:
    """Test suite for query run logs operations."""

    def test_logs_success(self, query_runs_service, mock_transport):
        """Test successful logs retrieval."""
        # Mock the read method to return a query run with log URL
        mock_query_run = Mock()
        mock_query_run.log_read_url = (
            "https://app.terraform.io/api/v2/queries/qr-123/logs"
        )

        # Mock the logs content
        mock_logs_response = Mock()
        mock_logs_response.content = b"Query run logs content\nLine 2\nLine 3"

        with patch.object(query_runs_service, "read", return_value=mock_query_run):
            mock_transport.request.return_value = mock_logs_response

            result = query_runs_service.logs("qr-123abc456def")

            # Verify read was called
            query_runs_service.read.assert_called_once_with("qr-123abc456def")

            # Verify logs request was made
            mock_transport.request.assert_called_once_with(
                "GET", "https://app.terraform.io/api/v2/queries/qr-123/logs"
            )

            # Verify the result is an IO stream
            assert result.read() == b"Query run logs content\nLine 2\nLine 3"

    def test_logs_no_url_error(self, query_runs_service):
        """Test logs method when query run has no log URL."""
        mock_query_run = Mock()
        mock_query_run.log_read_url = None

        with patch.object(query_runs_service, "read", return_value=mock_query_run):
            with pytest.raises(ValueError) as exc:
                query_runs_service.logs("qr-123abc456def")

            assert "does not have a log URL" in str(exc.value)

    def test_logs_invalid_id(self, query_runs_service):
        """Test logs with invalid query run ID."""
        with pytest.raises(InvalidQueryRunIDError):
            query_runs_service.logs("")


# ============================================================================
# Cancel Operations Tests
# ============================================================================


class TestQueryRunsCancel:
    """Test suite for query run cancel operations."""

    def test_cancel_success(self, query_runs_service, mock_transport):
        """Test successful query run cancellation."""
        mock_response = Mock()
        mock_transport.request.return_value = mock_response

        query_runs_service.cancel("qr-123abc456def")

        # Verify the request
        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/queries/qr-123abc456def/actions/cancel",
        )

    def test_cancel_invalid_id(self, query_runs_service):
        """Test cancel with invalid query run ID."""
        with pytest.raises(InvalidQueryRunIDError):
            query_runs_service.cancel("")


# ============================================================================
# Force Cancel Operations Tests
# ============================================================================


class TestQueryRunsForceCancel:
    """Test suite for query run force cancel operations."""

    def test_force_cancel_success(self, query_runs_service, mock_transport):
        """Test successful force cancellation."""
        mock_response = Mock()
        mock_transport.request.return_value = mock_response

        query_runs_service.force_cancel("qr-123abc456def")

        # Verify the request
        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/queries/qr-123abc456def/actions/force-cancel",
        )

    def test_force_cancel_invalid_id(self, query_runs_service):
        """Test force cancel with invalid query run ID."""
        with pytest.raises(InvalidQueryRunIDError):
            query_runs_service.force_cancel("")


# ============================================================================
# Unit Tests - Model Validation
# ============================================================================


class TestQueryRunCreateOptions:
    """Unit tests for QueryRunCreateOptions model."""

    def test_create_with_required_fields(self):
        """Test creating options with required fields only."""
        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id="ws-123",
        )

        assert options.source == QueryRunSource.API
        assert options.workspace_id == "ws-123"
        assert options.configuration_version_id is None
        assert options.variables is None

    def test_create_with_all_fields(self):
        """Test creating options with all fields."""
        variables = [
            QueryRunVariable(key="var1", value="value1"),
            QueryRunVariable(key="var2", value="value2"),
        ]

        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id="ws-123",
            configuration_version_id="cv-456",
            variables=variables,
        )

        assert options.source == QueryRunSource.API
        assert options.workspace_id == "ws-123"
        assert options.configuration_version_id == "cv-456"
        assert len(options.variables) == 2
        assert options.variables[0].key == "var1"


class TestQueryRunModel:
    """Unit tests for QueryRun model."""

    def test_status_enum_values(self):
        """Test all status enum values."""
        assert QueryRunStatus.PENDING.value == "pending"
        assert QueryRunStatus.QUEUED.value == "queued"
        assert QueryRunStatus.RUNNING.value == "running"
        assert QueryRunStatus.FINISHED.value == "finished"
        assert QueryRunStatus.ERRORED.value == "errored"
        assert QueryRunStatus.CANCELED.value == "canceled"

    def test_source_enum_value(self):
        """Test source enum value."""
        assert QueryRunSource.API.value == "tfe-api"


# ============================================================================
# Test Utilities
# ============================================================================


def test_query_run_variable():
    """Test QueryRunVariable model."""
    var = QueryRunVariable(key="test_key", value="test_value")

    assert var.key == "test_key"
    assert var.value == "test_value"


def test_query_run_status_timestamps():
    """Test QueryRunStatusTimestamps model."""
    timestamps = QueryRunStatusTimestamps(
        queued_at="2024-01-15T10:00:00Z",
        running_at="2024-01-15T10:05:00Z",
        errored_at="2024-01-15T10:10:00Z",
    )

    # Timestamps are datetime objects
    assert timestamps.queued_at is not None
    assert timestamps.running_at is not None
    assert timestamps.errored_at is not None
    assert timestamps.finished_at is None
    assert timestamps.canceled_at is None
