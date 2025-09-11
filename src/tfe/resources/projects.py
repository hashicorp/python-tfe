from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..types import Project
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


class Projects(_Service):
    def list(self, organization: str) -> Iterator[Project]:
        path = f"/api/v2/organizations/{organization}/projects"
        for item in self._list(path):
            attr = item.get("attributes", {}) or {}
            proj_id = _safe_str(item.get("id"))
            name = _safe_str(attr.get("name"))
            yield Project(id=proj_id, name=name, organization=organization)

    def create(self, organization: str, name: str) -> Project:
        """Create a new project in an organization"""
        path = f"/api/v2/organizations/{organization}/projects"
        payload = {
            "data": {
                "type": "projects",
                "attributes": {
                    "name": name
                }
            }
        }
        
        # Use json_body parameter (correct parameter name)
        response = self.t.request("POST", path, json_body=payload)
        data = response.json()["data"]
        attr = data.get("attributes", {}) or {}
        
        return Project(
            id=_safe_str(data.get("id")),
            name=_safe_str(attr.get("name")),
            organization=organization
        )

    def read(self, project_id: str) -> Project:
        """Get a specific project by ID"""
        path = f"/api/v2/projects/{project_id}"
        response = self.t.request("GET", path)
        data = response.json()["data"]
        attr = data.get("attributes", {}) or {}
        
        # Get organization from relationships if available
        relationships = data.get("relationships", {})
        org_data = relationships.get("organization", {}).get("data", {})
        organization = _safe_str(org_data.get("id"))
        
        return Project(
            id=_safe_str(data.get("id")),
            name=_safe_str(attr.get("name")),
            organization=organization
        )

    def update(self, project_id: str, name: str) -> Project:
        """Update a project's name"""
        path = f"/api/v2/projects/{project_id}"
        payload = {
            "data": {
                "type": "projects",
                "id": project_id,
                "attributes": {
                    "name": name
                }
            }
        }
        
        # Use json_body parameter (correct parameter name)
        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()["data"]
        attr = data.get("attributes", {}) or {}
        
        # Get organization from relationships if available
        relationships = data.get("relationships", {})
        org_data = relationships.get("organization", {}).get("data", {})
        organization = _safe_str(org_data.get("id"))
        
        return Project(
            id=_safe_str(data.get("id")),
            name=_safe_str(attr.get("name")),
            organization=organization
        )

    def delete(self, project_id: str) -> None:
        """Delete a project"""
        path = f"/api/v2/projects/{project_id}"
        self.t.request("DELETE", path)