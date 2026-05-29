# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Agent Pool resource implementation for the Python TFE SDK.

This module provides the AgentPools service for managing Terraform Enterprise/Cloud
agent pools, including CRUD operations and workspace assignments.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from pytfe.models.organization import Organization
from pytfe.models.project import Project
from pytfe.models.workspace import Workspace

from .._jsonapi import parse_relationships
from ..errors import (
    InvalidAgentPoolIDError,
    InvalidOrgError,
    InvalidProjectIDError,
    InvalidWorkspaceIDError,
    RequiredProjectError,
    RequiredWorkspaceError,
)
from ..models.agent import (
    Agent,
    AgentPool,
    AgentPoolAssignToProjectsOptions,
    AgentPoolAssignToWorkspacesOptions,
    AgentPoolCreateOptions,
    AgentPoolListOptions,
    AgentPoolReadOptions,
    AgentPoolRemoveFromWorkspacesOptions,
    AgentPoolUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service


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
        if not valid_string_id(organization):
            raise InvalidOrgError()

        path = f"/api/v2/organizations/{organization}/agent-pools"
        params: dict[str, str | int] = {}

        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.include:
                params["include"] = ",".join(options.include)
            if options.query:
                params["q"] = options.query
            if options.allowed_workspace_name:
                params["filter[allowed_workspaces][name]"] = (
                    options.allowed_workspace_name
                )
            if options.allowed_project_name:
                params["filter[allowed_projects][name]"] = options.allowed_project_name
            if options.sort:
                params["sort"] = options.sort
        for item in self._list(path, params=params):
            yield self._parse_agent_pool_from(item)

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
        if not valid_string_id(organization):
            raise InvalidOrgError()

        path = f"/api/v2/organizations/{organization}/agent-pools"
        attributes: dict[str, Any] = {"name": options.name}

        if options.organization_scoped is not None:
            attributes["organization-scoped"] = options.organization_scoped

        relationships: dict[str, Any] = {}
        if options.allowed_workspace_ids:
            relationships["allowed-workspaces"] = {
                "data": [
                    {"type": "workspaces", "id": ws_id}
                    for ws_id in options.allowed_workspace_ids
                ]
            }
        if options.excluded_workspace_ids:
            relationships["excluded-workspaces"] = {
                "data": [
                    {"type": "workspaces", "id": ws_id}
                    for ws_id in options.excluded_workspace_ids
                ]
            }
        if options.allowed_project_ids:
            relationships["allowed-projects"] = {
                "data": [
                    {"type": "projects", "id": proj_id}
                    for proj_id in options.allowed_project_ids
                ]
            }

        payload: dict[str, Any] = {
            "data": {"type": "agent-pools", "attributes": attributes}
        }
        if relationships:
            payload["data"]["relationships"] = relationships

        response = self.t.request("POST", path, json_body=payload)
        data = response.json()["data"]

        return self._parse_agent_pool_from(data)

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
            raise InvalidAgentPoolIDError()

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        params: dict[str, str] = {}

        if options and options.include:
            params["include"] = ",".join(options.include)

        if params:
            response = self.t.request("GET", path, params=params)
        else:
            response = self.t.request("GET", path)

        data = response.json()["data"]

        return self._parse_agent_pool_from(data)

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

        if not valid_string_id(agent_pool_id):
            raise InvalidAgentPoolIDError()

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        attributes: dict[str, Any] = {}

        if options.name is not None:
            attributes["name"] = options.name

        if options.organization_scoped is not None:
            attributes["organization-scoped"] = options.organization_scoped

        relationships: dict[str, Any] = {}
        if options.allowed_workspace_ids:
            relationships["allowed-workspaces"] = {
                "data": [
                    {"type": "workspaces", "id": ws_id}
                    for ws_id in options.allowed_workspace_ids
                ]
            }
        if options.excluded_workspace_ids:
            relationships["excluded-workspaces"] = {
                "data": [
                    {"type": "workspaces", "id": ws_id}
                    for ws_id in options.excluded_workspace_ids
                ]
            }
        if options.allowed_project_ids:
            relationships["allowed-projects"] = {
                "data": [
                    {"type": "projects", "id": proj_id}
                    for proj_id in options.allowed_project_ids
                ]
            }

        payload: dict[str, Any] = {
            "data": {
                "type": "agent-pools",
                "id": agent_pool_id,
                "attributes": attributes,
            }
        }
        if relationships:
            payload["data"]["relationships"] = relationships

        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]

        return self._parse_agent_pool_from(data)

    def delete(self, agent_pool_id: str) -> None:
        """Delete an agent pool.

        Args:
            agent_pool_id: Agent pool ID

        Raises:
            ValueError: If agent_pool_id is invalid
            TFEError: If API request fails
        """
        if not valid_string_id(agent_pool_id):
            raise InvalidAgentPoolIDError()

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        self.t.request("DELETE", path)

    def assign_to_workspaces(
        self, agent_pool_id: str, options: AgentPoolAssignToWorkspacesOptions
    ) -> AgentPool:
        """Assign an agent pool to workspaces by updating the allowed-workspaces
        relationship via PATCH /agent-pools/:id.

        The provided workspace IDs become the new complete list of allowed
        workspaces for this pool (full replacement, not append).

        Args:
            agent_pool_id: Agent pool ID
            options: Assignment options containing workspace IDs

        Returns:
            Updated AgentPool object

        Raises:
            ValueError: If parameters are invalid
            TFEError: If API request fails
        """
        if not valid_string_id(agent_pool_id):
            raise InvalidAgentPoolIDError()

        if not options.workspace_ids:
            raise RequiredWorkspaceError()

        for workspace_id in options.workspace_ids:
            if not valid_string_id(workspace_id):
                raise InvalidWorkspaceIDError(f"Invalid workspace ID: {workspace_id}")

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        payload: dict[str, Any] = {
            "data": {
                "type": "agent-pools",
                "id": agent_pool_id,
                "attributes": {},
                "relationships": {
                    "allowed-workspaces": {
                        "data": [
                            {"type": "workspaces", "id": ws_id}
                            for ws_id in options.workspace_ids
                        ]
                    }
                },
            }
        }
        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]

        return self._parse_agent_pool_from(data)

    def remove_from_workspaces(
        self, agent_pool_id: str, options: AgentPoolRemoveFromWorkspacesOptions
    ) -> AgentPool:
        """Exclude workspaces from an agent pool by updating the excluded-workspaces
        relationship via PATCH /agent-pools/:id.

        Use this for organization-scoped pools where most workspaces are allowed
        but you want to block specific ones.  The provided list becomes the new
        complete excluded-workspaces list (full replacement, not append).

        Args:
            agent_pool_id: Agent pool ID
            options: Removal options containing workspace IDs to exclude

        Returns:
            Updated AgentPool object

        Raises:
            ValueError: If parameters are invalid
            TFEError: If API request fails
        """
        if not valid_string_id(agent_pool_id):
            raise InvalidAgentPoolIDError()

        if not options.workspace_ids:
            raise RequiredWorkspaceError()

        for workspace_id in options.workspace_ids:
            if not valid_string_id(workspace_id):
                raise InvalidWorkspaceIDError(f"Invalid workspace ID: {workspace_id}")

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        payload: dict[str, Any] = {
            "data": {
                "type": "agent-pools",
                "id": agent_pool_id,
                "attributes": {},
                "relationships": {
                    "excluded-workspaces": {
                        "data": [
                            {"type": "workspaces", "id": ws_id}
                            for ws_id in options.workspace_ids
                        ]
                    }
                },
            }
        }
        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]

        return self._parse_agent_pool_from(data)

    def assign_to_projects(
        self, agent_pool_id: str, options: AgentPoolAssignToProjectsOptions
    ) -> AgentPool:
        """Assign an agent pool to projects by updating the allowed-projects
        relationship via PATCH /agent-pools/:id.

        The provided project IDs become the new complete list of allowed
        projects for this pool (full replacement, not append).

        Args:
            agent_pool_id: Agent pool ID
            options: Assignment options containing project IDs
        """
        if not valid_string_id(agent_pool_id):
            raise InvalidAgentPoolIDError()

        if not options.project_ids:
            raise RequiredProjectError()

        for project_id in options.project_ids:
            if not valid_string_id(project_id):
                raise InvalidProjectIDError(f"Invalid project ID: {project_id}")

        path = f"/api/v2/agent-pools/{agent_pool_id}"
        payload: dict[str, Any] = {
            "data": {
                "type": "agent-pools",
                "id": agent_pool_id,
                "attributes": {},
                "relationships": {
                    "allowed-projects": {
                        "data": [
                            {"type": "projects", "id": project_id}
                            for project_id in options.project_ids
                        ]
                    }
                },
            }
        }
        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]

        return self._parse_agent_pool_from(data)

    def _parse_agent_pool_from(self, data: dict[str, Any]) -> AgentPool:
        """Helper method to parse agent pool data from API response."""
        attr = data.get("attributes", {})
        attr["id"] = data.get("id")
        attr.update(
            parse_relationships(
                data.get("relationships"),
                {
                    "agents": Agent,
                    "organization": Organization,
                    "workspaces": Workspace,
                    "allowed-workspaces": Workspace,
                    "excluded-workspaces": Workspace,
                    "allowed-projects": Project,
                },
            )
        )
        return AgentPool.model_validate(attr)
