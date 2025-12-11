from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReservedTagKey(BaseModel):
    """Represents a reserved tag key in Terraform Enterprise."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="The unique identifier for this reserved tag key")
    type: str = Field(
        default="reserved-tag-keys", description="The type of this resource"
    )
    key: str = Field(..., description="The key targeted by this reserved tag key")
    disable_overrides: bool = Field(
        ...,
        alias="disable-overrides",
        description="If true, disables overriding inherited tags with the specified key at the workspace level",
    )
    created_at: datetime | None = Field(
        None,
        alias="created-at",
        description="The time when the reserved tag key was created",
    )
    updated_at: datetime | None = Field(
        None,
        alias="updated-at",
        description="The time when the reserved tag key was last updated",
    )


class ReservedTagKeyCreateOptions(BaseModel):
    """Options for creating a new reserved tag key."""

    model_config = ConfigDict(populate_by_name=True)

    key: str = Field(..., description="The key targeted by this reserved tag key")
    disable_overrides: bool = Field(
        ...,
        alias="disable-overrides",
        description="If true, disables overriding inherited tags with the specified key at the workspace level",
    )


class ReservedTagKeyUpdateOptions(BaseModel):
    """Options for updating a reserved tag key."""

    model_config = ConfigDict(populate_by_name=True)

    key: str | None = Field(
        None, description="The key targeted by this reserved tag key"
    )
    disable_overrides: bool | None = Field(
        None,
        alias="disable-overrides",
        description="If true, disables overriding inherited tags with the specified key at the workspace level",
    )


class ReservedTagKeyListOptions(BaseModel):
    """Options for listing reserved tag keys."""

    model_config = ConfigDict(populate_by_name=True)

    page_size: int | None = Field(
        None, alias="page[size]", description="Number of items per page", ge=1, le=100
    )
