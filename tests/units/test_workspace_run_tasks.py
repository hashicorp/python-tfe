"""Unit tests for the workspace run tasks module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidWorkspaceIDError,
    InvalidWorkspaceRunTaskIDError,
)
from pytfe.models.workspace_run_task import (
    Stage,
    TaskEnforcementLevel,
    WorkspaceRunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskIncludeOpt,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskReadOptions,
    WorkspaceRunTaskUpdateOptions,
)
from pytfe.resources.workspace_run_tasks import (
    WorkspaceRunTasksService,
    _workspace_run_task_from,
)


class TestWorkspaceRunTaskFrom:
    """Test the _workspace_run_task_from function."""

    def test_workspace_run_task_from_comprehensive(self):
        """Test _workspace_run_task_from with all fields populated."""
        data = {
            "id": "wsrt-123456789",
            "type": "workspace-tasks",
            "attributes": {
                "enforcement-level": "mandatory",
                "stage": "post-plan",
                "created-at": "2023-01-01T00:00:00Z",
                "updated-at": "2023-01-02T00:00:00Z",
            },
            "relationships": {
                "workspace": {"data": {"id": "ws-abc123", "type": "workspaces"}},
                "task": {"data": {"id": "task-xyz789", "type": "tasks"}},
            },
        }

        result = _workspace_run_task_from(data)

        assert result.id == "wsrt-123456789"
        assert result.type == "workspace-tasks"
        assert result.enforcement_level == TaskEnforcementLevel.MANDATORY
        assert result.stage == Stage.POST_PLAN
        assert result.created_at == "2023-01-01T00:00:00Z"
        assert result.updated_at == "2023-01-02T00:00:00Z"
        assert result.workspace is not None
        assert result.workspace["data"]["id"] == "ws-abc123"
        assert result.workspace["data"]["type"] == "workspaces"
        assert result.run_task is not None
        assert result.run_task["data"]["id"] == "task-xyz789"
        assert result.run_task["data"]["type"] == "tasks"

    def test_workspace_run_task_from_minimal(self):
        """Test _workspace_run_task_from with minimal required fields."""
        data = {
            "id": "wsrt-minimal",
            "attributes": {
                "enforcement-level": "advisory",
                "stage": "pre-plan",
            },
        }

        result = _workspace_run_task_from(data)

        assert result.id == "wsrt-minimal"
        assert result.type == "workspace-tasks"
        assert result.enforcement_level == TaskEnforcementLevel.ADVISORY
        assert result.stage == Stage.PRE_PLAN
        assert result.created_at is None
        assert result.updated_at is None
        assert result.workspace is None
        assert result.run_task is None

    def test_workspace_run_task_from_invalid_enum_values(self):
        """Test _workspace_run_task_from with invalid enum values falls back to defaults."""
        data = {
            "id": "wsrt-invalid",
            "attributes": {
                "enforcement-level": "invalid-level",
                "stage": "invalid-stage",
            },
        }

        result = _workspace_run_task_from(data)

        assert result.id == "wsrt-invalid"
        assert result.enforcement_level == TaskEnforcementLevel.ADVISORY  # Default
        assert result.stage == Stage.POST_PLAN  # Default

    def test_workspace_run_task_from_missing_attributes(self):
        """Test _workspace_run_task_from handles missing attributes gracefully."""
        data = {"id": "wsrt-missing", "attributes": {}}

        result = _workspace_run_task_from(data)

        assert result.id == "wsrt-missing"
        assert result.enforcement_level == TaskEnforcementLevel.ADVISORY  # Default
        assert result.stage == Stage.POST_PLAN  # Default

    def test_workspace_run_task_from_none_relationships(self):
        """Test _workspace_run_task_from handles None relationship data."""
        data = {
            "id": "wsrt-none-rels",
            "attributes": {
                "enforcement-level": "mandatory",
                "stage": "pre-apply",
            },
            "relationships": {
                "workspace": {"data": None},
                "run-task": {"data": None},
            },
        }

        result = _workspace_run_task_from(data)

        assert result.id == "wsrt-none-rels"
        assert result.workspace is None
        assert result.run_task is None


class TestWorkspaceRunTasksService:
    """Test the WorkspaceRunTasksService class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        """Create a WorkspaceRunTasksService with mocked transport."""
        return WorkspaceRunTasksService(mock_transport)

    def test_list_valid_workspace_id(self, service, mock_transport):
        """Test list method with valid workspace ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "wsrt-1",
                    "type": "workspace-tasks",
                    "attributes": {
                        "enforcement-level": "mandatory",
                        "stage": "post-plan",
                    },
                },
                {
                    "id": "wsrt-2",
                    "type": "workspace-tasks",
                    "attributes": {
                        "enforcement-level": "advisory",
                        "stage": "pre-plan",
                    },
                },
            ]
        }
        mock_transport.request.return_value = mock_response

        # Mock the _list method from base class
        service._list = Mock(
            return_value=[
                {
                    "id": "wsrt-1",
                    "type": "workspace-tasks",
                    "attributes": {
                        "enforcement-level": "mandatory",
                        "stage": "post-plan",
                    },
                },
                {
                    "id": "wsrt-2",
                    "type": "workspace-tasks",
                    "attributes": {
                        "enforcement-level": "advisory",
                        "stage": "pre-plan",
                    },
                },
            ]
        )

        result = list(service.list("ws-valid123"))

        assert len(result) == 2
        assert result[0].id == "wsrt-1"
        assert result[0].enforcement_level == TaskEnforcementLevel.MANDATORY
        assert result[0].stage == Stage.POST_PLAN
        assert result[1].id == "wsrt-2"
        assert result[1].enforcement_level == TaskEnforcementLevel.ADVISORY
        assert result[1].stage == Stage.PRE_PLAN

        service._list.assert_called_once_with(
            "/api/v2/workspaces/ws-valid123/tasks", params={}
        )

    def test_list_with_options(self, service):
        """Test list method with pagination and include options."""
        options = WorkspaceRunTaskListOptions(
            page_number=2,
            page_size=10,
            include=[
                WorkspaceRunTaskIncludeOpt.RUN_TASK,
                WorkspaceRunTaskIncludeOpt.WORKSPACE,
            ],
        )

        # Mock the _list method
        service._list = Mock(return_value=[])

        list(service.list("ws-123", options=options))

        service._list.assert_called_once_with(
            "/api/v2/workspaces/ws-123/tasks",
            params={
                "page[number]": 2,
                "page[size]": 10,
                "include": "run_task,workspace",
            },
        )

    def test_list_invalid_workspace_id(self, service):
        """Test list method with invalid workspace ID."""
        with pytest.raises(InvalidWorkspaceIDError):
            list(service.list(""))

        with pytest.raises(InvalidWorkspaceIDError):
            list(service.list("   "))

    def test_get_valid_ids(self, service, mock_transport):
        """Test get method with valid IDs."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wsrt-get123",
                "type": "workspace-tasks",
                "attributes": {
                    "enforcement-level": "mandatory",
                    "stage": "post-apply",
                    "created-at": "2023-01-01T00:00:00Z",
                },
                "relationships": {
                    "workspace": {"data": {"id": "ws-123", "type": "workspaces"}},
                    "task": {"data": {"id": "task-456", "type": "tasks"}},
                },
            }
        }
        mock_transport.request.return_value = mock_response

        result = service.get("ws-123", "wsrt-get123")

        assert result.id == "wsrt-get123"
        assert result.enforcement_level == TaskEnforcementLevel.MANDATORY
        assert result.stage == Stage.POST_APPLY
        assert result.created_at == "2023-01-01T00:00:00Z"
        assert result.workspace["data"]["id"] == "ws-123"
        assert result.run_task["data"]["id"] == "task-456"

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/workspaces/ws-123/tasks/wsrt-get123", params={}
        )

    def test_get_with_include_options(self, service, mock_transport):
        """Test get method with include options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wsrt-include",
                "type": "workspace-tasks",
                "attributes": {"enforcement-level": "advisory", "stage": "pre-plan"},
            }
        }
        mock_transport.request.return_value = mock_response

        options = WorkspaceRunTaskReadOptions(
            include=[WorkspaceRunTaskIncludeOpt.RUN_TASK]
        )

        result = service.get("ws-123", "wsrt-include", options=options)

        assert result.id == "wsrt-include"
        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/workspaces/ws-123/tasks/wsrt-include",
            params={"include": "run_task"},
        )

    def test_get_invalid_workspace_id(self, service):
        """Test get method with invalid workspace ID."""
        with pytest.raises(InvalidWorkspaceIDError):
            service.get("", "wsrt-123")

    def test_get_invalid_task_id(self, service):
        """Test get method with invalid task ID."""
        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            service.get("ws-123", "")

    def test_create_success(self, service, mock_transport):
        """Test create method success."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wsrt-created",
                "type": "workspace-tasks",
                "attributes": {
                    "enforcement-level": "mandatory",
                    "stage": "post-plan",
                },
                "relationships": {
                    "run-task": {"data": {"id": "task-123", "type": "tasks"}},
                },
            }
        }
        mock_transport.request.return_value = mock_response

        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY,
            stage=Stage.POST_PLAN,
            run_task={"data": {"type": "tasks", "id": "task-123"}},
        )

        result = service.create("ws-123", options)

        assert result.id == "wsrt-created"
        assert result.enforcement_level == TaskEnforcementLevel.MANDATORY
        assert result.stage == Stage.POST_PLAN

        expected_data = {
            "data": {
                "type": "workspace-tasks",
                "attributes": {
                    "enforcement-level": "mandatory",
                },
                "relationships": {
                    "task": {"data": {"type": "tasks", "id": "task-123"}}
                },
            }
        }

        mock_transport.request.assert_called_once_with(
            "POST", "/api/v2/workspaces/ws-123/tasks", json_body=expected_data
        )

    def test_create_minimal_options(self, service, mock_transport):
        """Test create method with minimal options (no stage)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wsrt-minimal",
                "type": "workspace-tasks",
                "attributes": {"enforcement-level": "advisory"},
            }
        }
        mock_transport.request.return_value = mock_response

        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=TaskEnforcementLevel.ADVISORY,
            run_task={"data": {"type": "tasks", "id": "task-456"}},
        )

        result = service.create("ws-456", options)

        assert result.id == "wsrt-minimal"
        assert result.enforcement_level == TaskEnforcementLevel.ADVISORY

        expected_data = {
            "data": {
                "type": "workspace-tasks",
                "attributes": {"enforcement-level": "advisory"},
                "relationships": {
                    "task": {"data": {"type": "tasks", "id": "task-456"}}
                },
            }
        }

        mock_transport.request.assert_called_once_with(
            "POST", "/api/v2/workspaces/ws-456/tasks", json_body=expected_data
        )

    def test_create_invalid_workspace_id(self, service):
        """Test create method with invalid workspace ID."""
        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=TaskEnforcementLevel.ADVISORY,
            run_task={"data": {"type": "tasks", "id": "task-123"}},
        )

        with pytest.raises(InvalidWorkspaceIDError):
            service.create("", options)

    def test_update_success(self, service, mock_transport):
        """Test update method success."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wsrt-updated",
                "type": "workspace-tasks",
                "attributes": {
                    "enforcement-level": "advisory",
                    "stage": "pre-apply",
                },
            }
        }
        mock_transport.request.return_value = mock_response

        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.ADVISORY, stage=Stage.PRE_APPLY
        )

        result = service.update("ws-123", "wsrt-update", options)

        assert result.id == "wsrt-updated"
        assert result.enforcement_level == TaskEnforcementLevel.ADVISORY
        assert result.stage == Stage.PRE_APPLY

        expected_data = {
            "data": {
                "type": "workspace-tasks",
                "id": "wsrt-update",
                "attributes": {
                    "enforcement-level": "advisory",
                    "stage": "pre-apply",
                },
            }
        }

        mock_transport.request.assert_called_once_with(
            "PATCH",
            "/api/v2/workspaces/ws-123/tasks/wsrt-update",
            json_body=expected_data,
        )

    def test_update_partial_options(self, service, mock_transport):
        """Test update method with partial options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wsrt-partial",
                "type": "workspace-tasks",
                "attributes": {"enforcement-level": "mandatory"},
            }
        }
        mock_transport.request.return_value = mock_response

        # Only update enforcement level, not stage
        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY
        )

        result = service.update("ws-789", "wsrt-partial", options)

        assert result.id == "wsrt-partial"

        expected_data = {
            "data": {
                "type": "workspace-tasks",
                "id": "wsrt-partial",
                "attributes": {"enforcement-level": "mandatory"},
            }
        }

        mock_transport.request.assert_called_once_with(
            "PATCH",
            "/api/v2/workspaces/ws-789/tasks/wsrt-partial",
            json_body=expected_data,
        )

    def test_update_invalid_workspace_id(self, service):
        """Test update method with invalid workspace ID."""
        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY
        )

        with pytest.raises(InvalidWorkspaceIDError):
            service.update("", "wsrt-123", options)

    def test_update_invalid_task_id(self, service):
        """Test update method with invalid task ID."""
        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY
        )

        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            service.update("ws-123", "", options)

    def test_delete_success(self, service, mock_transport):
        """Test delete method success."""
        # DELETE requests typically return no content
        mock_response = Mock()
        mock_response.json.return_value = None
        mock_transport.request.return_value = mock_response

        # Should not raise any exception
        service.delete("ws-123", "wsrt-delete")

        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/workspaces/ws-123/tasks/wsrt-delete"
        )

    def test_delete_invalid_workspace_id(self, service):
        """Test delete method with invalid workspace ID."""
        with pytest.raises(InvalidWorkspaceIDError):
            service.delete("", "wsrt-123")

    def test_delete_invalid_task_id(self, service):
        """Test delete method with invalid task ID."""
        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            service.delete("ws-123", "")


class TestWorkspaceRunTaskModels:
    """Test workspace run task model classes."""

    def test_workspace_run_task_creation(self):
        """Test WorkspaceRunTask model creation."""
        workspace = {"data": {"id": "ws-123", "type": "workspaces"}}
        run_task = {"data": {"id": "task-456", "type": "tasks"}}

        task = WorkspaceRunTask(
            id="wsrt-model123",
            enforcement_level=TaskEnforcementLevel.MANDATORY,
            stage=Stage.PRE_PLAN,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-02T00:00:00Z",
            workspace=workspace,
            run_task=run_task,
        )

        assert task.id == "wsrt-model123"
        assert task.type == "workspace-tasks"  # Default value
        assert task.enforcement_level == TaskEnforcementLevel.MANDATORY
        assert task.stage == Stage.PRE_PLAN
        assert task.created_at == "2023-01-01T00:00:00Z"
        assert task.updated_at == "2023-01-02T00:00:00Z"
        assert task.workspace == workspace
        assert task.run_task == run_task

    def test_workspace_run_task_create_options(self):
        """Test WorkspaceRunTaskCreateOptions model."""
        run_task_ref = {"data": {"type": "tasks", "id": "task-123"}}

        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=TaskEnforcementLevel.ADVISORY,
            stage=Stage.POST_APPLY,
            run_task=run_task_ref,
        )

        assert options.type == "workspace-tasks"
        assert options.enforcement_level == TaskEnforcementLevel.ADVISORY
        assert options.stage == Stage.POST_APPLY
        assert options.run_task == run_task_ref

    def test_workspace_run_task_update_options(self):
        """Test WorkspaceRunTaskUpdateOptions model."""
        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY,
            stage=Stage.PRE_PLAN,
        )

        assert options.type == "workspace-tasks"
        assert options.enforcement_level == TaskEnforcementLevel.MANDATORY
        assert options.stage == Stage.PRE_PLAN

    def test_workspace_run_task_list_options(self):
        """Test WorkspaceRunTaskListOptions model."""
        options = WorkspaceRunTaskListOptions(
            page_number=3,
            page_size=25,
            include=[WorkspaceRunTaskIncludeOpt.RUN_TASK],
        )

        assert options.page_number == 3
        assert options.page_size == 25
        assert options.include == [WorkspaceRunTaskIncludeOpt.RUN_TASK]

    def test_workspace_run_task_read_options(self):
        """Test WorkspaceRunTaskReadOptions model."""
        options = WorkspaceRunTaskReadOptions(
            include=[
                WorkspaceRunTaskIncludeOpt.RUN_TASK,
                WorkspaceRunTaskIncludeOpt.WORKSPACE,
            ]
        )

        assert len(options.include) == 2
        assert WorkspaceRunTaskIncludeOpt.RUN_TASK in options.include
        assert WorkspaceRunTaskIncludeOpt.WORKSPACE in options.include

    def test_stage_enum_values(self):
        """Test Stage enum values."""
        assert Stage.PRE_PLAN.value == "pre-plan"
        assert Stage.POST_PLAN.value == "post-plan"
        assert Stage.PRE_APPLY.value == "pre-apply"
        assert Stage.POST_APPLY.value == "post-apply"

    def test_task_enforcement_level_enum_values(self):
        """Test TaskEnforcementLevel enum values."""
        assert TaskEnforcementLevel.ADVISORY.value == "advisory"
        assert TaskEnforcementLevel.MANDATORY.value == "mandatory"

    def test_workspace_run_task_include_opt_enum_values(self):
        """Test WorkspaceRunTaskIncludeOpt enum values."""
        assert WorkspaceRunTaskIncludeOpt.RUN_TASK.value == "run_task"
        assert WorkspaceRunTaskIncludeOpt.WORKSPACE.value == "workspace"
