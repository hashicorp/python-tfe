# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ..errors import (
    ERR_INVALID_ORG,
)
from ..models.common import Pagination
from ..models.organization import Organization
from ..models.organization_tags import (
    AddWorkspacesToTagOptions,
    OrganizationTag,
    OrganizationTagsDeleteOptions,
    OrganizationTagsList,
    OrganizationTagsListOptions,
)
from ..utils import valid_string_id
from ._base import _Service

ERR_INVALID_TAG = "invalid value for tag"
ERR_REQUIRED_TAG_ID = "tag ID is required"
ERR_REQUIRED_TAG_WORKSPACE_ID = "workspace ID is required"


class OrganizationTags(_Service):
    """Organization tags service for Terraform Enterprise."""

    def list(
        self,
        organization: str,
        options: OrganizationTagsListOptions | None = None,
    ) -> OrganizationTagsList:
        """List all tags within an organization."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{quote(organization)}/tags"
        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )

        response = self.t.request("GET", path, params=params)
        payload = response.json() or {}

        items = [self._parse_organization_tag(item) for item in payload.get("data", [])]

        pagination = None
        meta = payload.get("meta", {})
        pagination_data = meta.get("pagination", {}) if isinstance(meta, dict) else {}
        if pagination_data:
            pagination = Pagination(
                current_page=pagination_data.get("current-page", 1),
                total_count=pagination_data.get("total-count", len(items)),
                previous_page=pagination_data.get("previous-page"),
                next_page=pagination_data.get("next-page"),
                total_pages=pagination_data.get("total-pages"),
            )

        return OrganizationTagsList(pagination=pagination, items=items)

    def delete(
        self,
        organization: str,
        options: OrganizationTagsDeleteOptions,
    ) -> None:
        """Delete tags from an organization."""
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
        """Associate workspaces with an organization tag."""
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

        return OrganizationTag(
            id=data.get("id", ""),
            name=attributes.get("name"),
            instance_count=attributes.get("instance-count"),
            organization=org,
        )
