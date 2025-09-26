"""Unit tests for the run task module."""

from unittest.mock import Mock, patch

import pytest

from tfe._http import HTTPTransport
from tfe.errors import (
    InvalidOrgError,
    InvalidRunTaskCategoryError,
    InvalidRunTaskIDError,
    InvalidRunTaskURLError,
    RequiredNameError,
)
from tfe.models.agent import AgentPool
from tfe.models.run_task import (
    GlobalRunTaskOptions,
    RunTaskCreateOptions,
    RunTaskIncludeOptions,
    RunTaskListOptions,
    RunTaskReadOptions,
    RunTaskUpdateOptions,
    Stage,
    TaskEnforcementLevel,
)
from tfe.resources.run_task import RunTasks, _run_task_from


class TestRunTaskFrom:
    """Test the _run_task_from function."""

    def test_run_task_from_comprehensive(self):
        """Test _run_task_from with various data scenarios."""

        # Testdata with all fields populated
        data = {
            "id": "task-123",
            "attributes": {
                "name": "Test Task",
                "url": "https://example.com/webhook",
                "category": "task",
                "enabled": True,
                "global-configuration": {
                    "enabled": True,
                    "stages": ["pre-plan", "post-apply"],
                    "enforcement-level": "mandatory",
                },
            },
            "relationships": {
                "agent-pool": {"data": {"id": "apool-123", "type": "agent-pools"}},
                "organization": {"data": {"id": "org-123", "type": "organizations"}},
                "workspace-tasks": {
                    "data": [
                        {"id": "wstask-1", "type": "workspace-tasks"},
                        {"id": "wstask-2", "type": "workspace-tasks"},
                    ]
                },
            },
        }

        result = _run_task_from(data, org="org-123")

        assert result.id == "task-123"
        assert result.name == "Test Task"
        assert result.url == "https://example.com/webhook"
        assert result.category == "task"
        assert result.enabled is True
        assert result.description is None
        assert result.hmac_key is None
        assert result.global_configuration is not None
        assert result.global_configuration.enabled is True
        assert result.global_configuration.stages == [Stage.PRE_PLAN, Stage.POST_APPLY]
        assert (
            result.global_configuration.enforcement_level
            == TaskEnforcementLevel.MANDATORY
        )
        assert result.agent_pool is not None
        assert result.agent_pool.id == "apool-123"
        assert result.organization is not None
        assert result.organization.id == "org-123"
        assert result.organization.name == "org-123"
        assert isinstance(result.workspace_run_tasks, list)
        assert len(result.workspace_run_tasks) == 2
        assert result.workspace_run_tasks[0].id == "wstask-1"
        assert result.workspace_run_tasks[1].id == "wstask-2"


class TestRunTasks:
    """Test the RunTasks.list method."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def run_tasks_service(self, mock_transport):
        """Create a RunTasks service with mocked transport."""
        return RunTasks(mock_transport)

    def test_list_run_task(self, run_tasks_service):
        """Test cases for list method with various scenarios."""

        # Test 1: Invalid organization ID should raise error
        with pytest.raises(InvalidOrgError):
            list(run_tasks_service.list("", None))

        with pytest.raises(InvalidOrgError):
            list(run_tasks_service.list(None, None))

        # Test 2: Default options (no options provided)
        mock_data = [
            {
                "id": "task-1",
                "attributes": {
                    "name": "Task 1",
                    "url": "https://example.com/webhook1",
                    "category": "task",
                    "enabled": True,
                },
            },
            {
                "id": "task-2",
                "attributes": {
                    "name": "Task 2",
                    "url": "https://example.com/webhook2",
                    "category": "task",
                    "enabled": False,
                },
            },
        ]

        with patch.object(run_tasks_service, "_list") as mock_list:
            mock_list.return_value = iter(mock_data)

            result = list(run_tasks_service.list("org-123"))

            # Verify _list was called with correct parameters
            mock_list.assert_called_once_with(
                "/api/v2/organizations/org-123/tasks", params={}
            )

            # Verify results
            assert len(result) == 2
            assert result[0].id == "task-1"
            assert result[0].name == "Task 1"
            assert result[1].id == "task-2"
            assert result[1].name == "Task 2"

        # Test 3: All options combined (includes pagination and multiple include options)
        options = RunTaskListOptions(
            page_number=3,
            page_size=25,
            include=[
                RunTaskIncludeOptions.RUN_TASK_WORKSPACE_TASKS,
                RunTaskIncludeOptions.RUN_TASK_WORKSPACE,
            ],
        )

        with patch.object(run_tasks_service, "_list") as mock_list:
            mock_list.return_value = iter([])

            list(run_tasks_service.list("org-complete", options))

            mock_list.assert_called_once_with(
                "/api/v2/organizations/org-complete/tasks",
                params={
                    "page[number]": "3",
                    "page[size]": "25",
                    "include": "workspace_tasks,workspace_tasks.workspace",
                },
            )

        # Test 4: Method returns iterator
        with patch.object(run_tasks_service, "_list") as mock_list:
            mock_list.return_value = iter([])

            result = run_tasks_service.list("org-iterator")

            # Verify it's an iterator
            assert hasattr(result, "__iter__")
            assert hasattr(result, "__next__")

    def test_create_run_task(self, run_tasks_service):
        """Test cases for create method with various scenarios."""

        # Test 1: Missing name should raise error
        with pytest.raises(RequiredNameError):
            options = RunTaskCreateOptions(
                name="",  # Empty string should trigger our validation
                url="https://example.com/webhook",
                category="task",
            )
            run_tasks_service.create("org-123", options)

        # Test 2: Missing URL should raise error
        with pytest.raises(InvalidRunTaskURLError):
            options = RunTaskCreateOptions(
                name="Test Task",
                url="",  # Empty string should trigger our validation
                category="task",
            )
            run_tasks_service.create("org-123", options)

        # Test 3: Invalid category should raise error
        with pytest.raises(InvalidRunTaskCategoryError):
            options = RunTaskCreateOptions(
                name="Test Task", url="https://example.com/webhook", category="invalid"
            )
            run_tasks_service.create("org-123", options)

        # Test 4: Create with all optional fields
        mock_response_data_full = {
            "id": "task-456",
            "attributes": {
                "name": "Advanced Task",
                "url": "https://example.com/advanced-webhook",
                "category": "task",
                "enabled": False,
                "description": "Advanced task description",
                "hmac_key": "secret-key-123",
                "global-configuration": {
                    "enabled": True,
                    "stages": ["pre-plan", "post-plan"],
                    "enforcement-level": "mandatory",
                },
            },
            "relationships": {
                "agent-pool": {"data": {"type": "agent_pools", "id": "apool-123"}}
            },
        }

        mock_response_full = Mock()
        mock_response_full.json.return_value = {"data": mock_response_data_full}

        with patch.object(run_tasks_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response_full

            options = RunTaskCreateOptions(
                name="Advanced Task",
                url="https://example.com/advanced-webhook",
                category="task",
                description="Advanced task description",
                hmac_key="secret-key-123",
                enabled=False,
                global_configuration=GlobalRunTaskOptions(
                    enabled=True,
                    stages=[Stage.PRE_PLAN, Stage.POST_PLAN],
                    enforcement_level=TaskEnforcementLevel.MANDATORY,
                ),
                agent_pool=AgentPool(id="apool-123"),
            )

            result = run_tasks_service.create("org-456", options)

            # Verify request was made correctly
            mock_transport.request.assert_called_once()
            call_args = mock_transport.request.call_args

            assert call_args[0][0] == "POST"  # HTTP method
            assert call_args[0][1] == "/api/v2/organizations/org-456/tasks"  # URL

            # Verify response
            assert result.id == "task-456"
            assert result.name == "Advanced Task"
            assert result.description == "Advanced task description"
            assert result.enabled is False

    def test_delete_run_task(self, run_tasks_service):
        """Test case for run task delete operations."""

        with patch.object(run_tasks_service, "t") as mock_transport:
            mock_transport.request.return_value = None  # DELETE returns no content

            run_tasks_service.delete("task-123")

            # Verify request was made correctly
            mock_transport.request.assert_called_once_with(
                "DELETE", "/api/v2/tasks/task-123"
            )

    def test_read_run_task(self, run_tasks_service):
        """Test cases for RunTask read operations."""

        # Mock response for read request with included relationships
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "task-123",
                "type": "tasks",
                "attributes": {
                    "name": "test-task",
                    "url": "https://example.com/task",
                    "description": "Test task description",
                    "category": "task",
                    "enabled": True,
                    "hmac-key": "secret-key",
                },
                "relationships": {
                    "organization": {"data": {"id": "org-123", "type": "organizations"}}
                },
                "links": {"self": "/api/v2/tasks/task-123"},
            },
            "included": [
                {
                    "id": "org-123",
                    "type": "organizations",
                    "attributes": {"name": "test-org"},
                }
            ],
        }

        with patch.object(run_tasks_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            result = run_tasks_service.read("task-123")

            # Verify request was made correctly
            mock_transport.request.assert_called_once_with(
                "GET", "/api/v2/tasks/task-123", params={}
            )

            # Verify returned data
            assert result.id == "task-123"
            assert result.name == "test-task"
            assert result.url == "https://example.com/task"
            assert result.description == "Test task description"
            assert result.category == "task"
            assert result.enabled is True
            assert result.hmac_key == "secret-key"

        options = RunTaskReadOptions(
            include=[RunTaskIncludeOptions.RUN_TASK_WORKSPACE_TASKS]
        )

        with patch.object(run_tasks_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            result = run_tasks_service.read_with_options("task-123", options)

            # Verify request was made with include parameter
            mock_transport.request.assert_called_once_with(
                "GET", "/api/v2/tasks/task-123", params={"include": "workspace_tasks"}
            )

        """Test read method with multiple include options."""

        options = RunTaskReadOptions(
            include=[
                RunTaskIncludeOptions.RUN_TASK_WORKSPACE_TASKS,
                RunTaskIncludeOptions.RUN_TASK_WORKSPACE,
            ]
        )

        with patch.object(run_tasks_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            result = run_tasks_service.read_with_options("task-123", options)

            # Verify request was made with multiple includes
            mock_transport.request.assert_called_once_with(
                "GET",
                "/api/v2/tasks/task-123",
                params={"include": "workspace_tasks,workspace_tasks.workspace"},
            )

    def test_update_task_all_fields(self, run_tasks_service):
        """Test cases for RunTask update operations."""

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "task-123",
                "type": "tasks",
                "attributes": {
                    "name": "comprehensive-update",
                    "url": "https://updated-example.com/webhook",
                    "description": "Comprehensive update test",
                    "category": "task",
                    "enabled": False,
                    "hmac-key": "new-secret-key",
                },
            }
        }

        options = RunTaskUpdateOptions(
            name="comprehensive-update",
            description="Comprehensive update test",
            url="https://updated-example.com/webhook",
            category="task",
            hmac_key="new-secret-key",
            enabled=False,
        )

        with patch.object(run_tasks_service, "t") as mock_transport:
            mock_transport.request.return_value = mock_response

            result = run_tasks_service.update("task-123", options)

            # Verify comprehensive request body
            call_args = mock_transport.request.call_args
            assert call_args[0] == ("PATCH", "/api/v2/tasks/task-123")

            assert result.id == "task-123"
            assert result.name == "comprehensive-update"
            assert result.url == "https://updated-example.com/webhook"
            assert result.description == "Comprehensive update test"
            assert result.category == "task"
            assert result.enabled is False
            assert result.hmac_key == "new-secret-key"
            assert result.organization is None
            assert result.workspace_run_tasks == []

    def test_update_task_validation_errors(self, run_tasks_service):
        """Test update method validation errors."""

        # Test invalid task ID
        options = RunTaskUpdateOptions(name="test-update")

        with pytest.raises(InvalidRunTaskIDError):
            run_tasks_service.update("", options)

        # Test invalid name
        options = RunTaskUpdateOptions(name="")
        with pytest.raises(RequiredNameError):
            run_tasks_service.update("task-123", options)

        # Test invalid URL
        options = RunTaskUpdateOptions(url="")
        with pytest.raises(InvalidRunTaskURLError):
            run_tasks_service.update("task-123", options)

        # Test invalid category
        options = RunTaskUpdateOptions(category="invalid-category")
        with pytest.raises(InvalidRunTaskCategoryError):
            run_tasks_service.update("task-123", options)
