from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidOrgError,
    InvalidRunTaskCategoryError,
    InvalidRunTaskIDError,
    InvalidRunTaskURLError,
    RequiredNameError,
)
from ..models.agent import AgentPool
from ..models.organization import Organization
from ..models.run_task import (
    GlobalRunTask,
    RunTask,
    RunTaskCreateOptions,
    RunTaskListOptions,
    RunTaskReadOptions,
    RunTaskUpdateOptions,
    Stage,
    TaskEnforcementLevel,
)
from ..models.workspace_run_task import WorkspaceRunTask
from ..utils import valid_string, valid_string_id
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


def _run_task_from(d: dict[str, Any], org: str | None = None) -> RunTask:
    """
    Convert JSON API response data to RunTask object.

    Maps the JSON API format to Python model fields, handling:
    - Basic attributes (id, name, url, etc.)
    - Optional fields (description, hmac_key)
    - Global configuration object
    - Relationships (agent_pool, organization, workspace_run_tasks)
    """
    attr: dict[str, Any] = d.get("attributes", {}) or {}
    relationships: dict[str, Any] = d.get("relationships", {}) or {}

    id_str: str = _safe_str(d.get("id"))
    name_str: str = _safe_str(attr.get("name"))

    # Handle global configuration if present
    global_config = None
    raw_global = attr.get("global-configuration")
    if raw_global and isinstance(raw_global, dict):
        # Check if enabled exists - if not, no global config
        if "enabled" in raw_global and isinstance(raw_global["enabled"], bool):
            stages = []
            if "stages" in raw_global and isinstance(raw_global["stages"], list):
                stages = [
                    Stage(stage)
                    for stage in raw_global["stages"]
                    if isinstance(stage, str)
                ]

            enforcement_level = TaskEnforcementLevel.ADVISORY  # Default value
            if "enforcement-level" in raw_global and isinstance(
                raw_global["enforcement-level"], str
            ):
                try:
                    enforcement_level = TaskEnforcementLevel(
                        raw_global["enforcement-level"]
                    )
                except ValueError:
                    # If invalid enforcement level, use default
                    enforcement_level = TaskEnforcementLevel.ADVISORY

            global_config = GlobalRunTask(
                enabled=raw_global["enabled"],
                stages=stages,
                enforcement_level=enforcement_level,
            )

    # Handle agent pool relationship
    agent_pool = None
    agent_pool_data = relationships.get("agent-pool", {}).get("data")
    if agent_pool_data and isinstance(agent_pool_data, dict):
        # Create minimal AgentPool object from relationship data
        agent_pool = AgentPool(id=_safe_str(agent_pool_data.get("id")))

    # Handle organization relationship
    organization = None
    org_data = relationships.get("organization", {}).get("data")
    if org_data and isinstance(org_data, dict):
        # Create minimal Organization object from relationship data
        organization = Organization(
            id=_safe_str(org_data.get("id")),
            name=org or None,  # Use org parameter or None
            email=None,  # Not available in relationship data
        )

    # Handle workspace run tasks relationship
    workspace_run_tasks = []
    wrt_data = relationships.get("workspace-tasks", {}).get("data", [])
    if isinstance(wrt_data, list):
        # Note: Full WorkspaceRunTask objects would need to be fetched separately
        # Here we just create minimal objects with IDs
        for item in wrt_data:
            if isinstance(item, dict) and "id" in item:
                workspace_run_tasks.append(
                    WorkspaceRunTask(id=_safe_str(item.get("id")))
                )

    return RunTask(
        id=id_str,
        name=name_str,
        description=_safe_str(attr.get("description")) or None,
        url=_safe_str(attr.get("url")),
        category=_safe_str(attr.get("category")),
        hmac_key=attr.get("hmac-key"),  # Can be None
        enabled=bool(attr.get("enabled")),
        global_configuration=global_config,
        agent_pool=agent_pool,
        organization=organization,
        workspace_run_tasks=workspace_run_tasks,
    )


class RunTasks(_Service):
    def list(
        self, organization_id: str, options: RunTaskListOptions | None = None
    ) -> Iterator[RunTask]:
        if not valid_string_id(organization_id):
            raise InvalidOrgError()

        if options is None:
            options = RunTaskListOptions()

        params: dict[str, str] = {}
        if options.page_size is not None:
            params["page[size]"] = str(options.page_size)
        if options.page_number is not None:
            params["page[number]"] = str(options.page_number)
        if options.include:
            params["include"] = ",".join(options.include)

        path = f"/api/v2/organizations/{organization_id}/tasks"
        for item in self._list(path, params=params):
            yield _run_task_from(item, organization_id)

    def create(self, organization_id: str, options: RunTaskCreateOptions) -> RunTask:
        if not valid_string_id(organization_id):
            raise InvalidOrgError()
        if not valid_string(options.name):
            raise RequiredNameError()
        if not valid_string(options.url):
            raise InvalidRunTaskURLError()
        if options.category != "task":
            raise InvalidRunTaskCategoryError("Invalid run task category; must be task")
        body: dict[str, Any] = {
            "data": {
                "type": "tasks",
                "attributes": {
                    "name": options.name,
                    "url": options.url,
                    "category": options.category,
                    "description": options.description or "",
                },
            },
        }
        if options.hmac_key is not None:
            body["data"]["attributes"]["hmac_key"] = options.hmac_key
        if options.enabled is not None:
            body["data"]["attributes"]["enabled"] = options.enabled
        if options.global_configuration is not None:
            gc = options.global_configuration
            gc_dict: dict[str, Any] = {}
            if gc.enabled is not None:
                gc_dict["enabled"] = gc.enabled
            if gc.stages is not None:
                gc_dict["stages"] = [stage.value for stage in gc.stages]
            if gc.enforcement_level is not None:
                gc_dict["enforcement-level"] = gc.enforcement_level.value
            body["data"]["attributes"]["global-configuration"] = gc_dict
        if options.agent_pool is not None and options.agent_pool.id:
            body["data"]["relationships"] = {
                "agent_pool": {
                    "data": {"type": "agent_pools", "id": options.agent_pool.id}
                }
            }

        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization_id}/tasks",
            json_body=body,
        )
        return _run_task_from(r.json()["data"], organization_id)

    def read(self, run_task_id: str) -> RunTask:
        return self.read_with_options(run_task_id, RunTaskReadOptions())

    def read_with_options(
        self, run_task_id: str, options: RunTaskReadOptions
    ) -> RunTask:
        if not valid_string_id(run_task_id):
            raise InvalidRunTaskIDError()
        params: dict[str, str] = {}
        if options.include:
            params["include"] = ",".join(options.include)

        path = f"/api/v2/tasks/{run_task_id}"
        r = self.t.request("GET", path, params=params)
        return _run_task_from(r.json()["data"])

    def update(self, run_task_id: str, options: RunTaskUpdateOptions) -> RunTask:
        if not valid_string_id(run_task_id):
            raise InvalidRunTaskIDError("Invalid run task ID")
        if options.name is not None and not valid_string(options.name):
            raise RequiredNameError()
        if options.url is not None and not valid_string(options.url):
            raise InvalidRunTaskURLError()
        if options.category is not None and options.category != "task":
            raise InvalidRunTaskCategoryError("Invalid run task category; must be task")
        body: dict[str, Any] = {
            "data": {"type": "tasks", "id": run_task_id, "attributes": {}}
        }
        if options.name is not None:
            body["data"]["attributes"]["name"] = options.name
        if options.url is not None:
            body["data"]["attributes"]["url"] = options.url
        if options.category is not None:
            body["data"]["attributes"]["category"] = options.category
        if options.description is not None:
            body["data"]["attributes"]["description"] = options.description
        if options.hmac_key is not None:
            body["data"]["attributes"]["hmac_key"] = options.hmac_key
        if options.enabled is not None:
            body["data"]["attributes"]["enabled"] = options.enabled
        if options.global_configuration is not None:
            gc = options.global_configuration
            gc_dict: dict[str, Any] = {}
            if gc.enabled is not None:
                gc_dict["enabled"] = gc.enabled
            if gc.stages is not None:
                gc_dict["stages"] = [stage.value for stage in gc.stages]
            if gc.enforcement_level is not None:
                gc_dict["enforcement-level"] = gc.enforcement_level.value
            body["data"]["attributes"]["global-configuration"] = gc_dict
        if options.agent_pool is not None:
            body["data"].setdefault("relationships", {})
            if options.agent_pool.id:
                body["data"]["relationships"]["agent_pool"] = {
                    "data": {"type": "agent_pools", "id": options.agent_pool.id}
                }
            else:
                body["data"]["relationships"]["agent_pool"] = {"data": None}
        r = self.t.request(
            "PATCH",
            f"/api/v2/tasks/{run_task_id}",
            json_body=body,
        )
        return _run_task_from(r.json()["data"])

    def delete(self, run_task_id: str) -> None:
        if not valid_string_id(run_task_id):
            raise InvalidRunTaskIDError()
        self.t.request("DELETE", f"/api/v2/tasks/{run_task_id}")

    def attach_to_workspace(
        self,
        workspace_id: str,
        run_task_id: str,
        enforcement_level: TaskEnforcementLevel,
    ) -> WorkspaceRunTask:
        """
        Attach a run task to a workspace.

        This is a convenience method that creates a workspace run task relationship.
        """
        # This would typically delegate to workspace_run_tasks.create()
        # For now, we'll create a placeholder implementation
        # In a real implementation, this would call:
        """
        create_options = WorkspaceRunTaskCreateOptions(
            enforcement_level=enforcement_level,
            run_task=RunTask(id=run_task_id, name="", url="", category="task", enabled=True)
        )
        return workspace_run_tasks.create(workspace_id, create_options)
        """

        # TODO: Implement actual workspace run task creation
        raise NotImplementedError("attach_to_workspace method needs to be implemented")
