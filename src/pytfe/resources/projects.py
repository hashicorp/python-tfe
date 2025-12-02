from __future__ import annotations

import builtins
import re
from collections.abc import Iterator
from typing import Any

from ..models.common import (
    EffectiveTagBinding,
    TagBinding,
)
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
    organization: str, name: str, description: str | None = None
) -> None:
    """Validate project creation parameters"""
    if not valid_organization_name(organization):
        raise ValueError("Organization name is required and must be valid")

    if not valid_string(name):
        raise ValueError("Project name is required")

    if not valid_project_name(name):
        raise ValueError("Project name contains invalid characters or is too long")

    if description is not None and not valid_string(description):
        raise ValueError("Description must be a valid string")


def validate_project_update_options(
    project_id: str, name: str | None = None, description: str | None = None
) -> None:
    """Validate project update parameters"""
    if not valid_string_id(project_id):
        raise ValueError("Project ID is required")

    if name is not None:
        if not valid_string(name):
            raise ValueError("Project name cannot be empty")
        if not valid_project_name(name):
            raise ValueError("Project name contains invalid characters or is too long")

    if description is not None and not valid_string(description):
        raise ValueError("Description must be a valid string")


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
        """List projects in an organization"""
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
            if options.page_number:
                params["page[number]"] = options.page_number
            if options.page_size:
                params["page[size]"] = options.page_size

        if params:
            items_iter = self._list(path, params=params)
        else:
            items_iter = self._list(path)

        for item in items_iter:
            # Extract project data
            attr = item.get("attributes", {}) or {}
            project_data = {
                "id": _safe_str(item.get("id")),
                "name": _safe_str(attr.get("name")),
                "description": _safe_str(attr.get("description")),
                "organization": organization,
                "created_at": _safe_str(attr.get("created-at")),
                "updated_at": _safe_str(attr.get("updated-at")),
                "workspace_count": attr.get("workspace-count", 0),
                "default_execution_mode": _safe_str(
                    attr.get("default-execution-mode"), "remote"
                ),
            }
            yield Project(**project_data)

    def create(self, organization: str, options: ProjectCreateOptions) -> Project:
        """Create a new project in an organization"""
        # Validate inputs
        validate_project_create_options(organization, options.name, options.description)

        path = f"/api/v2/organizations/{organization}/projects"
        attributes = {"name": options.name}
        if options.description:
            attributes["description"] = options.description

        payload = {"data": {"type": "projects", "attributes": attributes}}

        response = self.t.request("POST", path, json_body=payload)
        data = response.json()["data"]

        # Extract project data
        attr = data.get("attributes", {}) or {}
        project_data = {
            "id": _safe_str(data.get("id")),
            "name": _safe_str(attr.get("name")),
            "description": _safe_str(attr.get("description")),
            "organization": organization,
            "created_at": _safe_str(attr.get("created-at")),
            "updated_at": _safe_str(attr.get("updated-at")),
            "workspace_count": attr.get("workspace-count", 0),
            "default_execution_mode": _safe_str(
                attr.get("default-execution-mode"), "remote"
            ),
        }
        return Project(**project_data)

    def read(
        self, project_id: str, include: builtins.list[str] | None = None
    ) -> Project:
        """Get a specific project by ID"""
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

        data = response.json()["data"]

        # Extract organization from relationships
        relationships = data.get("relationships", {})
        org_data = relationships.get("organization", {}).get("data", {})
        organization = _safe_str(org_data.get("id"))

        # Extract project data
        attr = data.get("attributes", {}) or {}
        project_data = {
            "id": _safe_str(data.get("id")),
            "name": _safe_str(attr.get("name")),
            "description": _safe_str(attr.get("description")),
            "organization": organization,
            "created_at": _safe_str(attr.get("created-at")),
            "updated_at": _safe_str(attr.get("updated-at")),
            "workspace_count": attr.get("workspace-count", 0),
            "default_execution_mode": _safe_str(
                attr.get("default-execution-mode"), "remote"
            ),
        }
        return Project(**project_data)

    def update(self, project_id: str, options: ProjectUpdateOptions) -> Project:
        """Update a project's name and/or description"""
        # Validate inputs
        validate_project_update_options(project_id, options.name, options.description)

        path = f"/api/v2/projects/{project_id}"
        attributes = {}

        if options.name is not None:
            attributes["name"] = options.name
        if options.description is not None:
            attributes["description"] = options.description

        payload = {
            "data": {"type": "projects", "id": project_id, "attributes": attributes}
        }

        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]

        # Extract organization from relationships
        relationships = data.get("relationships", {})
        org_data = relationships.get("organization", {}).get("data", {})
        organization = _safe_str(org_data.get("id"))

        # Extract project data
        attr = data.get("attributes", {}) or {}
        project_data = {
            "id": _safe_str(data.get("id")),
            "name": _safe_str(attr.get("name")),
            "description": _safe_str(attr.get("description")),
            "organization": organization,
            "created_at": _safe_str(attr.get("created-at")),
            "updated_at": _safe_str(attr.get("updated-at")),
            "workspace_count": attr.get("workspace-count", 0),
            "default_execution_mode": _safe_str(
                attr.get("default-execution-mode"), "remote"
            ),
        }
        return Project(**project_data)

    def delete(self, project_id: str) -> None:
        """Delete a project"""
        # Validate inputs
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}"
        self.t.request("DELETE", path)

    def list_tag_bindings(self, project_id: str) -> builtins.list[TagBinding]:
        """List tag bindings for a project"""
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
    ) -> builtins.list[EffectiveTagBinding]:
        """List effective tag bindings for a project"""
        # Validate inputs
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}/tag-bindings/effective"
        response = self.t.request("GET", path)
        data = response.json()["data"]

        effective_tag_bindings = []
        for item in data:
            attr = item.get("attributes", {}) or {}
            links = item.get("links", {}) or {}
            effective_tag_binding = EffectiveTagBinding(
                id=_safe_str(item.get("id")),
                key=_safe_str(attr.get("key")),
                value=_safe_str(attr.get("value")),
                links=links,
            )
            effective_tag_bindings.append(effective_tag_binding)

        return effective_tag_bindings

    def add_tag_bindings(
        self, project_id: str, options: ProjectAddTagBindingsOptions
    ) -> builtins.list[TagBinding]:
        """Add or update tag bindings on a project

        This endpoint adds key-value tag bindings to an existing project or updates
        existing tag binding values. It cannot be used to remove tag bindings.
        This operation is additive.

        Constraints:
        - A project can have up to 10 tags
        - Keys can have up to 128 characters
        - Values can have up to 256 characters
        - Keys/values support alphanumeric chars and symbols: _, ., =, +, -, @, :
        - Cannot use hc: and hcp: as key prefixes
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
        """Delete all tag bindings from a project"""
        # Validate inputs
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}/tag-bindings"
        self.t.request("DELETE", path)
