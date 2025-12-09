from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidRunTaskIDError,
    InvalidWorkspaceIDError,
    InvalidWorkspaceRunTaskIDError,
)
from ..models.run_task import RunTask, Stage, TaskEnforcementLevel
from ..models.workspace_run_task import (
    WorkspaceRunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskUpdateOptions,
)
from ..utils import _safe_str, valid_string_id
from ._base import _Service


def _workspace_run_task_from(d: dict[str, Any]) -> WorkspaceRunTask:
    """
    Convert JSON API response data to WorkspaceRunTask object.

    Maps the JSON API format to Python model fields, handling:
    - Basic attributes (id, enforcement_level, stage, stages)
    - Relationships (run_task, workspace)
    """
    attr: dict[str, Any] = d.get("attributes", {}) or {}
    relationships: dict[str, Any] = d.get("relationships", {}) or {}

    id_str: str = _safe_str(d.get("id"))

    # Parse enforcement level
    enforcement_level = TaskEnforcementLevel.ADVISORY  # Default
    if "enforcement-level" in attr:
        try:
            enforcement_level = TaskEnforcementLevel(attr["enforcement-level"])
        except ValueError:
            enforcement_level = TaskEnforcementLevel.ADVISORY

    # Parse stage (deprecated)
    stage = Stage.PRE_PLAN  # Default
    if "stage" in attr:
        try:
            stage = Stage(attr["stage"])
        except ValueError:
            stage = Stage.PRE_PLAN

    # Parse stages list
    stages = []
    if "stages" in attr and isinstance(attr["stages"], list):
        for stage_str in attr["stages"]:
            if isinstance(stage_str, str):
                try:
                    stages.append(Stage(stage_str))
                except ValueError:
                    pass  # Skip invalid stages

    # Handle run_task relationship
    run_task = None
    run_task_data = relationships.get("task", {}).get("data")
    if run_task_data and isinstance(run_task_data, dict):
        run_task = RunTask(
            id=_safe_str(run_task_data.get("id")),
            name="",  # Name not available in relationship data
            url="",  # URL not available in relationship data
            category="task",
            enabled=True,
        )

    # Handle workspace relationship
    workspace = None
    workspace_data = relationships.get("workspace", {}).get("data")
    if workspace_data and isinstance(workspace_data, dict):
        from ..models.workspace import Workspace

        workspace = Workspace(
            id=_safe_str(workspace_data.get("id")),
            name="",  # Name not available in relationship data
        )

    return WorkspaceRunTask(
        id=id_str,
        enforcement_level=enforcement_level,
        stage=stage,
        stages=stages,
        run_task=run_task,
        workspace=workspace,
    )


class WorkspaceRunTasks(_Service):
    """
    Workspace Run Tasks service for managing run tasks attached to workspaces.

    API Documentation:
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspace-run-tasks
    """

    def list(
        self,
        workspace_id: str,
        options: WorkspaceRunTaskListOptions | None = None,
    ) -> Iterator[WorkspaceRunTask]:
        """
        List all run tasks attached to a workspace.

        Args:
            workspace_id: The ID of the workspace
            options: Optional pagination parameters

        Yields:
            WorkspaceRunTask objects

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid

        API Endpoint:
            GET /workspaces/:workspace_id/tasks
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError("Invalid workspace ID")

        url = f"/api/v2/workspaces/{workspace_id}/tasks"
        params: dict[str, Any] = {}

        if options:
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size

        while True:
            r = self.t.request("GET", url, params=params)
            response: dict[str, Any] = r.json()

            # Parse data array
            data_list = response.get("data", [])
            if not isinstance(data_list, list):
                break

            for item in data_list:
                yield _workspace_run_task_from(item)

            # Check for next page
            links = response.get("links", {})
            next_url = links.get("next")
            if not next_url:
                break

            # Update URL for next page
            url = next_url
            params = {}

    def read(self, workspace_id: str, workspace_task_id: str) -> WorkspaceRunTask:
        """
        Read a workspace run task by ID.

        Args:
            workspace_id: The ID of the workspace
            workspace_task_id: The ID of the workspace run task

        Returns:
            WorkspaceRunTask object

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
            InvalidWorkspaceRunTaskIDError: If workspace_task_id is invalid

        API Endpoint:
            GET /workspaces/:workspace_id/tasks/:workspace_task_id
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError("Invalid workspace ID")

        if not valid_string_id(workspace_task_id):
            raise InvalidWorkspaceRunTaskIDError("Invalid workspace run task ID")

        url = f"/api/v2/workspaces/{workspace_id}/tasks/{workspace_task_id}"
        r = self.t.request("GET", url)
        response: dict[str, Any] = r.json()

        data = response.get("data", {})
        return _workspace_run_task_from(data)

    def create(
        self,
        workspace_id: str,
        options: WorkspaceRunTaskCreateOptions,
    ) -> WorkspaceRunTask:
        """
        Create a workspace run task (attach a run task to a workspace).

        The run task must exist in the workspace's organization.

        Args:
            workspace_id: The ID of the workspace
            options: Creation options including run_task and enforcement_level

        Returns:
            Created WorkspaceRunTask object

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
            InvalidRunTaskIDError: If run_task ID is invalid

        API Endpoint:
            POST /workspaces/:workspace_id/tasks
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError("Invalid workspace ID")

        if not options.run_task or not options.run_task.id:
            raise InvalidRunTaskIDError("Invalid run task ID")

        url = f"/api/v2/workspaces/{workspace_id}/tasks"

        # Build request payload
        payload: dict[str, Any] = {
            "data": {
                "type": options.type,
                "attributes": {
                    "enforcement-level": options.enforcement_level.value,
                },
                "relationships": {
                    "task": {
                        "data": {
                            "type": "tasks",
                            "id": options.run_task.id,
                        }
                    }
                },
            }
        }

        # Add optional stage (deprecated)
        if options.stage is not None:
            payload["data"]["attributes"]["stage"] = options.stage.value

        # Add optional stages
        if options.stages is not None:
            payload["data"]["attributes"]["stages"] = [s.value for s in options.stages]

        r = self.t.request("POST", url, json_body=payload)
        response: dict[str, Any] = r.json()

        data = response.get("data", {})
        return _workspace_run_task_from(data)

    def update(
        self,
        workspace_id: str,
        workspace_task_id: str,
        options: WorkspaceRunTaskUpdateOptions,
    ) -> WorkspaceRunTask:
        """
        Update an existing workspace run task.

        Args:
            workspace_id: The ID of the workspace
            workspace_task_id: The ID of the workspace run task
            options: Update options (enforcement_level, stage, stages)

        Returns:
            Updated WorkspaceRunTask object

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
            InvalidWorkspaceRunTaskIDError: If workspace_task_id is invalid

        API Endpoint:
            PATCH /workspaces/:workspace_id/tasks/:workspace_task_id
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError("Invalid workspace ID")

        if not valid_string_id(workspace_task_id):
            raise InvalidWorkspaceRunTaskIDError("Invalid workspace run task ID")

        url = f"/api/v2/workspaces/{workspace_id}/tasks/{workspace_task_id}"

        # Build request payload
        payload: dict[str, Any] = {
            "data": {
                "type": options.type,
                "attributes": {},
            }
        }

        # Add optional enforcement level
        if options.enforcement_level is not None:
            payload["data"]["attributes"]["enforcement-level"] = (
                options.enforcement_level.value
            )

        # Add optional stage (deprecated)
        if options.stage is not None:
            payload["data"]["attributes"]["stage"] = options.stage.value

        # Add optional stages
        if options.stages is not None:
            payload["data"]["attributes"]["stages"] = [s.value for s in options.stages]

        r = self.t.request("PATCH", url, json_body=payload)
        response: dict[str, Any] = r.json()

        data = response.get("data", {})
        return _workspace_run_task_from(data)

    def delete(self, workspace_id: str, workspace_task_id: str) -> None:
        """
        Delete a workspace run task by ID.

        Args:
            workspace_id: The ID of the workspace
            workspace_task_id: The ID of the workspace run task

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
            InvalidWorkspaceRunTaskIDError: If workspace_task_id is invalid

        API Endpoint:
            DELETE /workspaces/:workspace_id/tasks/:workspace_task_id
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError("Invalid workspace ID")

        if not valid_string_id(workspace_task_id):
            raise InvalidWorkspaceRunTaskIDError("Invalid workspace run task ID")

        url = f"/api/v2/workspaces/{workspace_id}/tasks/{workspace_task_id}"
        self.t.request("DELETE", url)
