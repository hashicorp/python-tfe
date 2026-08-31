# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
import re
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..models.agent import AgentPool
from ..models.common import (
    EffectiveTagBinding,
    TagBinding,
)
from ..models.organization import Organization
from ..models.project import (
    Project,
    ProjectAddTagBindingsOptions,
    ProjectCreateOptions,
    ProjectListOptions,
    ProjectUpdateOptions,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service


# Project validation functions
def valid_project_name(name: str) -> bool:
    """Validate project name format"""
    if not valid_string(name):
        return False
    # Project names can contain letters, numbers, spaces, hyphens, underscores, and periods
    # Must be between 1 and 90 characters
    if len(name) > 90:
        return False
    # Allow most printable characters except some special ones
    # Based on Terraform Cloud API documentation
    pattern = re.compile(r"^[a-zA-Z0-9\s._-]+$")
    return bool(pattern.match(name))


def valid_organization_name(org_name: str) -> bool:
    """Validate organization name format"""
    if not valid_string(org_name):
        return False
    # Organization names must be valid identifiers
    return valid_string_id(org_name)


def validate_project_create_options(
    organization: str, options: ProjectCreateOptions
) -> None:
    """Validate project creation parameters"""
    if not valid_organization_name(organization):
        raise ValueError("Organization name is required and must be valid")

    if not valid_string(options.name):
        raise ValueError("Project name is required")

    if not valid_project_name(options.name):
        raise ValueError("Project name contains invalid characters or is too long")

    if options.description is not None and not valid_string(options.description):
        raise ValueError("Description must be a valid string")

    if (
        options.default_execution_mode
        and options.default_execution_mode == "agent"
        and not options.default_agent_pool_id
    ):
        raise ValueError(
            "Default agent pool is required when default execution mode is set to 'agent'"
        )


def validate_project_update_options(
    project_id: str, options: ProjectUpdateOptions
) -> None:
    """Validate project update parameters"""
    if not valid_string_id(project_id):
        raise ValueError("Project ID is required")

    if options.name is not None:
        if not valid_string(options.name):
            raise ValueError("Project name cannot be empty")
        if not valid_project_name(options.name):
            raise ValueError("Project name contains invalid characters or is too long")

    if options.description is not None and not valid_string(options.description):
        raise ValueError("Description must be a valid string")

    if (
        options.default_execution_mode
        and options.default_execution_mode == "agent"
        and not options.default_agent_pool_id
    ):
        raise ValueError(
            "Default agent pool is required when default execution mode is set to 'agent'"
        )


def validate_project_list_options(
    organization: str, query: str | None = None, name: str | None = None
) -> None:
    """Validate project list options."""
    if not valid_organization_name(organization):
        raise ValueError("Organization name is required and must be valid")

    if query and not valid_string(query):
        raise ValueError("Query must be a valid string")

    if name and not valid_project_name(name):
        raise ValueError("Project name must be valid")


def _safe_str(value: Any, default: str = "") -> str:
    """Safely convert a value to string with optional default."""
    if value is None:
        return default
    return str(value)


class Projects(_Service):
    """Projects service for managing Terraform Enterprise projects"""

    def list(
        self, organization: str, options: ProjectListOptions | None = None
    ) -> Iterator[Project]:
        """List projects in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional filters and pagination, as a :class:`ProjectListOptions`.

        Returns:
            A single-use ``Iterator[Project]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ProjectListOptions
            >>> options = ProjectListOptions(page_size=20)
            >>> for project in client.projects.list("my-org", options):
            ...     print(project.id, project.name)
        """
        # Validate inputs
        validate_project_list_options(organization)

        path = f"/api/v2/organizations/{organization}/projects"
        params: dict[str, str | int] = {}

        if options:
            if options.include:
                params["include"] = ",".join(options.include)
            if options.query:
                params["q"] = options.query
            if options.name:
                params["filter[names]"] = options.name
            if options.tags:
                for i, (tag_name, tag_value) in enumerate(options.tags.items()):
                    params[f"filter[tagged][{i}][key]"] = _safe_str(tag_name)
                    params[f"filter[tagged][{i}][value]"] = _safe_str(tag_value)
            if options.page_size:
                params["page[size]"] = options.page_size

        if params:
            items_iter = self._list(path, params=params)
        else:
            items_iter = self._list(path)

        for item in items_iter:
            # Extract project data
            yield self._project_from(item)

    def create(self, organization: str, options: ProjectCreateOptions) -> Project:
        """Create a project in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The project settings, as a :class:`ProjectCreateOptions`.

        Returns:
            The created :class:`Project`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ProjectCreateOptions
            >>> project = client.projects.create(
            ...     "my-org", ProjectCreateOptions(name="Platform")
            ... )
        """
        # Validate inputs
        validate_project_create_options(organization, options)

        path = f"/api/v2/organizations/{organization}/projects"
        attributes = options.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude={"tag_bindings", "setting_overwrites"},
        )
        if options.setting_overwrites:
            attributes["setting-overwrites"] = options.setting_overwrites.model_dump(
                by_alias=True, exclude_none=True
            )
        if options.tag_bindings:
            relationships = {}
            data = [
                {
                    "type": "tag-bindings",
                    "attributes": tag_binding.model_dump(
                        by_alias=True, exclude_none=True
                    ),
                }
                for tag_binding in options.tag_bindings
            ]
            relationships["tag-bindings"] = {"data": data}
            payload = {
                "data": {
                    "type": "projects",
                    "attributes": attributes,
                    "relationships": relationships,
                }
            }
        else:
            payload = {"data": {"type": "projects", "attributes": attributes}}

        response = self.t.request("POST", path, json_body=payload)
        data = response.json()["data"]

        return self._project_from(data)

    def read(
        self, project_id: str, include: builtins.list[str] | None = None
    ) -> Project:
        """Read a project by its ID.

        Args:
            project_id: The project ID (e.g. ``"prj-xxxxxxxx"``).
            include: Related resources to include, such as ``["default-agent-pool"]``.

        Returns:
            The :class:`Project`.

        Raises:
            ValueError: If ``project_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> project = client.projects.read("prj-123")
            >>> print(project.name)
        """
        # Validate inputs
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}"
        params: dict[str, str] = {}
        if include:
            params["include"] = ",".join(include)

        if params:
            response = self.t.request("GET", path, params=params)
        else:
            response = self.t.request("GET", path)

        payload = response.json()

        return self._project_from(payload["data"], payload.get("included"))

    def update(self, project_id: str, options: ProjectUpdateOptions) -> Project:
        """Update a project.

        Args:
            project_id: The project ID (e.g. ``"prj-xxxxxxxx"``).
            options: The project fields to change, as a :class:`ProjectUpdateOptions`.

        Returns:
            The updated :class:`Project`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ProjectUpdateOptions
            >>> project = client.projects.update(
            ...     "prj-123", ProjectUpdateOptions(description="Shared services")
            ... )
        """
        # Validate inputs
        validate_project_update_options(project_id, options)

        path = f"/api/v2/projects/{project_id}"
        attributes = options.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude={"tag_bindings", "setting_overwrites"},
        )
        if options.setting_overwrites:
            attributes["setting-overwrites"] = options.setting_overwrites.model_dump(
                by_alias=True, exclude_none=True
            )
        if options.tag_bindings:
            relationships = {}
            data = [
                {
                    "type": "tag-bindings",
                    "attributes": tag_binding.model_dump(
                        by_alias=True, exclude_none=True
                    ),
                }
                for tag_binding in options.tag_bindings
            ]
            relationships["tag-bindings"] = {"data": data}
            payload = {
                "data": {
                    "type": "projects",
                    "attributes": attributes,
                    "relationships": relationships,
                }
            }
        else:
            payload = {"data": {"type": "projects", "attributes": attributes}}

        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]

        return self._project_from(data)

    def delete(self, project_id: str) -> None:
        """Delete a project.

        Args:
            project_id: The project ID (e.g. ``"prj-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``project_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.projects.delete("prj-123")
        """
        # Validate inputs
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}"
        self.t.request("DELETE", path)

    def move_workspaces(
        self, project_id: str, workspace_ids: builtins.list[str]
    ) -> None:
        """Move one or more workspaces into a project.

        The caller must have permission to move each workspace out of its current
        project and into the target project.

        Args:
            project_id: The destination project ID (e.g. ``"prj-xxxxxxxx"``).
            workspace_ids: Workspace IDs to move (e.g. ``["ws-xxxxxxxx"]``).

        Returns:
            None.

        Raises:
            ValueError: If ``project_id`` or any workspace ID is invalid, or no
                workspace IDs are provided.
            TFEError: If the API request fails.

        Example:
            >>> client.projects.move_workspaces("prj-123", ["ws-abc123"])
        """
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")
        if not workspace_ids:
            raise ValueError("at least one workspace id is required")
        for wid in workspace_ids:
            if not valid_string_id(wid):
                raise ValueError(f"invalid workspace id: {wid!r}")
        payload = {"data": [{"id": wid, "type": "workspaces"} for wid in workspace_ids]}
        self.t.request(
            "POST",
            f"/api/v2/projects/{project_id}/relationships/workspaces",
            json_body=payload,
        )
        return None

    def list_tag_bindings(self, project_id: str) -> builtins.list[TagBinding]:
        """List tag bindings for a project.

        Args:
            project_id: The project ID (e.g. ``"prj-xxxxxxxx"``).

        Returns:
            A ``list[TagBinding]``.

        Raises:
            ValueError: If ``project_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> tags = client.projects.list_tag_bindings("prj-123")
            >>> print(tags[0].key)
        """
        # Validate inputs
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}/tag-bindings"
        response = self.t.request("GET", path)
        data = response.json()["data"]

        tag_bindings = []
        for item in data:
            attr = item.get("attributes", {}) or {}
            tag_binding = TagBinding(
                id=_safe_str(item.get("id")),
                key=_safe_str(attr.get("key")),
                value=_safe_str(attr.get("value")),
            )
            tag_bindings.append(tag_binding)

        return tag_bindings

    def list_effective_tag_bindings(
        self, project_id: str
    ) -> Iterator[EffectiveTagBinding]:
        """List effective tag bindings for a project.

        Args:
            project_id: The project ID (e.g. ``"prj-xxxxxxxx"``).

        Returns:
            A single-use ``Iterator[EffectiveTagBinding]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``project_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for tag in client.projects.list_effective_tag_bindings("prj-123"):
            ...     print(tag.key, tag.value)
        """
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        # effective-tag-bindings is not paginated.
        path = f"/api/v2/projects/{project_id}/effective-tag-bindings"
        for item in self._list(path, paginated=False):
            attr = item.get("attributes", {}) or {}
            links = item.get("links", {}) or {}
            yield EffectiveTagBinding(
                id=_safe_str(item.get("id")),
                key=_safe_str(attr.get("key")),
                value=_safe_str(attr.get("value")),
                links=links,
            )

    def add_tag_bindings(
        self, project_id: str, options: ProjectAddTagBindingsOptions
    ) -> builtins.list[TagBinding]:
        """Add or update tag bindings on a project.

        This endpoint adds key-value tag bindings to an existing project or updates
        existing tag binding values. It cannot remove tag bindings.

        Args:
            project_id: The project ID (e.g. ``"prj-xxxxxxxx"``).
            options: Tag bindings to add, as a :class:`ProjectAddTagBindingsOptions`.

        Returns:
            A ``list[TagBinding]``.

        Raises:
            ValueError: If ``project_id`` is invalid or no tag bindings are provided.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ProjectAddTagBindingsOptions, TagBinding
            >>> options = ProjectAddTagBindingsOptions(
            ...     tag_bindings=[TagBinding(key="env", value="prod")]
            ... )
            >>> tags = client.projects.add_tag_bindings(
            ...     "prj-123", options
            ... )
        """
        # Validate inputs
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        if not options.tag_bindings:
            raise ValueError("At least one tag binding is required")

        path = f"/api/v2/projects/{project_id}/tag-bindings"

        # Build payload with tag binding data
        data_items = []
        for tag_binding in options.tag_bindings:
            attributes = {"key": tag_binding.key}
            if tag_binding.value is not None:
                attributes["value"] = tag_binding.value

            data_items.append({"type": "tag-bindings", "attributes": attributes})

        payload = {"data": data_items}

        # Use PATCH method as per API documentation
        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]

        # Parse response into TagBinding objects
        tag_bindings = []
        for item in data:
            attr = item.get("attributes", {}) or {}
            tag_binding = TagBinding(
                id=_safe_str(item.get("id")),
                key=_safe_str(attr.get("key")),
                value=_safe_str(attr.get("value")),
            )
            tag_bindings.append(tag_binding)

        return tag_bindings

    def delete_tag_bindings(self, project_id: str) -> None:
        """Delete all tag bindings from a project.

        Args:
            project_id: The project ID (e.g. ``"prj-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``project_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.projects.delete_tag_bindings("prj-123")
        """
        # Validate inputs
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        payload = {
            "data": {
                "type": "projects",
                "relationships": {"tag-bindings": {"data": []}},
            }
        }

        path = f"/api/v2/projects/{project_id}"
        self.t.request("PATCH", path, json_body=payload)

    def _project_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> Project:
        """Helper method to create a Project object from API response data"""
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        relationships = data.get("relationships", {})
        org_data = relationships.get("organization", {}).get("data", {})
        organization = _safe_str(org_data.get("id")) if org_data else None
        default_agent_pool_data = relationships.get("default-agent-pool", {}).get(
            "data", {}
        )
        attrs["organization"] = Organization(id=organization) if organization else None
        attrs["default_agent_pool"] = (
            AgentPool(id=_safe_str(default_agent_pool_data.get("id")))
            if default_agent_pool_data
            else None
        )

        return attach_jsonapi(Project.model_validate(attrs), data, included)
