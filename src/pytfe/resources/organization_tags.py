# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import quote

from ..errors import (
    ERR_INVALID_ORG,
    ERR_INVALID_TAG,
    ERR_REQUIRED_TAG_ID,
    ERR_REQUIRED_TAG_WORKSPACE_ID,
)
from ..models.organization import Organization
from ..models.organization_tags import (
    AddWorkspacesToTagOptions,
    OrganizationTag,
    OrganizationTagsDeleteOptions,
    OrganizationTagsListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class OrganizationTags(_Service):
    """Organization tags service for Terraform Enterprise."""

    def list(
        self,
        organization: str,
        options: OrganizationTagsListOptions | None = None,
    ) -> Iterator[OrganizationTag]:
        """List all tags within an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional tag filters, as a :class:`OrganizationTagsListOptions`.

        Returns:
            A single-use ``Iterator[OrganizationTag]``. Wrap with ``list(...)``
            to materialize the results or iterate more than once.

        Raises:
            ValueError: If an argument or options value is invalid.

        Example:
            >>> from pytfe.models import OrganizationTagsListOptions
            >>> for tag in client.organization_tags.list(
            ...     "my-org", OrganizationTagsListOptions(query="env")
            ... ):
            ...     print(tag.id, tag.name)
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)
        return self._iter_tags(organization, options)

    def _iter_tags(
        self,
        organization: str,
        options: OrganizationTagsListOptions | None = None,
    ) -> Iterator[OrganizationTag]:
        path = f"/api/v2/organizations/{quote(organization)}/tags"
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        for item in self._list(path, params=params):
            yield self._parse_organization_tag(item)

    def delete(
        self,
        organization: str,
        options: OrganizationTagsDeleteOptions,
    ) -> None:
        """Delete tags from an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Tag IDs to delete, as a :class:`OrganizationTagsDeleteOptions`.

        Returns:
            None.

        Raises:
            ValueError: If an argument or options value is invalid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OrganizationTagsDeleteOptions
            >>> client.organization_tags.delete(
            ...     "my-org", OrganizationTagsDeleteOptions(ids=["tag-1"])
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        if len(options.ids) == 0:
            raise ValueError(ERR_REQUIRED_TAG_ID)

        for tag_id in options.ids:
            if not valid_string_id(tag_id):
                raise ValueError(f"{tag_id} is not a valid id value")

        body = {"data": [{"type": "tags", "id": tag_id} for tag_id in options.ids]}
        path = f"/api/v2/organizations/{quote(organization)}/tags"
        self.t.request("DELETE", path, json_body=body)

    def add_workspaces(
        self, organization: str, tag: str, options: AddWorkspacesToTagOptions
    ) -> None:
        """Associate workspaces with an organization tag.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            tag: The organization tag ID (e.g. ``"tag-xxxxxxxx"``).
            options: Workspace IDs to associate, as a
                :class:`AddWorkspacesToTagOptions`.

        Returns:
            None.

        Raises:
            ValueError: If an argument or options value is invalid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AddWorkspacesToTagOptions
            >>> client.organization_tags.add_workspaces(
            ...     "my-org", "tag-1",
            ...     AddWorkspacesToTagOptions(workspace_ids=["ws-xxxxxxxx"]),
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)
        if not valid_string_id(tag):
            raise ValueError(ERR_INVALID_TAG)

        if len(options.workspace_ids) == 0:
            raise ValueError(ERR_REQUIRED_TAG_WORKSPACE_ID)

        for workspace_id in options.workspace_ids:
            if not valid_string_id(workspace_id):
                raise ValueError(f"{workspace_id} is not a valid id value")

        body = {
            "data": [
                {"type": "workspaces", "id": workspace_id}
                for workspace_id in options.workspace_ids
            ]
        }
        path = f"/api/v2/tags/{quote(tag)}/relationships/workspaces"
        self.t.request("POST", path, json_body=body)

    def _parse_organization_tag(self, data: dict[str, Any]) -> OrganizationTag:
        attributes = data.get("attributes", {})
        relationships = data.get("relationships", {})

        org = None
        org_data = relationships.get("organization", {}).get("data")
        if org_data and isinstance(org_data, dict):
            org = Organization(id=org_data.get("id"))

        return OrganizationTag.model_validate(
            {
                "id": data.get("id", ""),
                "name": attributes.get("name"),
                "instance-count": attributes.get("instance-count"),
                "organization": org,
            }
        )
