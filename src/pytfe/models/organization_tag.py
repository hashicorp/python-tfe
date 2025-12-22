"""Models for organization tags."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationTag(BaseModel):
    """Represents a Terraform Enterprise Organization tag."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="The unique identifier for this organization tag")
    name: str | None = Field(
        None, description="The name of the tag"
    )
    instance_count: int | None = Field(
        None,
        alias="instance-count",
        description="Number of workspaces that have this tag",
    )
    created_at: datetime | None = Field(
        None, alias="created-at", description="The time this tag was created"
    )
    # Relationships
    organization_name: str | None = Field(
        None, description="The organization name this tag belongs to"
    )


class OrganizationTagsList(BaseModel):
    """Represents a paginated list of organization tags."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[OrganizationTag] = Field(
        default_factory=list, description="List of organization tags"
    )
    current_page: int | None = Field(None, description="Current page number")
    total_pages: int | None = Field(None, description="Total number of pages")
    prev_page: int | str | None = Field(None, description="Previous page number or URL")
    next_page: int | str | None = Field(None, description="Next page number or URL")
    total_count: int | None = Field(None, description="Total number of items")


class OrganizationTagsListOptions(BaseModel):
    """Options for listing organization tags."""

    model_config = ConfigDict(populate_by_name=True)

    page_number: int | None = Field(
        None, alias="page[number]", description="Page number to retrieve", ge=1
    )
    page_size: int | None = Field(
        None, alias="page[size]", description="Number of items per page", ge=1, le=100
    )
    filter: str | None = Field(
        None,
        alias="filter[exclude][taggable][id]",
        description="If specified, omits organization's related workspace's tags",
    )
    query: str | None = Field(
        None,
        alias="q",
        description="A search query string. Organization tags are searchable by name likeness",
    )


class OrganizationTagsDeleteOptions(BaseModel):
    """Options for deleting tags from an organization."""

    model_config = ConfigDict(populate_by_name=True)

    ids: list[str] = Field(
        ..., description="List of tag IDs to delete from the organization"
    )


class AddWorkspacesToTagOptions(BaseModel):
    """Options for adding workspaces to a tag."""

    model_config = ConfigDict(populate_by_name=True)

    workspace_ids: list[str] = Field(
        ..., description="List of workspace IDs to add to the tag"
    )
