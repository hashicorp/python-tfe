"""Unit tests for the workspace run task module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidRunTaskIDError,
    InvalidWorkspaceIDError,
    InvalidWorkspaceRunTaskIDError,
)
from pytfe.models.run_task import RunTask, Stage, TaskEnforcementLevel
from pytfe.models.workspace_run_task import (
    WorkspaceRunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskUpdateOptions,
)
from pytfe.resources.workspace_run_task import (
    WorkspaceRunTasks,
    _workspace_run_task_from,
)

# Ensure models are fully defined for tests
WorkspaceRunTask.model_rebuild()
WorkspaceRunTaskCreateOptions.model_rebuild()
WorkspaceRunTaskUpdateOptions.model_rebuild()


class TestWorkspaceRunTaskFrom:
    """Test the _workspace_run_task_from function."""

    def test_workspace_run_task_from_complete(self):
        """Test _workspace_run_task_from with all fields populated."""

        data = {
            "id": "wstask-123",
            "attributes": {
                "enforcement-level": "mandatory",
                "stage": "pre_plan",
                "stages": ["pre_plan", "post_plan"],
            },
            "relationships": {
                "task": {"data": {"id": "task-456", "type": "tasks"}},
                "workspace": {"data": {"id": "ws-789", "type": "workspaces"}},
            },
        }

        result = _workspace_run_task_from(data)

        assert result.id == "wstask-123"
        assert result.enforcement_level == TaskEnforcementLevel.MANDATORY
        assert result.stage == Stage.PRE_PLAN
        assert len(result.stages) == 2
        assert result.stages[0] == Stage.PRE_PLAN
        assert result.stages[1] == Stage.POST_PLAN
        assert result.run_task is not None
        assert result.run_task.id == "task-456"
        assert result.workspace is not None
        assert result.workspace.id == "ws-789"

    def test_workspace_run_task_from_minimal(self):
        """Test _workspace_run_task_from with minimal fields."""

        data = {
            "id": "wstask-minimal",
            "attributes": {"enforcement-level": "advisory"},
        }

        result = _workspace_run_task_from(data)

        assert result.id == "wstask-minimal"
        assert result.enforcement_level == TaskEnforcementLevel.ADVISORY
        # Should have default stage
        assert result.stage == Stage.PRE_PLAN
        # Should have empty stages list
        assert result.stages == []
        # Relationships should be None
        assert result.run_task is None
        assert result.workspace is None

    def test_workspace_run_task_from_invalid_enforcement_level(self):
        """Test _workspace_run_task_from handles invalid enforcement level."""

        data = {
            "id": "wstask-invalid",
            "attributes": {"enforcement-level": "invalid-level"},
        }

        result = _workspace_run_task_from(data)

        # Should default to ADVISORY for invalid values
        assert result.enforcement_level == TaskEnforcementLevel.ADVISORY

    def test_workspace_run_task_from_invalid_stage(self):
        """Test _workspace_run_task_from handles invalid stage."""

        data = {
            "id": "wstask-invalid-stage",
            "attributes": {
                "enforcement-level": "mandatory",
                "stage": "invalid-stage",
                "stages": ["pre_plan", "invalid-stage", "post_plan"],
            },
        }

        result = _workspace_run_task_from(data)

        # Should default to PRE_PLAN for invalid stage value
        assert result.stage == Stage.PRE_PLAN
        # Stages list should skip invalid stages
        assert len(result.stages) == 2
        assert result.stages[0] == Stage.PRE_PLAN
        assert result.stages[1] == Stage.POST_PLAN


class TestWorkspaceRunTasks:
    """Test the WorkspaceRunTasks service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def workspace_run_tasks_service(self, mock_transport):
        """Create a WorkspaceRunTasks service with mocked transport."""
        return WorkspaceRunTasks(mock_transport)

    # List Tests
    def test_list_with_invalid_workspace_id(self, workspace_run_tasks_service):
        """Test list with invalid workspace ID."""

        with pytest.raises(InvalidWorkspaceIDError):
            list(workspace_run_tasks_service.list(""))

    def test_list_success(self, workspace_run_tasks_service, mock_transport):
        """Test successful list operation."""

        mock_response_data = {
            "data": [
                {
                    "id": "wstask-1",
                    "attributes": {
                        "enforcement-level": "mandatory",
                        "stage": "pre_plan",
                        "stages": ["pre_plan"],
                    },
                },
                {
                    "id": "wstask-2",
                    "attributes": {
                        "enforcement-level": "advisory",
                        "stage": "post_plan",
                        "stages": ["post_plan"],
                    },
                },
            ],
            "links": {},
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = WorkspaceRunTaskListOptions(page_number=1, page_size=10)
        results = list(workspace_run_tasks_service.list("ws-123", options))

        assert len(results) == 2
        assert results[0].id == "wstask-1"
        assert results[0].enforcement_level == TaskEnforcementLevel.MANDATORY
        assert results[1].id == "wstask-2"
        assert results[1].enforcement_level == TaskEnforcementLevel.ADVISORY

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/api/v2/workspaces/ws-123/tasks"

    def test_list_pagination(self, workspace_run_tasks_service, mock_transport):
        """Test list with pagination."""

        # First page
        mock_response_page1_data = {
            "data": [
                {
                    "id": "wstask-1",
                    "attributes": {"enforcement-level": "mandatory"},
                }
            ],
            "links": {"next": "workspaces/ws-123/tasks?page[number]=2"},
        }

        # Second page
        mock_response_page2_data = {
            "data": [
                {
                    "id": "wstask-2",
                    "attributes": {"enforcement-level": "advisory"},
                }
            ],
            "links": {},
        }

        mock_response_1 = Mock()
        mock_response_1.json.return_value = mock_response_page1_data
        mock_response_2 = Mock()
        mock_response_2.json.return_value = mock_response_page2_data
        mock_transport.request.side_effect = [mock_response_1, mock_response_2]

        results = list(workspace_run_tasks_service.list("ws-123"))

        assert len(results) == 2
        assert results[0].id == "wstask-1"
        assert results[1].id == "wstask-2"
        assert mock_transport.request.call_count == 2

    # Read Tests
    def test_read_with_invalid_workspace_id(self, workspace_run_tasks_service):
        """Test read with invalid workspace ID."""

        with pytest.raises(InvalidWorkspaceIDError):
            workspace_run_tasks_service.read("", "wstask-123")

    def test_read_with_invalid_task_id(self, workspace_run_tasks_service):
        """Test read with invalid workspace task ID."""

        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            workspace_run_tasks_service.read("ws-123", "")

    def test_read_success(self, workspace_run_tasks_service, mock_transport):
        """Test successful read operation."""

        mock_response_data = {
            "data": {
                "id": "wstask-123",
                "attributes": {
                    "enforcement-level": "mandatory",
                    "stage": "pre_plan",
                    "stages": ["pre_plan", "post_plan"],
                },
                "relationships": {
                    "task": {"data": {"id": "task-456", "type": "tasks"}},
                    "workspace": {"data": {"id": "ws-789", "type": "workspaces"}},
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        result = workspace_run_tasks_service.read("ws-789", "wstask-123")

        assert result.id == "wstask-123"
        assert result.enforcement_level == TaskEnforcementLevel.MANDATORY
        assert result.stage == Stage.PRE_PLAN
        assert len(result.stages) == 2
        assert result.run_task.id == "task-456"
        assert result.workspace.id == "ws-789"

        # Verify API call
        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/workspaces/ws-789/tasks/wstask-123"
        )

    # Create Tests
    def test_create_with_invalid_workspace_id(self, workspace_run_tasks_service):
        """Test create with invalid workspace ID."""

        run_task = RunTask(
            id="task-123",
            name="Test Task",
            url="https://example.com",
            category="task",
            enabled=True,
        )
        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY,
            run_task=run_task,
        )

        with pytest.raises(InvalidWorkspaceIDError):
            workspace_run_tasks_service.create("", options)

    def test_create_with_invalid_run_task(self, workspace_run_tasks_service):
        """Test create with invalid run task."""

        # Run task with no ID
        run_task = RunTask(
            id="", name="Test", url="https://example.com", category="task", enabled=True
        )
        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY,
            run_task=run_task,
        )

        with pytest.raises(InvalidRunTaskIDError):
            workspace_run_tasks_service.create("ws-123", options)

    def test_create_success(self, workspace_run_tasks_service, mock_transport):
        """Test successful create operation."""

        mock_response_data = {
            "data": {
                "id": "wstask-new",
                "attributes": {
                    "enforcement-level": "mandatory",
                    "stage": "pre_plan",
                    "stages": ["pre_plan", "post_plan"],
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        run_task = RunTask(
            id="task-123",
            name="Test Task",
            url="https://example.com",
            category="task",
            enabled=True,
        )
        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY,
            run_task=run_task,
            stages=[Stage.PRE_PLAN, Stage.POST_PLAN],
        )

        result = workspace_run_tasks_service.create("ws-789", options)

        assert result.id == "wstask-new"
        assert result.enforcement_level == TaskEnforcementLevel.MANDATORY

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v2/workspaces/ws-789/tasks"
        payload = call_args[1]["json_body"]
        assert payload["data"]["type"] == "workspace-tasks"
        assert payload["data"]["attributes"]["enforcement-level"] == "mandatory"
        assert payload["data"]["attributes"]["stages"] == ["pre_plan", "post_plan"]
        assert payload["data"]["relationships"]["task"]["data"]["id"] == "task-123"

    def test_create_with_deprecated_stage(
        self, workspace_run_tasks_service, mock_transport
    ):
        """Test create with deprecated stage attribute."""

        mock_response_data = {
            "data": {
                "id": "wstask-new",
                "attributes": {
                    "enforcement-level": "advisory",
                    "stage": "post_plan",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        run_task = RunTask(
            id="task-123",
            name="Test Task",
            url="https://example.com",
            category="task",
            enabled=True,
        )
        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=TaskEnforcementLevel.ADVISORY,
            run_task=run_task,
            stage=Stage.POST_PLAN,
        )

        result = workspace_run_tasks_service.create("ws-789", options)

        assert result.id == "wstask-new"

        # Verify API call includes stage
        payload = mock_transport.request.call_args[1]["json_body"]
        assert payload["data"]["attributes"]["stage"] == "post_plan"

    # Update Tests
    def test_update_with_invalid_workspace_id(self, workspace_run_tasks_service):
        """Test update with invalid workspace ID."""

        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.ADVISORY
        )

        with pytest.raises(InvalidWorkspaceIDError):
            workspace_run_tasks_service.update("", "wstask-123", options)

    def test_update_with_invalid_task_id(self, workspace_run_tasks_service):
        """Test update with invalid workspace task ID."""

        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.ADVISORY
        )

        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            workspace_run_tasks_service.update("ws-123", "", options)

    def test_update_success(self, workspace_run_tasks_service, mock_transport):
        """Test successful update operation."""

        mock_response_data = {
            "data": {
                "id": "wstask-123",
                "attributes": {
                    "enforcement-level": "advisory",
                    "stage": "pre_plan",
                    "stages": ["pre_plan", "post_plan"],
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.ADVISORY,
            stages=[Stage.PRE_PLAN, Stage.POST_PLAN],
        )

        result = workspace_run_tasks_service.update("ws-789", "wstask-123", options)

        assert result.id == "wstask-123"
        assert result.enforcement_level == TaskEnforcementLevel.ADVISORY

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "/api/v2/workspaces/ws-789/tasks/wstask-123"
        payload = call_args[1]["json_body"]
        assert payload["data"]["attributes"]["enforcement-level"] == "advisory"
        assert payload["data"]["attributes"]["stages"] == ["pre_plan", "post_plan"]

    # Delete Tests
    def test_delete_with_invalid_workspace_id(self, workspace_run_tasks_service):
        """Test delete with invalid workspace ID."""

        with pytest.raises(InvalidWorkspaceIDError):
            workspace_run_tasks_service.delete("", "wstask-123")

    def test_delete_with_invalid_task_id(self, workspace_run_tasks_service):
        """Test delete with invalid workspace task ID."""

        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            workspace_run_tasks_service.delete("ws-123", "")

    def test_delete_success(self, workspace_run_tasks_service, mock_transport):
        """Test successful delete operation."""

        workspace_run_tasks_service.delete("ws-789", "wstask-123")

        # Verify API call
        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/workspaces/ws-789/tasks/wstask-123"
        )
