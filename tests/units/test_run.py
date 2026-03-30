"""Unit tests for the run module."""

from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidRunIDError,
    RequiredWorkspaceError,
    TerraformVersionValidForPlanOnlyError,
)
from pytfe.models.run import (
    Run,
    RunApplyOptions,
    RunCancelOptions,
    RunCreateOptions,
    RunDiscardOptions,
    RunForceCancelOptions,
    RunIncludeOpt,
    RunListForOrganizationOptions,
    RunListOptions,
    RunReadOptions,
    RunSource,
    RunStatus,
    RunVariable,
)
from pytfe.models.workspace import Workspace
from pytfe.resources.run import Runs


class TestRuns:
    """Test the Runs service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def runs_service(self, mock_transport):
        """Create a Runs service with mocked transport."""
        return Runs(mock_transport)

    def test_list_runs_success(self, runs_service):
        """Test successful list operation."""

        mock_list_data = [
            {
                "id": "run-123",
                "attributes": {
                    "status": "applied",
                    "source": "tfe-configuration-version",
                    "message": "Test run",
                    "created-at": "2023-01-01T12:00:00Z",
                    "has-changes": True,
                    "is-destroy": False,
                    "auto-apply": False,
                    "plan-only": False,
                },
            },
            {
                "id": "run-456",
                "attributes": {
                    "status": "planned",
                    "source": "tfe-ui",
                    "message": "Another test run",
                    "created-at": "2023-01-02T14:00:00Z",
                    "has-changes": False,
                    "is-destroy": True,
                    "auto-apply": True,
                    "plan-only": True,
                },
            },
        ]

        with patch.object(runs_service, "_list") as mock_list:
            mock_list.return_value = mock_list_data

            # Test with options
            options = RunListOptions(page_number=1, page_size=5)
            result = list(runs_service.list("ws-123", options))

            # Verify _list was called with correct path
            assert mock_list.call_count == 1
            call_args = mock_list.call_args
            assert call_args[0][0] == "/api/v2/workspaces/ws-123/runs"

            # Verify params structure includes pagination and options
            params = call_args[1]["params"]
            assert "page[number]" in params
            assert "page[size]" in params
            assert "include" in params

            # Verify result structure - iterator yields Run objects
            assert len(result) == 2

            # Verify run objects were created correctly from response data
            run1 = result[0]
            assert isinstance(run1, Run)
            assert run1.id == "run-123"
            assert run1.status == RunStatus.Run_Applied
            assert run1.source == RunSource.Run_Source_Configuration_Version
            assert run1.message == "Test run"
            assert run1.has_changes is True
            assert run1.is_destroy is False

            run2 = result[1]
            assert isinstance(run2, Run)
            assert run2.id == "run-456"
            assert run2.status == RunStatus.Run_Planned
            assert run2.source == RunSource.Run_Source_UI
            assert run2.message == "Another test run"
            assert run2.has_changes is False
            assert run2.is_destroy is True

    def test_list_for_organization_success(self, runs_service):
        """Test successful list_for_organization operation."""

        mock_response_data = [
            {
                "id": "run-org-1",
                "attributes": {
                    "status": "applied",
                    "source": "tfe-api",
                    "message": "Organization run",
                    "created-at": "2023-01-01T12:00:00Z",
                    "has-changes": True,
                    "is-destroy": False,
                },
            }
        ]

        with patch.object(runs_service, "_list") as mock_list:
            mock_list.return_value = mock_response_data

            options = RunListForOrganizationOptions(status="applied,planned")
            result = list(runs_service.list_for_organization("test-org", options))

            # Verify _list was called with correct path and params
            expected_params = {
                "page[number]": 1,
                "page[size]": 20,
                "filter[status]": "applied,planned",
                "include": [],
            }
            mock_list.assert_called_once_with(
                "/api/v2/organizations/test-org/runs", params=expected_params
            )

            # Verify result structure - now returns list of Run objects
            assert len(result) == 1
            assert result[0].id == "run-org-1"
            assert result[0].status == RunStatus.Run_Applied

    def test_create_run_validation_errors(self, runs_service):
        """Test create method with validation errors."""

        # Test missing workspace
        options = RunCreateOptions()
        with pytest.raises(RequiredWorkspaceError):
            runs_service.create(options)

        # Test terraform_version with non-plan-only run
        workspace = Workspace(id="ws-123", name="test", organization=None)
        options = RunCreateOptions(
            workspace=workspace, terraform_version="1.5.0", plan_only=False
        )
        with pytest.raises(TerraformVersionValidForPlanOnlyError):
            runs_service.create(options)

        # Test terraform_version with plan_only=None (defaults to False)
        options = RunCreateOptions(workspace=workspace, terraform_version="1.5.0")
        with pytest.raises(TerraformVersionValidForPlanOnlyError):
            runs_service.create(options)

    def test_create_run_success(self, runs_service):
        """Test successful create operation."""

        mock_response_data = {
            "data": {
                "id": "run-new-123",
                "attributes": {
                    "status": "pending",
                    "source": "tfe-api",
                    "message": "Created via API",
                    "created-at": "2023-01-01T12:00:00Z",
                    "has-changes": False,
                    "is-destroy": False,
                    "auto-apply": False,
                    "plan-only": True,
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(runs_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            workspace = Workspace(id="ws-123", name="test", organization=None)
            variables = [
                RunVariable(key="env", value="test"),
                RunVariable(key="region", value="us-east-1"),
            ]
            options = RunCreateOptions(
                workspace=workspace,
                message="Test run creation",
                plan_only=True,
                variables=variables,
            )

            result = runs_service.create(options)

            # Verify request was made correctly
            mock_transport.request.assert_called_once()
            call_args = mock_transport.request.call_args

            assert call_args[0][0] == "POST"  # HTTP method
            assert call_args[0][1] == "/api/v2/runs"  # URL

            # Verify request body structure
            json_body = call_args[1]["json_body"]
            assert "data" in json_body
            assert json_body["data"]["type"] == "runs"
            assert "attributes" in json_body["data"]
            assert json_body["data"]["attributes"]["message"] == "Test run creation"
            assert json_body["data"]["attributes"]["plan-only"] is True

            # Verify relationships
            assert "relationships" in json_body["data"]
            assert "workspace" in json_body["data"]["relationships"]
            workspace_data = json_body["data"]["relationships"]["workspace"]["data"]
            assert workspace_data["id"] == "ws-123"
            assert workspace_data["type"] == "workspaces"

            # Verify result
            assert isinstance(result, Run)
            assert result.id == "run-new-123"
            assert result.status == RunStatus.Run_Pending
            assert result.plan_only is True

    def test_read_run_validation_errors(self, runs_service):
        """Test read method with invalid run ID."""

        # Test empty run ID
        with pytest.raises(InvalidRunIDError):
            runs_service.read("")

        # Test None run ID
        with pytest.raises(InvalidRunIDError):
            runs_service.read(None)

    def test_read_run_success(self, runs_service):
        """Test successful read operation."""

        mock_response_data = {
            "data": {
                "id": "run-read-123",
                "attributes": {
                    "status": "applied",
                    "source": "tfe-configuration-version",
                    "message": "Read test run",
                    "created-at": "2023-01-01T12:00:00Z",
                    "has-changes": True,
                    "is-destroy": False,
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(runs_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            result = runs_service.read("run-read-123")

            # Verify request was made correctly (read calls read_with_options with empty params)
            mock_transport.request.assert_called_once_with(
                "GET", "/api/v2/runs/run-read-123", params={}
            )

            # Verify result
            assert isinstance(result, Run)
            assert result.id == "run-read-123"
            assert result.status == RunStatus.Run_Applied
            assert result.message == "Read test run"

    def test_read_with_options_success(self, runs_service):
        """Test successful read_with_options operation."""

        mock_response_data = {
            "data": {
                "id": "run-detailed-123",
                "attributes": {
                    "status": "planned",
                    "source": "tfe-api",
                    "message": "Detailed read test",
                    "created-at": "2023-01-01T12:00:00Z",
                    "has-changes": True,
                    "is-destroy": False,
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(runs_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            options = RunReadOptions(
                include=[
                    RunIncludeOpt.RUN_PLAN,
                    RunIncludeOpt.RUN_APPLY,
                    RunIncludeOpt.RUN_CREATED_BY,
                ]
            )
            result = runs_service.read_with_options("run-detailed-123", options)

            # Verify request was made correctly
            mock_transport.request.assert_called_once_with(
                "GET",
                "/api/v2/runs/run-detailed-123",
                params={"include": "plan,apply,created-by"},
            )

            # Verify result
            assert isinstance(result, Run)
            assert result.id == "run-detailed-123"

    def test_apply_run_success(self, runs_service):
        """Test successful apply operation."""

        with patch.object(runs_service, "t") as mock_transport:
            mock_transport.request.return_value = Mock()

            options = RunApplyOptions(comment="Applying via API")
            runs_service.apply("run-apply-123", options)

            # Verify request was made correctly
            mock_transport.request.assert_called_once()
            call_args = mock_transport.request.call_args

            assert call_args[0][0] == "POST"  # HTTP method
            assert call_args[0][1] == "/api/v2/runs/run-apply-123/actions/apply"  # URL

            # Verify request body
            json_body = call_args[1]["json_body"]
            assert json_body["comment"] == "Applying via API"

    def test_cancel_run_success(self, runs_service):
        """Test successful cancel operation."""

        with patch.object(runs_service, "t") as mock_transport:
            mock_transport.request.return_value = Mock()

            options = RunCancelOptions(comment="Canceling run")
            runs_service.cancel("run-cancel-123", options)

            # Verify request was made correctly
            mock_transport.request.assert_called_once()
            call_args = mock_transport.request.call_args

            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/api/v2/runs/run-cancel-123/actions/cancel"
            assert call_args[1]["json_body"]["comment"] == "Canceling run"

    def test_force_cancel_run_success(self, runs_service):
        """Test successful force_cancel operation."""

        with patch.object(runs_service, "t") as mock_transport:
            mock_transport.request.return_value = Mock()

            options = RunForceCancelOptions(comment="Force canceling run")
            runs_service.force_cancel("run-force-cancel-123", options)

            # Verify request was made correctly
            call_args = mock_transport.request.call_args
            assert (
                call_args[0][1]
                == "/api/v2/runs/run-force-cancel-123/actions/force-cancel"
            )
            assert call_args[1]["json_body"]["comment"] == "Force canceling run"

    def test_force_execute_run_success(self, runs_service):
        """Test successful force_execute operation."""

        with patch.object(runs_service, "t") as mock_transport:
            mock_transport.request.return_value = Mock()

            runs_service.force_execute("run-force-execute-123")

            # Verify request was made correctly - force_execute doesn't pass json_body
            call_args = mock_transport.request.call_args
            assert call_args[0][0] == "POST"
            assert (
                call_args[0][1]
                == "/api/v2/runs/run-force-execute-123/actions/force-execute"
            )
            # force_execute doesn't pass json_body parameter at all
            assert "json_body" not in call_args[1]

    def test_discard_run_success(self, runs_service):
        """Test successful discard operation."""

        with patch.object(runs_service, "t") as mock_transport:
            mock_transport.request.return_value = Mock()

            options = RunDiscardOptions(comment="Discarding run")
            runs_service.discard("run-discard-123", options)

            # Verify request was made correctly
            call_args = mock_transport.request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/api/v2/runs/run-discard-123/actions/discard"
            assert call_args[1]["json_body"]["comment"] == "Discarding run"

    def test_run_source_enum_values(self):
        """Test that all RunSource enum values work with Run model validation."""

        # Test all RunSource enum values
        test_sources = [
            ("tfe-api", RunSource.Run_Source_API),
            ("tfe-configuration-version", RunSource.Run_Source_Configuration_Version),
            ("tfe-ui", RunSource.Run_Source_UI),
            ("terraform+cloud", RunSource.Run_Source_Terraform_Cloud),
            ("terraform", RunSource.Run_Source_Terraform),
            ("tfe-run-trigger", RunSource.Run_Source_Run_Trigger),
            ("tfe-infrastructure-lifecycle", RunSource.Run_Source_Infra_Lifecycle),
        ]

        for source_value, expected_enum in test_sources:
            # Test that Run model can be created with this source
            # Use the same format as the service methods (attributes flattened with id)
            run_data = {
                "id": f"run-test-{source_value.replace('+', '').replace('-', '_')}",
                "status": "pending",
                "source": source_value,
                "message": f"Test run with source {source_value}",
                "created-at": "2023-01-01T12:00:00Z",
                "has-changes": False,
                "is-destroy": False,
            }

            # This should not raise an exception
            run = Run.model_validate(run_data)

            # Verify the source was correctly parsed
            assert run.source == expected_enum
            assert run.source.value == source_value
