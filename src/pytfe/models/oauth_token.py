from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .oauth_client import OAuthClient


class OAuthToken(BaseModel):
    """OAuth token represents a VCS configuration including the associated OAuth token."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="OAuth token ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    has_ssh_key: bool = Field(..., description="Whether the token has an SSH key")
    service_provider_user: str = Field(..., description="Service provider user")

    # Relationships
    oauth_client: OAuthClient | None = Field(
        None, description="The associated OAuth client"
    )


class OAuthTokenListOptions(BaseModel):
    """Options for listing OAuth tokens."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]", description="Page size")


class OAuthTokenUpdateOptions(BaseModel):
    """Options for updating an OAuth token."""

    model_config = ConfigDict(extra="forbid")

    private_ssh_key: str | None = Field(
        None, description="A private SSH key to be used for git clone operations"
    )


# Rebuild models to resolve forward references
try:
    from .oauth_client import OAuthClient  # noqa: F401

    OAuthToken.model_rebuild()
except ImportError:
    # If OAuthClient is not available, create a dummy class
    pass
