from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SSHKey(BaseModel):
    """Represents an SSH key in Terraform Enterprise."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="The unique identifier for this SSH key")
    type: str = Field(default="ssh-keys", description="The type of this resource")
    name: str = Field(..., description="A name to identify the SSH key")


class SSHKeyCreateOptions(BaseModel):
    """Options for creating a new SSH key."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="A name to identify the SSH key")
    value: str = Field(..., description="The text of the SSH private key")


class SSHKeyUpdateOptions(BaseModel):
    """Options for updating an SSH key."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(None, description="A name to identify the SSH key")


class SSHKeyListOptions(BaseModel):
    """Options for listing SSH keys."""

    model_config = ConfigDict(populate_by_name=True)

    page_number: int | None = Field(
        None, alias="page[number]", description="Page number to retrieve", ge=1
    )
    page_size: int | None = Field(
        None, alias="page[size]", description="Number of items per page", ge=1, le=100
    )


class SSHKeyList(BaseModel):
    """Represents a paginated list of SSH keys."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[SSHKey] = Field(default_factory=list, description="List of SSH keys")
    current_page: int | None = Field(None, description="Current page number")
    total_pages: int | None = Field(None, description="Total number of pages")
    prev_page: str | None = Field(None, description="URL of the previous page")
    next_page: str | None = Field(None, description="URL of the next page")
    total_count: int | None = Field(None, description="Total number of items")
