# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import quote

from ..errors import (
    InvalidRunTaskIDError,
    InvalidWorkspaceIDError,
    InvalidWorkspaceRunTaskIDError,
)
from ..models.workspace_run_task import (
    WorkspaceRunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskRunTask,
    WorkspaceRunTaskUpdateOptions,
    WorkspaceRunTaskWorkspace,
)
from ..utils import _safe_str, valid_string_id
from ._base import _Service


def _workspace_run_task_from(data: dict[str, Any]) -> WorkspaceRunTask:
    """Convert API response data to WorkspaceRunTask model."""
    attributes = data.get("attributes", {}) or {}
    relationships = data.get("relationships", {}) or {}

    run_task = None
    run_task_data = relationships.get("task", {}).get("data")
    if isinstance(run_task_data, dict) and run_task_data.get("id"):
        run_task = WorkspaceRunTaskRunTask(id=_safe_str(run_task_data.get("id")))

    workspace = None
    workspace_data = relationships.get("workspace", {}).get("data")
    if isinstance(workspace_data, dict) and workspace_data.get("id"):
        workspace = WorkspaceRunTaskWorkspace(id=_safe_str(workspace_data.get("id")))

    return WorkspaceRunTask(
        id=_safe_str(data.get("id")),
        enforcement_level=_safe_str(attributes.get("enforcement-level")) or None,
        stage=_safe_str(attributes.get("stage")) or None,
        stages=[
            stage for stage in attributes.get("stages", []) if isinstance(stage, str)
        ],
        run_task=run_task,
        workspace=workspace,
    )


class WorkspaceRunTasks(_Service):
    """Workspace run tasks service."""

    def create(
        self, workspace_id: str, options: WorkspaceRunTaskCreateOptions
    ) -> WorkspaceRunTask:
        """Attach a run task to a workspace."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        options.validate_for_create()

        body: dict[str, Any] = {
            "data": {
                "type": "workspace-tasks",
                "attributes": {
                    "enforcement-level": options.enforcement_level,
                },
                "relationships": {
                    "task": {"data": {"type": "tasks", "id": options.run_task.id}}
                },
            }
        }

        if options.stage is not None:
            body["data"]["attributes"]["stage"] = options.stage
        if options.stages is not None:
            body["data"]["attributes"]["stages"] = options.stages

        path = f"/api/v2/workspaces/{quote(workspace_id)}/tasks"
        response = self.t.request("POST", path, json_body=body)
        return _workspace_run_task_from(response.json()["data"])

    def list(
        self,
        workspace_id: str,
        options: WorkspaceRunTaskListOptions | None = None,
    ) -> Iterator[WorkspaceRunTask]:
        """List all workspace run tasks for a workspace."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        path = f"/api/v2/workspaces/{quote(workspace_id)}/tasks"
        for item in self._list(path, params=params):
            yield _workspace_run_task_from(item)

    def read(self, workspace_id: str, workspace_task_id: str) -> WorkspaceRunTask:
        """Read a workspace run task by ID."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if not valid_string_id(workspace_task_id):
            raise InvalidWorkspaceRunTaskIDError()

        path = (
            f"/api/v2/workspaces/{quote(workspace_id)}/tasks/{quote(workspace_task_id)}"
        )
        response = self.t.request("GET", path)
        return _workspace_run_task_from(response.json()["data"])

    def update(
        self,
        workspace_id: str,
        workspace_task_id: str,
        options: WorkspaceRunTaskUpdateOptions,
    ) -> WorkspaceRunTask:
        """Update a workspace run task by ID."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if not valid_string_id(workspace_task_id):
            raise InvalidWorkspaceRunTaskIDError()

        attributes = options.model_dump(
            by_alias=True, exclude_none=True, exclude={"type"}
        )
        body: dict[str, Any] = {
            "data": {
                "type": "workspace-tasks",
                "id": workspace_task_id,
                "attributes": attributes,
            }
        }

        path = (
            f"/api/v2/workspaces/{quote(workspace_id)}/tasks/{quote(workspace_task_id)}"
        )
        response = self.t.request("PATCH", path, json_body=body)
        return _workspace_run_task_from(response.json()["data"])

    def delete(self, workspace_id: str, workspace_task_id: str) -> None:
        """Delete a workspace run task by ID."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if not valid_string_id(workspace_task_id):
            raise InvalidWorkspaceRunTaskIDError()

        path = (
            f"/api/v2/workspaces/{quote(workspace_id)}/tasks/{quote(workspace_task_id)}"
        )
        self.t.request("DELETE", path)


def _validate_run_task_id(run_task_id: str) -> None:
    """Backward-compatible helper for direct ID validation usage in tests/callers."""
    if not valid_string_id(run_task_id):
        raise InvalidRunTaskIDError()
