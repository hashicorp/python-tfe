"""Workspace resources models for Terraform Enterprise."""

from pydantic import BaseModel


class WorkspaceResource(BaseModel):
    """Represents a Terraform Enterprise workspace resource.

    These are resources managed by Terraform in a workspace's state.
    """

    id: str
    address: str
    name: str
    created_at: str
    updated_at: str
    module: str
    provider: str
    provider_type: str
    modified_by_state_version_id: str
    name_index: str | None = None


class WorkspaceResourceListOptions(BaseModel):
    """Options for listing workspace resources."""

    # Pagination
    page_number: int | None = None
    page_size: int | None = None
