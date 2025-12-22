"""Organization Tags API resource."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidOrgError,
    InvalidTagIDError,
    RequiredTagIDError,
    RequiredTagWorkspaceIDError,
)
from ..models.organization_tag import (
    AddWorkspacesToTagOptions,
    OrganizationTag,
    OrganizationTagsDeleteOptions,
    OrganizationTagsListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class OrganizationTags(_Service):
    """Organization Tags API for Terraform Enterprise."""

    def list(
        self, organization: str, options: OrganizationTagsListOptions | None = None
    ) -> Iterator[OrganizationTag]:
        """Iterate through all tags in an organization.

        This method automatically handles pagination and yields OrganizationTag objects one at a time.

        Args:
            organization: The name of the organization
            options: Optional list options (page_size, page_number, filter, query)

        Yields:
            OrganizationTag objects one at a time

        Example:
            for tag in client.organization_tags.list(organization_name):
                print(f"Tag: {tag.name} - Instances: {tag.instance_count}")
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        params: dict[str, Any] = {}
        if options:
            params = options.model_dump(by_alias=True, exclude_none=True)

        path = f"/api/v2/organizations/{organization}/tags"
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")

            # Extract organization relationship
            relationships = item.get("relationships", {})
            org_rel = relationships.get("organization", {})
            org_data = org_rel.get("data", {})
            if org_data and isinstance(org_data, dict):
                attrs["organization_name"] = org_data.get("id")

            yield OrganizationTag.model_validate(attrs)

    def delete(
        self, organization: str, options: OrganizationTagsDeleteOptions
    ) -> None:
        """Delete tags from an organization.

        The organization and tags must already exist. Tags deleted here will be
        removed from all other resources.

        Args:
            organization: The name of the organization
            options: Options containing the list of tag IDs to delete

        Returns:
            None (204 No Content on success)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        if not options.ids:
            raise RequiredTagIDError()

        # Validate all tag IDs
        for tag_id in options.ids:
            if not valid_string_id(tag_id):
                raise InvalidTagIDError(f"{tag_id} is not a valid tag ID")

        # Build the request body with tag IDs
        tags_to_remove = [{"type": "tags", "id": tag_id} for tag_id in options.ids]

        path = f"/api/v2/organizations/{organization}/tags"
        self.t.request("DELETE", path, json_body={"data": tags_to_remove})

    def add_workspaces(
        self, tag_id: str, options: AddWorkspacesToTagOptions
    ) -> None:
        """Add workspaces to a tag.

        Associates the specified workspaces with the tag.

        Args:
            tag_id: The ID of the tag
            options: Options containing the list of workspace IDs to add

        Returns:
            None (204 No Content on success)
        """
        if not valid_string_id(tag_id):
            raise InvalidTagIDError()

        if not options.workspace_ids:
            raise RequiredTagWorkspaceIDError()

        # Validate all workspace IDs
        for workspace_id in options.workspace_ids:
            if not valid_string_id(workspace_id):
                raise RequiredTagWorkspaceIDError(
                    f"{workspace_id} is not a valid workspace ID"
                )

        # Build the request body with workspace IDs
        workspaces = [
            {"type": "workspaces", "id": workspace_id}
            for workspace_id in options.workspace_ids
        ]

        path = f"/api/v2/tags/{tag_id}/relationships/workspaces"
        self.t.request("POST", path, json_body={"data": workspaces})
