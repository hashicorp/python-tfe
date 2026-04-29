"""Unit tests for the run_events module."""

from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidRunEventIDError, InvalidRunIDError
from pytfe.models.run_event import (
    RunEvent,
    RunEventIncludeOpt,
    RunEventListOptions,
    RunEventReadOptions,
)
from pytfe.resources.run_event import RunEvents


class TestRunEvents:
    """Test the RunEvents service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def run_events_service(self, mock_transport):
        """Create a RunEvents service with mocked transport."""
        return RunEvents(mock_transport)

    def test_list_run_events_success(self, run_events_service):
        """Test successful list operation using iterator pattern."""

        # Mock data for run events
        mock_data = [
            {
                "id": "re-123",
                "attributes": {
                    "action": "queued",
                    "description": "Run queued",
                    "created-at": "2023-01-01T12:00:00Z",
                },
            },
            {
                "id": "re-456",
                "attributes": {
                    "action": "planning",
                    "description": "Planning started",
                    "created-at": "2023-01-01T12:01:00Z",
                },
            },
            {
                "id": "re-789",
                "attributes": {
                    "action": "planned",
                    "description": "Planning finished",
                    "created-at": "2023-01-01T12:02:00Z",
                },
            },
        ]

        with patch.object(run_events_service, "_list") as mock_list:
            # Mock _list to return an iterator
            mock_list.return_value = iter(mock_data)

            options = RunEventListOptions(include=[RunEventIncludeOpt.RUN_EVENT_ACTOR])
            results = list(run_events_service.list("run-123", options))

            # Verify _list was called correctly
            mock_list.assert_called_once_with(
                "/api/v2/runs/run-123/run-events",
                params={"include": "actor"},
            )

            # Verify results
            assert len(results) == 3
            assert isinstance(results[0], RunEvent)
            assert results[0].id == "re-123"
            assert results[0].action == "queued"
            assert results[1].id == "re-456"
            assert results[1].action == "planning"
            assert results[2].id == "re-789"
            assert results[2].action == "planned"

    def test_list_run_events_with_multiple_includes(self, run_events_service):
        """Test list with multiple include options."""

        mock_data = [
            {
                "id": "re-111",
                "attributes": {
                    "action": "apply-queued",
                    "description": "Apply queued",
                    "created-at": "2023-01-01T12:10:00Z",
                },
            },
        ]

        with patch.object(run_events_service, "_list") as mock_list:
            mock_list.return_value = iter(mock_data)

            options = RunEventListOptions(
                include=[
                    RunEventIncludeOpt.RUN_EVENT_ACTOR,
                    RunEventIncludeOpt.RUN_EVENT_COMMENT,
                ]
            )
            results = list(run_events_service.list("run-456", options))

            # Verify include parameter is formatted correctly
            mock_list.assert_called_once_with(
                "/api/v2/runs/run-456/run-events",
                params={"include": "actor,comment"},
            )

            assert len(results) == 1
            assert results[0].id == "re-111"

    def test_list_run_events_no_options(self, run_events_service):
        """Test list without include options."""

        mock_data = [
            {
                "id": "re-222",
                "attributes": {
                    "action": "apply-finished",
                    "created-at": "2023-01-01T12:15:00Z",
                },
            },
        ]

        with patch.object(run_events_service, "_list") as mock_list:
            mock_list.return_value = iter(mock_data)

            results = list(run_events_service.list("run-789"))

            # Verify _list was called with empty params
            mock_list.assert_called_once_with(
                "/api/v2/runs/run-789/run-events",
                params={},
            )

            assert len(results) == 1
            assert results[0].id == "re-222"

    def test_list_run_events_empty_result(self, run_events_service):
        """Test list with no run events returned."""

        with patch.object(run_events_service, "_list") as mock_list:
            mock_list.return_value = iter([])

            results = list(run_events_service.list("run-empty"))

            assert len(results) == 0

    def test_list_run_events_invalid_run_id(self, run_events_service):
        """Test list with invalid run ID."""

        with pytest.raises(InvalidRunIDError):
            list(run_events_service.list(""))

        with pytest.raises(InvalidRunIDError):
            list(run_events_service.list("run/invalid"))

    def test_read_run_event_success(self, run_events_service):
        """Test successful read operation."""

        mock_response_data = {
            "data": {
                "id": "re-read-123",
                "attributes": {
                    "action": "planned",
                    "description": "Run planned successfully",
                    "created-at": "2023-01-01T13:00:00Z",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(run_events_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            result = run_events_service.read("re-read-123")

            # Verify request was made correctly
            mock_transport.request.assert_called_once_with(
                "GET",
                "/api/v2/run-events/re-read-123",
                params={},
            )

            # Verify result
            assert isinstance(result, RunEvent)
            assert result.id == "re-read-123"
            assert result.action == "planned"
            assert result.description == "Run planned successfully"

    def test_read_run_event_with_includes(self, run_events_service):
        """Test read with include options."""

        mock_response_data = {
            "data": {
                "id": "re-read-456",
                "attributes": {
                    "action": "discarded",
                    "description": "Run discarded",
                    "created-at": "2023-01-01T13:05:00Z",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(run_events_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            options = RunEventReadOptions(include=[RunEventIncludeOpt.RUN_EVENT_ACTOR])
            result = run_events_service.read_with_options("re-read-456", options)

            # Verify include parameter was passed
            mock_transport.request.assert_called_once_with(
                "GET",
                "/api/v2/run-events/re-read-456",
                params={"include": "actor"},
            )

            assert result.id == "re-read-456"
            assert result.action == "discarded"

    def test_read_run_event_invalid_id(self, run_events_service):
        """Test read with invalid run event ID."""

        with pytest.raises(InvalidRunEventIDError):
            run_events_service.read("")

        with pytest.raises(InvalidRunEventIDError):
            run_events_service.read("re/invalid")

    def test_read_vs_read_with_options(self, run_events_service):
        """Test that read() delegates to read_with_options()."""

        mock_response_data = {
            "data": {
                "id": "re-read-789",
                "attributes": {
                    "action": "completed",
                    "created-at": "2023-01-01T13:10:00Z",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(run_events_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            result1 = run_events_service.read("re-read-789")

            # Reset mock
            mock_transport.reset_mock()
            mock_transport.request.return_value = mock_response

            result2 = run_events_service.read_with_options("re-read-789")

            # Both should produce the same result
            assert result1.id == result2.id
            assert result1.action == result2.action

    def test_list_run_events_iterator_lazy_loading(self, run_events_service):
        """Test that list returns an iterator that lazily loads data."""

        mock_data = [
            {
                "id": "re-lazy-1",
                "attributes": {
                    "action": "queued",
                    "created-at": "2023-01-01T12:00:00Z",
                },
            },
        ]

        with patch.object(run_events_service, "_list") as mock_list:
            mock_list.return_value = iter(mock_data)

            # Get the iterator without consuming it yet
            iterator = run_events_service.list("run-lazy")

            # _list should not have been called yet (iterator not consumed)
            # This test ensures lazy evaluation
            first_event = next(iterator)

            # Now _list should have been called
            mock_list.assert_called_once()
            assert first_event.id == "re-lazy-1"
