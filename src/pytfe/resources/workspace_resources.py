# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Workspace resources service for Terraform Enterprise."""

from collections.abc import Iterator
from typing import Any

from pytfe.models import (
    WorkspaceResource,
    WorkspaceResourceListOptions,
)

from .._jsonapi import attach_jsonapi
from ._base import _Service


def _workspace_resource_from(data: dict[str, Any]) -> WorkspaceResource:
    """Convert API response data to WorkspaceResource model."""
    attributes = data.get("attributes", {})

    return attach_jsonapi(
        WorkspaceResource(
            id=data.get("id", ""),
            address=attributes.get("address", ""),
            name=attributes.get("name", ""),
            created_at=attributes.get("created-at", ""),
            updated_at=attributes.get("updated-at", ""),
            module=attributes.get("module", ""),
            provider=attributes.get("provider", ""),
            provider_type=attributes.get("provider-type", ""),
            modified_by_state_version_id=attributes.get(
                "modified-by-state-version-id", ""
            ),
            name_index=attributes.get("name-index"),
        ),
        data,
    )


class WorkspaceResourcesService(_Service):
    """Service for managing workspace resources in Terraform Enterprise.

    Workspace resources represent the infrastructure resources
    managed by Terraform in a workspace's state file.
    """

    def list(
        self, workspace_id: str, options: WorkspaceResourceListOptions | None = None
    ) -> Iterator[WorkspaceResource]:
        """List resources in a workspace state.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Optional pagination settings, as a
                :class:`WorkspaceResourceListOptions`.

        Returns:
            A single-use ``Iterator[WorkspaceResource]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``workspace_id`` is empty.
            TFEError: If the API request fails.

        Example:
            >>> for resource in client.workspace_resources.list("ws-abc123"):
            ...     print(resource.address)
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
