from __future__ import annotations

import builtins
import re
from collections.abc import Iterator
from typing import Any

from ..types import (
    EffectiveTagBinding,
    Project,
    ProjectAddTagBindingsOptions,
    ProjectCreateOptions,
    ProjectListOptions,
    ProjectUpdateOptions,
    TagBinding,
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
    """Validate project list options following Go TFE patterns."""
    if not valid_organization_name(organization):
        raise ValueError("Organization name is required and must be valid")

    if query and not valid_string(query):
        raise ValueError("Query must be a valid string")

    if name and not valid_project_name(name):
        raise ValueError("Project name must be valid")


def valid_tag_key(key: str) -> bool:
    """Validate tag key format following Go TFE patterns"""
    if not valid_string(key):
        return False
    # Tag keys must be between 1 and 128 characters
    if len(key) > 128:
        return False
    # Tag keys can contain letters, numbers, hyphens, underscores
    pattern = re.compile(r"^[a-zA-Z0-9_-]+$")
    return bool(pattern.match(key))


def valid_tag_value(value: str | None) -> bool:
    """Validate tag value format following Go TFE patterns"""
    # Tag values can be empty/None (for tag existence checks)
    if value is None or value == "":
        return True
    # Tag values must be less than 256 characters
    if len(value) > 256:
        return False
    # Tag values can contain most characters but not control characters
    return not any(ord(c) < 32 or ord(c) == 127 for c in value)


def _safe_str(value: Any, default: str = "") -> str:
    """Safely convert a value to string with optional default."""
    if value is None:
        return default
    return str(value)


def validate_tag_binding(tag_binding: TagBinding) -> None:
    """Validate a tag binding following Go TFE patterns"""
    if not valid_tag_key(tag_binding.key):
        raise ValueError(f"Invalid tag key: {tag_binding.key}")

    if not valid_tag_value(tag_binding.value):
        raise ValueError(f"Invalid tag value: {tag_binding.value}")


def validate_project_add_tag_bindings_options(
    project_id: str, options: ProjectAddTagBindingsOptions
) -> None:
    """Validate project add tag bindings parameters following Go TFE patterns"""
    if not valid_string_id(project_id):
        raise ValueError("Project ID is required and must be valid")

    if not options.tag_bindings:
        raise ValueError("Tag bindings are required")

    if len(options.tag_bindings) > 10:
        raise ValueError("Cannot exceed 10 tag bindings per project")

    for tag_binding in options.tag_bindings:
        validate_tag_binding(tag_binding)


class Projects(_Service):
    """Projects service for managing Terraform Enterprise projects"""

    def list(
        self, organization: str, options: ProjectListOptions | None = None
    ) -> Iterator[Project]:
        """List projects in an organization"""
        # Validate inputs following Go patterns
        validate_project_list_options(organization)

        path = f"/api/v2/organizations/{organization}/projects"

        # Build params dict - base class expects integer values for pagination
        params: dict[str, str | int] = {}

        if options:
            if options.include:
                params["include"] = ",".join(options.include)
            if options.query:
                params["q"] = options.query
            if options.name:
                params["filter[names]"] = options.name

        # Handle pagination by letting base class manage it entirely for now
        # Base class will set default page[number]=1 and page[size]=100
        items_iter = self._list(path, params=params if params else None)

        for item in items_iter:
            # Extract project data following Go patterns
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
        # Validate inputs following Go patterns
        validate_project_create_options(organization, options.name, options.description)

        path = f"/api/v2/organizations/{organization}/projects"
        attributes = {"name": options.name}
        if options.description:
            attributes["description"] = options.description

        payload = {"data": {"type": "projects", "attributes": attributes}}

        response = self.t.request("POST", path, json_body=payload)
        data = response.json()["data"]

        # Extract project data following Go patterns
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
        # Validate inputs following Go patterns
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

        # Extract project data following Go patterns
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
        # Validate inputs following Go patterns
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

        # Extract project data following Go patterns
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
        # Validate inputs following Go patterns
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}"
        self.t.request("DELETE", path)

    def list_tag_bindings(self, project_id: str) -> builtins.list[TagBinding]:
        """List all tag bindings associated with the project"""
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}/tag-bindings"
        response = self.t.request("GET", path)
        data = response.json()["data"]

        tag_bindings = []
        for binding_data in data:
            attr = binding_data.get("attributes", {})
            tag_binding = TagBinding(
                id=binding_data.get("id"),
                key=_safe_str(attr.get("key")),
                value=_safe_str(attr.get("value")),
            )
            tag_bindings.append(tag_binding)

        return tag_bindings

    def list_effective_tag_bindings(
        self, project_id: str
    ) -> builtins.list[EffectiveTagBinding]:
        """List all effective tag bindings associated with the project"""
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        path = f"/api/v2/projects/{project_id}/effective-tag-bindings"
        response = self.t.request("GET", path)
        data = response.json()["data"]

        effective_bindings = []
        for binding_data in data:
            attr = binding_data.get("attributes", {})
            links = binding_data.get("links", {})

            effective_binding = EffectiveTagBinding(
                id=binding_data.get("id"),
                key=_safe_str(attr.get("key")),
                value=_safe_str(attr.get("value")),
                links=links if links else None,
            )
            effective_bindings.append(effective_binding)

        return effective_bindings

    def add_tag_bindings(
        self, project_id: str, options: ProjectAddTagBindingsOptions
    ) -> builtins.list[TagBinding]:
        """Add or modify tag bindings for a project"""
        # Validate inputs following Go TFE patterns
        validate_project_add_tag_bindings_options(project_id, options)

        path = f"/api/v2/projects/{project_id}/tag-bindings"

        # Prepare the tag bindings data for the API
        tag_bindings_data = []
        for binding in options.tag_bindings:
            binding_data = {
                "type": "tag-bindings",
                "attributes": {
                    "key": binding.key,
                    "value": binding.value or "",
                },
            }
            tag_bindings_data.append(binding_data)

        # Wrap in JSON:API structure
        payload = {"data": tag_bindings_data}

        response = self.t.request("PATCH", path, json_body=payload)
        response_data = response.json()["data"]

        # Parse response into TagBinding objects
        result_bindings = []
        for binding_data in response_data:
            attr = binding_data.get("attributes", {})
            tag_binding = TagBinding(
                id=binding_data.get("id"),
                key=_safe_str(attr.get("key")),
                value=_safe_str(attr.get("value")),
            )
            result_bindings.append(tag_binding)

        return result_bindings

    def delete_all_tag_bindings(self, project_id: str) -> None:
        """Delete all tag bindings associated with a project"""
        if not valid_string_id(project_id):
            raise ValueError("Project ID is required and must be valid")

        # Use PATCH request with empty tag bindings array to clear all bindings
        path = f"/api/v2/projects/{project_id}"

        # Empty tag bindings relationship to clear all
        data = {
            "data": {
                "type": "projects",
                "id": project_id,
                "relationships": {"tag-bindings": {"data": []}},
            }
        }

        self.t.request("PATCH", path, json_body=data)
