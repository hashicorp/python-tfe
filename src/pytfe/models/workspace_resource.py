"""Workspace resources models for Terraform Enterprise."""

from pydantic import BaseModel, ConfigDict, Field

from ..models.common import Pagination


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


class WorkspaceResourcesList(BaseModel):
    """List of workspace resources with pagination information."""

    model_config = ConfigDict(extra="forbid")

    data: list[WorkspaceResource] = Field(
        default_factory=list, description="List of workspace resources"
    )
    pagination: Pagination | None = None
