"""Agent Pool resource implementation for the Python TFE SDK.

This module provides the AgentPools service for managing Terraform Enterprise/Cloud
agent pools, including CRUD operations and workspace assignments.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

from ..models.agent import (
    AgentPool,
    AgentPoolAllowedWorkspacePolicy,
    AgentPoolAssignToWorkspacesOptions,
    AgentPoolCreateOptions,
    AgentPoolListOptions,
    AgentPoolReadOptions,
    AgentPoolRemoveFromWorkspacesOptions,
    AgentPoolUpdateOptions,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service


def valid_agent_pool_name(name: str) -> bool:
    """Validate agent pool name format."""
    if not valid_string(name):
        return False
    # Agent pool names must be between 1 and 90 characters
    # and can contain letters, numbers, spaces, hyphens, and underscores
    if len(name) > 90:
        return False
    return True


def validate_agent_pool_create_options(organization: str, name: str) -> None:
    """Validate agent pool creation parameters."""
    if not valid_string(organization):
        raise ValueError("Organization name is required and must be valid")

    if not valid_string(name):
        raise ValueError("Agent pool name is required")

    if not valid_agent_pool_name(name):
        raise ValueError("Agent pool name contains invalid characters or is too long")


def validate_agent_pool_update_options(
    agent_pool_id: str, name: str | None = None
) -> None:
    """Validate agent pool update parameters."""
    if not valid_string_id(agent_pool_id):
        raise ValueError("Agent pool ID is required and must be valid")

    if name is not None:
        if not valid_string(name):
            raise ValueError("Agent pool name must be a valid string")
        if not valid_agent_pool_name(name):
            raise ValueError(
                "Agent pool name contains invalid characters or is too long"
            )


def _safe_str(value: Any, default: str = "") -> str:
    """Safely convert a value to string with optional default."""
    if value is None:
        return default
    return str(value)


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to an integer."""
    if value is None:
        return default
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_bool(value: Any) -> bool | None:
    """Safely convert a value to a boolean."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def _safe_workspace_policy(value: Any) -> AgentPoolAllowedWorkspacePolicy | None:
    """Safely convert a value to an AgentPoolAllowedWorkspacePolicy enum."""
    if value is None:
        return None
    if isinstance(value, AgentPoolAllowedWorkspacePolicy):
        return value
    try:
        return AgentPoolAllowedWorkspacePolicy(str(value))
    except (ValueError, TypeError):
        return None


class AgentPools(_Service):
    """Agent Pools service for managing Terraform Enterprise agent pools."""

    def list(
        self, organization: str, options: AgentPoolListOptions | None = None
    ) -> Iterator[AgentPool]:
        """List agent pools in an organization.

        Args:
            organization: Organization name
            options: Optional parameters for filtering and pagination

        Returns:
            Iterator of AgentPool objects

        Raises:
            ValueError: If organization name is invalid
            TFEError: If API request fails
        """
        if not valid_string(organization):
            raise ValueError("Organization name is required and must be valid")

        path = f"/api/v2/organizations/{organization}/agent-pools"
        params: dict[str, str | int] = {}

        if options:
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.include:
                params["include"] = ",".join(options.include)
            if options.allowed_workspace_policy:
                params["filter[allowed_workspace_policy]"] = (
                    options.allowed_workspace_policy.value
                )

        items_iter = self._list(path, params=params)

        for item in items_iter:
            # Extract agent pool data from API response
            attr = item.get("attributes", {}) or {}
            relationships = item.get("relationships", {}) or {}

            # Note: organization and workspace relationships available but not currently used

            # Extract agents from relationships
            agents_data = relationships.get("agents", {}).get("data", [])
            agent_count = (
                len(agents_data) if agents_data else attr.get("agent-count", 0)
            )

            agent_pool_data = {
                "id": _safe_str(item.get("id")),
                "name": _safe_str(attr.get("name")),
                "created_at": attr.get("created-at"),
                "organization_scoped": attr.get("organization-scoped"),
                "allowed_workspace_policy": attr.get("allowed-workspace-policy"),
                "agent_count": agent_count,
            }

            yield AgentPool(
                id=_safe_str(agent_pool_data["id"]) or "",
                name=_safe_str(agent_pool_data["name"]),
                created_at=cast(Any, agent_pool_data["created_at"]),
                organization_scoped=_safe_bool(agent_pool_data["organization_scoped"]),
                allowed_workspace_policy=_safe_workspace_policy(
                    agent_pool_data["allowed_workspace_policy"]
                ),
                agent_count=_safe_int(agent_pool_data["agent_count"]),
            )

    def create(self, organization: str, options: AgentPoolCreateOptions) -> AgentPool:
        """Create a new agent pool in an organization.

        Args:
            organization: Organization name
            options: Agent pool creation options

        Returns:
            Created AgentPool object

        Raises:
            ValueError: If parameters are invalid
            TFEError: If API request fails
        """
        validate_agent_pool_create_options(organization, options.name)

        path = f"/api/v2/organizations/{organization}/agent-pools"
        attributes: dict[str, Any] = {"name": options.name}

        if options.organization_scoped is not None:
            attributes["organization-scoped"] = options.organization_scoped

        if options.allowed_workspace_policy is not None:
            attributes["allowed-workspace-policy"] = (
                options.allowed_workspace_policy.value
            )

        payload = {"data": {"type": "agent-pools", "attributes": attributes}}

        response = self.t.request("POST", path, json_body=payload)
        data = response.json()["data"]

        # Extract agent pool data from response
        attr = data.get("attributes", {}) or {}
        agent_pool_data = {
            "id": _safe_str(data.get("id")),
            "name": _safe_str(attr.get("name")),
            "created_at": attr.get("created-at"),
            "organization_scoped": attr.get("organization-scoped"),
            "allowed_workspace_policy": attr.get("allowed-workspace-policy"),
            "agent_count": attr.get("agent-count", 0),
        }

        return AgentPool(
            id=_safe_str(agent_pool_data["id"]) or "",
            name=_safe_str(agent_pool_data["name"]),
            created_at=cast(Any, agent_pool_data["created_at"]),
            organization_scoped=_safe_bool(agent_pool_data["organization_scoped"]),
            allowed_workspace_policy=_safe_workspace_policy(
                agent_pool_data["allowed_workspace_policy"]
            ),
            agent_count=_safe_int(agent_pool_data["agent_count"]),
        )

    def read(
        self, agent_pool_id: str, options: AgentPoolReadOptions | None = None
    ) -> AgentPool:
        """Get a specific agent pool by ID.

        Args:
            agent_pool_id: Agent pool ID
            options: Optional parameters for including related resources

        Returns:
            AgentPool object

        Raises:
            ValueError: If agent_pool_id is invalid
            TFEError: If API request fails
        """
        if not valid_string_id(agent_pool_id):
            raise ValueError("Agent pool ID is required and must be valid")

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        params: dict[str, str] = {}

        if options and options.include:
            params["include"] = ",".join(options.include)

        if params:
            response = self.t.request("GET", path, params=params)
        else:
            response = self.t.request("GET", path)

        data = response.json()["data"]

        # Extract agent pool data from response
        attr = data.get("attributes", {}) or {}
        relationships = data.get("relationships", {}) or {}

        # Extract agents count
        agents_data = relationships.get("agents", {}).get("data", [])
        agent_count = len(agents_data) if agents_data else attr.get("agent-count", 0)

        agent_pool_data = {
            "id": _safe_str(data.get("id")),
            "name": _safe_str(attr.get("name")),
            "created_at": attr.get("created-at"),
            "organization_scoped": attr.get("organization-scoped"),
            "allowed_workspace_policy": attr.get("allowed-workspace-policy"),
            "agent_count": agent_count,
        }

        return AgentPool(
            id=_safe_str(agent_pool_data["id"]) or "",
            name=_safe_str(agent_pool_data["name"]),
            created_at=cast(Any, agent_pool_data["created_at"]),
            organization_scoped=_safe_bool(agent_pool_data["organization_scoped"]),
            allowed_workspace_policy=_safe_workspace_policy(
                agent_pool_data["allowed_workspace_policy"]
            ),
            agent_count=_safe_int(agent_pool_data["agent_count"]),
        )

    def update(self, agent_pool_id: str, options: AgentPoolUpdateOptions) -> AgentPool:
        """Update an agent pool's properties.

        Args:
            agent_pool_id: Agent pool ID
            options: Agent pool update options

        Returns:
            Updated AgentPool object

        Raises:
            ValueError: If parameters are invalid
            TFEError: If API request fails
        """
        validate_agent_pool_update_options(agent_pool_id, options.name)

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        attributes: dict[str, Any] = {}

        if options.name is not None:
            attributes["name"] = options.name

        if options.organization_scoped is not None:
            attributes["organization-scoped"] = options.organization_scoped

        if options.allowed_workspace_policy is not None:
            attributes["allowed-workspace-policy"] = (
                options.allowed_workspace_policy.value
            )

        payload = {
            "data": {
                "type": "agent-pools",
                "id": agent_pool_id,
                "attributes": attributes,
            }
        }

        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]

        # Extract agent pool data from response
        attr = data.get("attributes", {}) or {}
        agent_pool_data = {
            "id": _safe_str(data.get("id")),
            "name": _safe_str(attr.get("name")),
            "created_at": attr.get("created-at"),
            "organization_scoped": attr.get("organization-scoped"),
            "allowed_workspace_policy": attr.get("allowed-workspace-policy"),
            "agent_count": attr.get("agent-count", 0),
        }

        return AgentPool(
            id=_safe_str(agent_pool_data["id"]) or "",
            name=_safe_str(agent_pool_data["name"]),
            created_at=cast(Any, agent_pool_data["created_at"]),
            organization_scoped=_safe_bool(agent_pool_data["organization_scoped"]),
            allowed_workspace_policy=_safe_workspace_policy(
                agent_pool_data["allowed_workspace_policy"]
            ),
            agent_count=_safe_int(agent_pool_data["agent_count"]),
        )

    def delete(self, agent_pool_id: str) -> None:
        """Delete an agent pool.

        Args:
            agent_pool_id: Agent pool ID

        Raises:
            ValueError: If agent_pool_id is invalid
            TFEError: If API request fails
        """
        if not valid_string_id(agent_pool_id):
            raise ValueError("Agent pool ID is required and must be valid")

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        self.t.request("DELETE", path)

    def assign_to_workspaces(
        self, agent_pool_id: str, options: AgentPoolAssignToWorkspacesOptions
    ) -> None:
        """Assign an agent pool to workspaces.

        Args:
            agent_pool_id: Agent pool ID
            options: Assignment options containing workspace IDs

        Raises:
            ValueError: If parameters are invalid
            TFEError: If API request fails
        """
        if not valid_string_id(agent_pool_id):
            raise ValueError("Agent pool ID is required and must be valid")

        if not options.workspace_ids:
            raise ValueError("At least one workspace ID is required")

        path = f"/api/v2/agent-pools/{agent_pool_id}/relationships/workspaces"

        # Create data payload with workspace references
        workspace_data = []
        for workspace_id in options.workspace_ids:
            if not valid_string_id(workspace_id):
                raise ValueError(f"Invalid workspace ID: {workspace_id}")
            workspace_data.append({"type": "workspaces", "id": workspace_id})

        payload = {"data": workspace_data}
        self.t.request("POST", path, json_body=payload)

    def remove_from_workspaces(
        self, agent_pool_id: str, options: AgentPoolRemoveFromWorkspacesOptions
    ) -> None:
        """Remove an agent pool from workspaces.

        Args:
            agent_pool_id: Agent pool ID
            options: Removal options containing workspace IDs

        Raises:
            ValueError: If parameters are invalid
            TFEError: If API request fails
        """
        if not valid_string_id(agent_pool_id):
            raise ValueError("Agent pool ID is required and must be valid")

        if not options.workspace_ids:
            raise ValueError("At least one workspace ID is required")

        path = f"/api/v2/agent-pools/{agent_pool_id}/relationships/workspaces"

        # Create data payload with workspace references
        workspace_data = []
        for workspace_id in options.workspace_ids:
            if not valid_string_id(workspace_id):
                raise ValueError(f"Invalid workspace ID: {workspace_id}")
            workspace_data.append({"type": "workspaces", "id": workspace_id})

        payload = {"data": workspace_data}
        self.t.request("DELETE", path, json_body=payload)
