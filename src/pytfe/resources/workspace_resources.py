"""Workspace resources service for Terraform Enterprise."""

from collections.abc import Iterator
from typing import Any

from pytfe.models import (
    WorkspaceResource,
    WorkspaceResourceListOptions,
)

from ._base import _Service


def _workspace_resource_from(data: dict[str, Any]) -> WorkspaceResource:
    """Convert API response data to WorkspaceResource model."""
    attributes = data.get("attributes", {})

    return WorkspaceResource(
        id=data.get("id", ""),
        address=attributes.get("address", ""),
        name=attributes.get("name", ""),
        created_at=attributes.get("created-at", ""),
        updated_at=attributes.get("updated-at", ""),
        module=attributes.get("module", ""),
        provider=attributes.get("provider", ""),
        provider_type=attributes.get("provider-type", ""),
        modified_by_state_version_id=attributes.get("modified-by-state-version-id", ""),
        name_index=attributes.get("name-index"),
    )


class WorkspaceResourcesService(_Service):
    """Service for managing workspace resources in Terraform Enterprise.

    Workspace resources represent the infrastructure resources
    managed by Terraform in a workspace's state file.
    """

    def list(
        self, workspace_id: str, options: WorkspaceResourceListOptions | None = None
    ) -> Iterator[WorkspaceResource]:
        """List workspace resources for a given workspace.

        Args:
            workspace_id: The ID of the workspace to list resources for
            options: Optional query parameters for filtering and pagination

        Yields:
            WorkspaceResource objects
        """
        if not workspace_id or not workspace_id.strip():
            raise ValueError("workspace_id is required")

        url = f"/api/v2/workspaces/{workspace_id}/resources"

        # Handle parameters
        params: dict[str, int] = {}
        if options:
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size

        # Use the _list method from base service to handle pagination
        for item in self._list(url, params=params):
            yield _workspace_resource_from(item)
