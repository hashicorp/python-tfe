from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    pass


class TokenType(str, Enum):
    """Token type enumeration."""

    AUDIT_TRAILS = "audit-trails"


class OrganizationToken(BaseModel):
    """Organization token represents a Terraform Enterprise organization token."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Organization token ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    description: str = Field("", description="Token description")
    last_used_at: datetime | None = Field(None, description="Last usage timestamp")
    token: str = Field("", description="The actual token value")
    expired_at: datetime | None = Field(None, description="Token expiration timestamp")
    created_by: Any | None = Field(
        None, description="The entity that created this token"
    )


class OrganizationTokenCreateOptions(BaseModel):
    """Options for creating an organization token."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    expired_at: datetime | None = Field(
        None,
        description="The token's expiration date. Available in TFE release v202305-1 and later",
    )
    token_type: TokenType | None = Field(
        None,
        alias="token",
        description="What type of token to create. Only applicable to HCP Terraform",
    )


class OrganizationTokenReadOptions(BaseModel):
    """Options for reading an organization token."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    token_type: TokenType | None = Field(
        None,
        alias="token",
        description="What type of token to read. Only applicable to HCP Terraform",
    )


class OrganizationTokenDeleteOptions(BaseModel):
    """Options for deleting an organization token."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    token_type: TokenType | None = Field(
        None,
        alias="token",
        description="What type of token to delete. Only applicable to HCP Terraform",
    )
