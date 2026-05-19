# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for workspace run tasks."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidWorkspaceIDError, InvalidWorkspaceRunTaskIDError
from pytfe.models.workspace_run_task import (
    WorkspaceRunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskRunTask,
    WorkspaceRunTaskUpdateOptions,
)
from pytfe.resources.workspace_run_task import (
    WorkspaceRunTasks,
    _workspace_run_task_from,
)


class TestWorkspaceRunTaskFrom:
    def test_workspace_run_task_from_full(self):
        data = {
            "id": "wst-123",
            "attributes": {
                "enforcement-level": "mandatory",
                "stage": "post_plan",
                "stages": ["post_plan", "pre_apply"],
            },
            "relationships": {
                "task": {"data": {"id": "task-123", "type": "tasks"}},
                "workspace": {"data": {"id": "ws-123", "type": "workspaces"}},
            },
        }

        result = _workspace_run_task_from(data)

        assert isinstance(result, WorkspaceRunTask)
        assert result.id == "wst-123"
        assert result.enforcement_level == "mandatory"
        assert result.stage == "post_plan"
        assert result.stages == ["post_plan", "pre_apply"]
        assert result.run_task is not None
        assert result.run_task.id == "task-123"
        assert result.workspace is not None
        assert result.workspace.id == "ws-123"


class TestWorkspaceRunTasks:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def workspace_run_tasks_service(self, mock_transport):
        return WorkspaceRunTasks(mock_transport)

    def test_create_success(self, workspace_run_tasks_service, mock_transport):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wst-1",
                "attributes": {
                    "enforcement-level": "advisory",
                    "stages": ["post_plan"],
                },
                "relationships": {
                    "task": {"data": {"id": "task-1", "type": "tasks"}},
                    "workspace": {"data": {"id": "ws-1", "type": "workspaces"}},
                },
            }
        }
        mock_transport.request.return_value = mock_response

        options = WorkspaceRunTaskCreateOptions(
            enforcement_level="advisory",
            run_task=WorkspaceRunTaskRunTask(id="task-1"),
            stages=["post_plan"],
        )

        result = workspace_run_tasks_service.create("ws-1", options)

        assert isinstance(result, WorkspaceRunTask)
        assert result.id == "wst-1"
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v2/workspaces/ws-1/tasks"

    def test_create_validation_errors(self, workspace_run_tasks_service):
        options = WorkspaceRunTaskCreateOptions(
            enforcement_level="advisory",
            run_task=WorkspaceRunTaskRunTask(id="task-1"),
        )

        with pytest.raises(InvalidWorkspaceIDError):
            workspace_run_tasks_service.create("", options)

    def test_list_success(self, workspace_run_tasks_service):
        workspace_run_tasks_service._list = Mock(
            return_value=[
                {
                    "id": "wst-1",
                    "attributes": {"enforcement-level": "advisory", "stages": []},
                    "relationships": {},
                },
                {
                    "id": "wst-2",
                    "attributes": {
                        "enforcement-level": "mandatory",
                        "stages": ["pre_apply"],
                    },
                    "relationships": {},
                },
            ]
        )

        options = WorkspaceRunTaskListOptions(page_size=10, page_number=2)
        items = list(workspace_run_tasks_service.list("ws-1", options))

        workspace_run_tasks_service._list.assert_called_once_with(
            "/api/v2/workspaces/ws-1/tasks",
            params={"page[size]": 10, "page[number]": 2},
        )
        assert len(items) == 2
        assert items[0].id == "wst-1"
        assert items[1].id == "wst-2"

    def test_list_validation_error(self, workspace_run_tasks_service):
        with pytest.raises(InvalidWorkspaceIDError):
            list(workspace_run_tasks_service.list(""))

    def test_read_success(self, workspace_run_tasks_service, mock_transport):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wst-1",
                "attributes": {
                    "enforcement-level": "advisory",
                    "stages": ["post_plan"],
                },
                "relationships": {},
            }
        }
        mock_transport.request.return_value = mock_response

        result = workspace_run_tasks_service.read("ws-1", "wst-1")

        assert isinstance(result, WorkspaceRunTask)
        assert result.id == "wst-1"
        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/workspaces/ws-1/tasks/wst-1"
        )

    def test_read_validation_error(self, workspace_run_tasks_service):
        with pytest.raises(InvalidWorkspaceIDError):
            workspace_run_tasks_service.read("", "wst-1")
        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            workspace_run_tasks_service.read("ws-1", "")

    def test_update_success(self, workspace_run_tasks_service, mock_transport):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "wst-1",
                "attributes": {
                    "enforcement-level": "mandatory",
                    "stages": ["post_plan", "pre_apply"],
                },
                "relationships": {},
            }
        }
        mock_transport.request.return_value = mock_response

        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level="mandatory",
            stages=["post_plan", "pre_apply"],
        )
        result = workspace_run_tasks_service.update("ws-1", "wst-1", options)

        assert isinstance(result, WorkspaceRunTask)
        assert result.enforcement_level == "mandatory"
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "/api/v2/workspaces/ws-1/tasks/wst-1"

    def test_update_validation_error(self, workspace_run_tasks_service):
        options = WorkspaceRunTaskUpdateOptions(enforcement_level="mandatory")

        with pytest.raises(InvalidWorkspaceIDError):
            workspace_run_tasks_service.update("", "wst-1", options)
        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            workspace_run_tasks_service.update("ws-1", "", options)

    def test_delete_success(self, workspace_run_tasks_service, mock_transport):
        workspace_run_tasks_service.delete("ws-1", "wst-1")

        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/workspaces/ws-1/tasks/wst-1"
        )

    def test_delete_validation_error(self, workspace_run_tasks_service):
        with pytest.raises(InvalidWorkspaceIDError):
            workspace_run_tasks_service.delete("", "wst-1")
        with pytest.raises(InvalidWorkspaceRunTaskIDError):
            workspace_run_tasks_service.delete("ws-1", "")
