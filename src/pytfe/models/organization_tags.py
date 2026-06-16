# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .organization import Organization


class OrganizationTag(TFEModel):
    """Terraform Enterprise organization tag."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str = Field(..., description="Tag ID")
    name: str | None = Field(None, description="Tag name")
    instance_count: int | None = Field(
        None,
        alias="instance-count",
        description="Number of workspaces that have this tag",
    )
    organization: Organization | None = Field(
        None,
        description="Organization this tag belongs to",
    )


class OrganizationTagsListOptions(BaseModel):
    """Options for listing organization tags."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    filter: str | None = Field(None, alias="filter[exclude][taggable][id]")
    query: str | None = Field(
        None,
        alias="q",
        description="Search query string for tag name likeness",
    )


class OrganizationTagsDeleteOptions(BaseModel):
    """Options for deleting tags from an organization."""

    model_config = ConfigDict(extra="forbid")

    ids: list[str] = Field(default_factory=list)


class AddWorkspacesToTagOptions(BaseModel):
    """Options for associating workspaces with a tag."""

    model_config = ConfigDict(extra="forbid")

    workspace_ids: list[str] = Field(default_factory=list)
