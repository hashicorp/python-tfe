# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import quote

from .._jsonapi import attach_jsonapi
from ..errors import (
    InvalidWorkspaceIDError,
    InvalidWorkspaceRunTaskIDError,
)
from ..models.run_task import RunTask
from ..models.workspace import Workspace
from ..models.workspace_run_task import (
    WorkspaceRunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskUpdateOptions,
)
from ..utils import _safe_str, valid_string_id
from ._base import _Service


def _workspace_run_task_from(data: dict[str, Any]) -> WorkspaceRunTask:
    """Convert API response data to WorkspaceRunTask model."""
    attributes = data.get("attributes", {})
    relationships = data.get("relationships", {})
    attributes["id"] = data.get("id")

    run_task_data = relationships.get("task", {}).get("data")
    if isinstance(run_task_data, dict) and run_task_data.get("id"):
        attributes["run_task"] = RunTask.model_construct(
            id=_safe_str(run_task_data.get("id"))
        )
    workspace_data = relationships.get("workspace", {}).get("data")
    if isinstance(workspace_data, dict) and workspace_data.get("id"):
        attributes["workspace"] = Workspace.model_construct(
            id=_safe_str(workspace_data.get("id"))
        )

    return attach_jsonapi(WorkspaceRunTask.model_validate(attributes), data)


class WorkspaceRunTasks(_Service):
    """Workspace run tasks service."""

    def create(
        self, workspace_id: str, options: WorkspaceRunTaskCreateOptions
    ) -> WorkspaceRunTask:
        """Attach a run task to a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: The workspace run task settings, as a
                :class:`WorkspaceRunTaskCreateOptions`.

        Returns:
            The created :class:`WorkspaceRunTask`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunTask, WorkspaceRunTaskCreateOptions
            >>> options = WorkspaceRunTaskCreateOptions(
            ...     enforcement_level="advisory",
            ...     run_task=RunTask.model_construct(id="task-123"),
            ... )
            >>> task = client.workspace_run_tasks.create("ws-123", options)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

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
        """List run tasks attached to a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Optional pagination options, as a
                :class:`WorkspaceRunTaskListOptions`.

        Returns:
            A single-use ``Iterator[WorkspaceRunTask]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for task in client.workspace_run_tasks.list("ws-123"):
            ...     print(task.id, task.enforcement_level)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        path = f"/api/v2/workspaces/{quote(workspace_id)}/tasks"
        for item in self._list(path, params=params):
            yield _workspace_run_task_from(item)

    def read(self, workspace_id: str, workspace_task_id: str) -> WorkspaceRunTask:
        """Read a workspace run task by its ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            workspace_task_id: The workspace run task ID (e.g. ``"wst-xxxxxxxx"``).

        Returns:
            The :class:`WorkspaceRunTask`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            InvalidWorkspaceRunTaskIDError: If ``workspace_task_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> task = client.workspace_run_tasks.read("ws-123", "wst-1")
            >>> print(task.stages)
        """
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
        """Update a workspace run task by its ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            workspace_task_id: The workspace run task ID (e.g. ``"wst-xxxxxxxx"``).
            options: The workspace run task updates, as a
                :class:`WorkspaceRunTaskUpdateOptions`.

        Returns:
            The updated :class:`WorkspaceRunTask`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            InvalidWorkspaceRunTaskIDError: If ``workspace_task_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceRunTaskUpdateOptions
            >>> task = client.workspace_run_tasks.update(
            ...     "ws-123",
            ...     "wst-1",
            ...     WorkspaceRunTaskUpdateOptions(enforcement_level="mandatory"),
            ... )
        """
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
        """Delete a workspace run task by its ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            workspace_task_id: The workspace run task ID (e.g. ``"wst-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            InvalidWorkspaceRunTaskIDError: If ``workspace_task_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> client.workspace_run_tasks.delete("ws-123", "wst-1")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if not valid_string_id(workspace_task_id):
            raise InvalidWorkspaceRunTaskIDError()

        path = (
            f"/api/v2/workspaces/{quote(workspace_id)}/tasks/{quote(workspace_task_id)}"
        )
        self.t.request("DELETE", path)
