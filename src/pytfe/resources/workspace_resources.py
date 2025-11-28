"""Workspace resources service for Terraform Enterprise."""

import urllib.parse
from typing import Any

from ..models.common import Pagination
from ..models.workspace_resource import (
    WorkspaceResource,
    WorkspaceResourceListOptions,
    WorkspaceResourcesList,
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
    ) -> WorkspaceResourcesList:
        """List workspace resources for a given workspace.

        Args:
            workspace_id: The ID of the workspace to list resources for
            options: Optional query parameters for filtering and pagination

        Returns:
            WorkspaceResourcesList containing resources and pagination info
        """
        if not workspace_id or not workspace_id.strip():
            raise ValueError("workspace_id is required")

        # URL encode the workspace ID and construct URL without leading slash
        encoded_workspace_id = urllib.parse.quote(workspace_id, safe="")
        url = f"workspaces/{encoded_workspace_id}/resources"

        # Handle parameters - use None if no params to match test expectations
        params: dict[str, int] | None = None
        if options:
            temp_params: dict[str, int] = {}
            if options.page_number is not None:
                temp_params["page_number"] = options.page_number
            if options.page_size is not None:
                temp_params["page_size"] = options.page_size
            # If we have actual params, use them; otherwise keep None
            if temp_params:
                params = temp_params

        response = self.t.request("GET", url, params=params)
        response_data = response.json()

        # Transform workspace resources
        resources = []
        if "data" in response_data:
            for item in response_data["data"]:
                resource = _workspace_resource_from(item)
                resources.append(resource)

        # Transform pagination info
        pagination = None
        if "meta" in response_data and "pagination" in response_data["meta"]:
            meta_pagination = response_data["meta"]["pagination"]
            pagination = Pagination(
                current_page=meta_pagination.get("current-page", meta_pagination.get("current_page", 1)),
                total_count=meta_pagination.get("total-count", meta_pagination.get("total_count", 0)),
                previous_page=meta_pagination.get("prev-page", meta_pagination.get("previous_page")),
                next_page=meta_pagination.get("next-page", meta_pagination.get("next_page")),
                total_pages=meta_pagination.get("total-pages", meta_pagination.get("total_pages", 1)),
            )

        return WorkspaceResourcesList(data=resources, pagination=pagination)
