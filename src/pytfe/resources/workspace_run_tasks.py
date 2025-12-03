from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidWorkspaceIDError,
    InvalidWorkspaceRunTaskIDError,
)
from pytfe.models import (
    RunTask,
    Stage,
    TaskEnforcementLevel,
    Workspace,
    WorkspaceRunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskReadOptions,
    WorkspaceRunTaskUpdateOptions,
)
from ..utils import _safe_str, valid_string_id
from ._base import _Service


def _workspace_run_task_from(d: dict[str, Any]) -> WorkspaceRunTask:
    """
    Convert JSON API response data to WorkspaceRunTask object.

    Maps the JSON API format to Python model fields, handling:
    - Basic attributes (id, enforcement_level, stage, timestamps)
    - Relationships (workspace, run_task)
    """
    attr: dict[str, Any] = d.get("attributes", {}) or {}
    relationships: dict[str, Any] = d.get("relationships", {}) or {}

    id_str: str = _safe_str(d.get("id"))
    type_str: str = _safe_str(d.get("type", "workspace-tasks"))

    # Extract enforcement level and stage
    enforcement_level_str = attr.get("enforcement-level")
    stage_str = attr.get("stage")

    # Convert to enum values
    enforcement_level = TaskEnforcementLevel.ADVISORY  # Default
    if isinstance(enforcement_level_str, str):
        try:
            enforcement_level = TaskEnforcementLevel(enforcement_level_str)
        except ValueError:
            enforcement_level = TaskEnforcementLevel.ADVISORY

    stage = Stage.POST_PLAN  # Default
    if isinstance(stage_str, str):
        try:
            # API returns kebab-case (pre-plan, post-plan, etc.)
            stage = Stage(stage_str)
        except ValueError:
            stage = Stage.POST_PLAN

    # Handle timestamps
    created_at = attr.get("created-at")
    updated_at = attr.get("updated-at")

    # Handle relationships
    workspace_data = relationships.get("workspace", {}).get("data")
    run_task_data = relationships.get("task", {}).get("data")

    workspace = None
    if workspace_data and isinstance(workspace_data, dict):
        workspace = Workspace(id=_safe_str(workspace_data.get("id")))

    run_task = None
    if run_task_data and isinstance(run_task_data, dict):
        run_task = RunTask(
            id=_safe_str(run_task_data.get("id")),
            name="",  # Will be populated when included in API response
            description=None,
            url="",  # Will be populated when included
            category="",  # Will be populated when included
            hmac_key=None,
            enabled=True,
        )

    return WorkspaceRunTask(
        id=id_str,
        type=type_str,
        enforcement_level=enforcement_level,
        stage=stage,
        created_at=created_at,
        updated_at=updated_at,
        workspace=workspace,
        run_task=run_task,
    )


class WorkspaceRunTasksService(_Service):
    """Service for managing workspace run tasks."""

    def list(
        self,
        workspace_id: str,
        *,
        options: WorkspaceRunTaskListOptions | None = None,
    ) -> Iterator[WorkspaceRunTask]:
        """
        List workspace run tasks.

        Args:
            workspace_id: The workspace ID to list run tasks for
            options: Optional list options for pagination and includes

        Yields:
            WorkspaceRunTask objects

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError(workspace_id)

        url = f"/api/v2/workspaces/{workspace_id}/tasks"

        params: dict[str, Any] = {}

        if options:
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])

        # Use the list method from base service
        for item in self._list(url, params=params):
            yield _workspace_run_task_from(item)

    def get(
        self,
        workspace_id: str,
        task_id: str,
        *,
        options: WorkspaceRunTaskReadOptions | None = None,
    ) -> WorkspaceRunTask:
        """
        Get a specific workspace run task.

        Args:
            workspace_id: The workspace ID
            task_id: The workspace run task ID
            options: Optional read options for includes

        Returns:
            The WorkspaceRunTask object

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
            InvalidWorkspaceRunTaskIDError: If task_id is invalid
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError(workspace_id)
        if not valid_string_id(task_id):
            raise InvalidWorkspaceRunTaskIDError(task_id)

        url = f"/api/v2/workspaces/{workspace_id}/tasks/{task_id}"

        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", url, params=params)
        json_response = response.json() or {}
        return _workspace_run_task_from(json_response["data"])

    def create(
        self,
        workspace_id: str,
        options: WorkspaceRunTaskCreateOptions,
    ) -> WorkspaceRunTask:
        """
        Create a new workspace run task.

        Args:
            workspace_id: The workspace ID
            options: Create options

        Returns:
            The created WorkspaceRunTask

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError(workspace_id)

        url = f"/api/v2/workspaces/{workspace_id}/tasks"

        # Build the request payload
        data: dict[str, Any] = {
            "data": {
                "type": options.type,
                "attributes": {
                    "enforcement-level": options.enforcement_level.value,
                },
                "relationships": {"task": options.run_task},
            }
        }

        # Add optional stages if provided (stages is the recommended approach)
        if options.stages is not None:
            data["data"]["attributes"]["stages"] = [s.value for s in options.stages]

        response = self.t.request("POST", url, json_body=data)

        # API returns 204 No Content on success
        if response.status_code == 204:
            # Try to parse response body if present, otherwise list tasks to get the created one
            try:
                json_response = response.json()
                if json_response and "data" in json_response:
                    return _workspace_run_task_from(json_response["data"])
            except Exception:
                pass
            # If no response body, list tasks to find the newly created one
            for task in self.list(workspace_id):
                # Return the most recently created task (should be first after sorting)
                return task
            raise ValueError("Could not parse workspace run task creation response")

        json_response = response.json() or {}
        return _workspace_run_task_from(json_response["data"])

    def update(
        self,
        workspace_id: str,
        task_id: str,
        options: WorkspaceRunTaskUpdateOptions,
    ) -> WorkspaceRunTask:
        """
        Update a workspace run task.

        Args:
            workspace_id: The workspace ID
            task_id: The workspace run task ID
            options: Update options

        Returns:
            The updated WorkspaceRunTask

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
            InvalidWorkspaceRunTaskIDError: If task_id is invalid
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError(workspace_id)
        if not valid_string_id(task_id):
            raise InvalidWorkspaceRunTaskIDError(task_id)

        url = f"/api/v2/workspaces/{workspace_id}/tasks/{task_id}"

        # Build the request payload
        data: dict[str, Any] = {
            "data": {"type": options.type, "id": task_id, "attributes": {}}
        }

        # Add optional fields if provided - convert underscore to kebab-case for API
        if options.enforcement_level is not None:
            data["data"]["attributes"]["enforcement-level"] = (
                options.enforcement_level.value
            )
        if options.stage is not None:
            data["data"]["attributes"]["stage"] = options.stage.value
        if options.stages is not None:
            data["data"]["attributes"]["stages"] = [
                stage.value for stage in options.stages
            ]

        response = self.t.request("PATCH", url, json_body=data)
        json_response = response.json() or {}
        return _workspace_run_task_from(json_response["data"])

    def delete(
        self,
        workspace_id: str,
        task_id: str,
    ) -> None:
        """
        Delete a workspace run task.

        Args:
            workspace_id: The workspace ID
            task_id: The workspace run task ID

        Raises:
            InvalidWorkspaceIDError: If workspace_id is invalid
            InvalidWorkspaceRunTaskIDError: If task_id is invalid
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError(workspace_id)
        if not valid_string_id(task_id):
            raise InvalidWorkspaceRunTaskIDError(task_id)

        url = f"/api/v2/workspaces/{workspace_id}/tasks/{task_id}"
        self.t.request("DELETE", url)
