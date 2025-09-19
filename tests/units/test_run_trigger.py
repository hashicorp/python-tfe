"""Unit tests for the run trigger module."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from tfe._http import HTTPTransport
from tfe.errors import (
    InvalidRunTriggerIDError,
    InvalidRunTriggerTypeError,
    InvalidWorkspaceIDError,
    RequiredRunTriggerListOpsError,
    RequiredSourceableError,
    UnsupportedRunTriggerTypeError,
)
from tfe.models.run_trigger import (
    RunTrigger,
    RunTriggerCreateOptions,
    RunTriggerFilterOp,
    RunTriggerIncludeOp,
    RunTriggerListOptions,
    SourceableChoice,
)
from tfe.models.workspace import Workspace
from tfe.resources.run_trigger import RunTriggers, _run_trigger_from


class TestRunTriggerFrom:
    """Test the _run_trigger_from function."""

    def test_run_trigger_from_comprehensive(self):
        """Test _run_trigger_from with various data scenarios."""

        # Test data with all fields populated
        data = {
            "id": "rt-123",
            "attributes": {
                "created-at": "2023-01-01T12:00:00Z",
                "sourceable-name": "source-workspace",
                "workspace-name": "target-workspace",
            },
            "relationships": {
                "sourceable": {"data": {"id": "ws-source-123", "type": "workspaces"}},
                "workspace": {"data": {"id": "ws-target-456", "type": "workspaces"}},
            },
        }

        result = _run_trigger_from(data)

        assert result.id == "rt-123"
        assert result.sourceable_name == "source-workspace"
        assert result.workspace_name == "target-workspace"
        assert isinstance(result.created_at, datetime)
        assert result.sourceable is not None
        assert result.sourceable.name == "source-workspace"
        assert result.sourceable_choice is not None
        assert result.sourceable_choice.workspace.name == "source-workspace"
        assert result.workspace is not None
        assert result.workspace.name == "target-workspace"


class TestRunTriggers:
    """Test the RunTriggers service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def run_triggers_service(self, mock_transport):
        """Create a RunTriggers service with mocked transport."""
        return RunTriggers(mock_transport)

    def test_list_run_triggers_validations(self, run_triggers_service):
        """Test list method with invalid workspace ID."""

        # Test empty workspace ID
        with pytest.raises(InvalidWorkspaceIDError):
            list(
                run_triggers_service.list(
                    "",
                    RunTriggerListOptions(
                        run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_INBOUND
                    ),
                )
            )

        """Test list method with missing options."""
        with pytest.raises(RequiredRunTriggerListOpsError):
            list(run_triggers_service.list("ws-123", None))

        """Test list method with invalid filter type."""
        # Mock an invalid filter type by monkey-patching the validation
        with patch.object(
            run_triggers_service, "validate_run_trigger_filter_param"
        ) as mock_validate:
            mock_validate.side_effect = InvalidRunTriggerTypeError()

            with pytest.raises(InvalidRunTriggerTypeError):
                list(
                    run_triggers_service.list(
                        "ws-123",
                        RunTriggerListOptions(
                            run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_INBOUND
                        ),
                    )
                )

        """Test list method with include options on outbound trigger type."""
        options = RunTriggerListOptions(
            run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_OUTBOUND,
            include=[RunTriggerIncludeOp.RUN_TRIGGER_WORKSPACE],
        )

        with pytest.raises(UnsupportedRunTriggerTypeError):
            list(run_triggers_service.list("ws-123", options))

    def test_list_run_triggers_success(self, run_triggers_service):
        """Test successful list operation."""

        # Mock data structure that _list returns - each item should have the full structure
        # since the list method calls _run_trigger_from(item["attributes"])
        mock_data = [
            {
                "id": "rt-1",
                "attributes": {
                    "created-at": "2023-01-01T10:00:00Z",
                    "sourceable-name": "source-ws-1",
                    "workspace-name": "target-ws-1",
                },
            },
            {
                "id": "rt-2",
                "attributes": {
                    "created-at": "2023-01-02T11:00:00Z",
                    "sourceable-name": "source-ws-2",
                    "workspace-name": "target-ws-2",
                },
            },
        ]

        with patch.object(run_triggers_service, "_list") as mock_list:
            mock_list.return_value = iter(mock_data)

            options = RunTriggerListOptions(
                run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_INBOUND,
                page_number=2,
                page_size=10,
                include=[RunTriggerIncludeOp.RUN_TRIGGER_WORKSPACE],
            )

            result = list(run_triggers_service.list("ws-123", options))

            # Verify _list was called with correct parameters
            mock_list.assert_called_once_with(
                "/api/v2/workspaces/ws-123/run-triggers",
                params={
                    "page[size]": "10",
                    "page[number]": "2",
                    "filter[run-trigger][type]": "inbound",
                    "include": "workspace",
                },
            )

            # Verify results - test the actual _run_trigger_from behavior
            assert len(result) == 2
            assert result[0].sourceable_name == "source-ws-1"
            assert result[0].workspace_name == "target-ws-1"
            assert result[1].sourceable_name == "source-ws-2"
            assert result[1].workspace_name == "target-ws-2"

    def test_list_run_triggers_returns_iterator(self, run_triggers_service):
        """Test that list method returns an iterator."""

        with patch.object(run_triggers_service, "_list") as mock_list:
            mock_list.return_value = iter([])

            options = RunTriggerListOptions(
                run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_INBOUND
            )
            result = run_triggers_service.list("ws-123", options)

            # Verify it's an iterator
            assert hasattr(result, "__iter__")
            assert hasattr(result, "__next__")

    def test_create_run_trigger_validations(self, run_triggers_service):
        """Test create method with invalid workspace ID."""

        options = RunTriggerCreateOptions(
            sourceable=Workspace(id="ws-source", name="source", organization="org")
        )

        with pytest.raises(InvalidWorkspaceIDError):
            run_triggers_service.create("", options)

        """Test create method with missing sourceable."""
        # Since the model requires sourceable, we can just validate that RequiredSourceableError
        # is raised when the service method checks for None sourceable
        # Create valid options but then manually set sourceable to None to bypass model validation
        options = RunTriggerCreateOptions(
            sourceable=Workspace(id="ws-source", name="source", organization="org")
        )
        options.sourceable = None

        with pytest.raises(RequiredSourceableError):
            run_triggers_service.create("ws-123", options)

    def test_create_run_trigger_success(self, run_triggers_service):
        """Test successful create operation."""

        mock_response_data = {
            "id": "rt-new",
            "attributes": {
                "created-at": "2023-01-01T12:00:00Z",
                "sourceable-name": "source-workspace",
                "workspace-name": "target-workspace",
            },
        }

        mock_response = Mock()
        mock_response.json.return_value = {"data": mock_response_data}

        with patch.object(run_triggers_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            options = RunTriggerCreateOptions(
                sourceable=Workspace(id="ws-source", name="source", organization="org")
            )

            result = run_triggers_service.create("ws-123", options)

            # Verify request was made correctly
            mock_transport.request.assert_called_once()
            call_args = mock_transport.request.call_args

            assert call_args[0][0] == "POST"  # HTTP method
            assert call_args[0][1] == "/api/v2/workspaces/ws-123/run-triggers"  # URL

            # Verify request body structure
            json_body = call_args[1]["json_body"]
            assert "data" in json_body
            assert "relationships" in json_body["data"]
            assert "sourceable" in json_body["data"]["relationships"]
            assert (
                json_body["data"]["relationships"]["sourceable"]["data"]["id"]
                == "ws-source"
            )

            # Verify response
            assert result.id == "rt-new"
            assert result.sourceable_name == "source-workspace"
            assert result.workspace_name == "target-workspace"

    def test_read_run_trigger_invalid_id(self, run_triggers_service):
        """Test read method with invalid run trigger ID."""

        with pytest.raises(InvalidRunTriggerIDError):
            run_triggers_service.read("")

    def test_read_run_trigger_success(self, run_triggers_service):
        """Test successful read operation."""

        mock_response_data = {
            "id": "rt-read",
            "attributes": {
                "created-at": "2023-01-01T12:00:00Z",
                "sourceable-name": "source-workspace",
                "workspace-name": "target-workspace",
            },
        }

        mock_response = Mock()
        mock_response.json.return_value = {"data": mock_response_data}

        with patch.object(run_triggers_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            result = run_triggers_service.read("rt-123")

            # Verify request was made correctly
            mock_transport.request.assert_called_once_with(
                "GET", "/api/v2/run-triggers/rt-123"
            )

            # Verify response
            assert result.id == "rt-read"
            assert result.sourceable_name == "source-workspace"
            assert result.workspace_name == "target-workspace"

    def test_delete_run_trigger_success(self, run_triggers_service):
        """Test successful delete operation."""

        with patch.object(run_triggers_service, "t") as mock_transport:
            mock_transport.request.return_value = None  # DELETE returns no content

            result = run_triggers_service.delete("rt-123")

            # Verify request was made correctly
            mock_transport.request.assert_called_once_with(
                "DELETE", "/api/v2/run-triggers/rt-123"
            )

            # Verify return value
            assert result is None

    def test_validate_run_trigger_filter_param_validations(self, run_triggers_service):
        """Test validation with invalid filter parameter."""

        # This should be tested by mocking the enum validation
        with patch("tfe.resources.run_trigger.RunTriggerFilterOp") as mock_enum:
            mock_enum.__contains__ = Mock(return_value=False)

            with pytest.raises(InvalidRunTriggerTypeError):
                run_triggers_service.validate_run_trigger_filter_param("invalid", [])

        """Test validation with unsupported include options."""
        with pytest.raises(UnsupportedRunTriggerTypeError):
            run_triggers_service.validate_run_trigger_filter_param(
                RunTriggerFilterOp.RUN_TRIGGER_OUTBOUND,
                [RunTriggerIncludeOp.RUN_TRIGGER_WORKSPACE],
            )

    def test_validate_run_trigger_filter_param_success(self, run_triggers_service):
        """Test successful validation."""

        # Should not raise any exception
        run_triggers_service.validate_run_trigger_filter_param(
            RunTriggerFilterOp.RUN_TRIGGER_INBOUND,
            [RunTriggerIncludeOp.RUN_TRIGGER_WORKSPACE],
        )

        # Should not raise any exception for outbound with no includes
        run_triggers_service.validate_run_trigger_filter_param(
            RunTriggerFilterOp.RUN_TRIGGER_OUTBOUND, []
        )

    def test_backfill_deprecated_sourceable_already_exists(self, run_triggers_service):
        """Test backfill when sourceable already exists."""

        workspace = Workspace(id="ws-1", name="workspace", organization="org")
        rt = RunTrigger(
            id="rt-1",
            created_at=datetime.now(),
            sourceable_name="source",
            workspace_name="target",
            sourceable=workspace,  # Already exists
            sourceable_choice=SourceableChoice(workspace=workspace),
            workspace=workspace,
        )

        run_triggers_service.backfill_deprecated_sourceable(rt)

        # Should not change existing sourceable
        assert rt.sourceable == workspace

        # Manually set to None to test the backfill logic
        rt.sourceable = None

        run_triggers_service.backfill_deprecated_sourceable(rt)

        # Should backfill from sourceable_choice
        assert rt.sourceable == workspace
