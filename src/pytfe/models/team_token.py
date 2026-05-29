# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .organization import Organization
from .team import Team
from .user import User


class TeamToken(BaseModel):
    """TeamToken represents a Terraform Enterprise team token."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    created_at: datetime | None = Field(default=None, alias="created-at")
    last_used_at: datetime | None = Field(default=None, alias="last-used-at")
    description: str | None = Field(default=None, alias="description")
    token: str | None = Field(default=None, alias="token")
    expired_at: datetime | None = Field(default=None, alias="expired-at")

    # Relations
    team: Team | None = None
    created_by: CreatedByChoice | None = Field(default=None, alias="created-by")


class TeamTokenCreateOptions(BaseModel):
    """TeamTokenCreateOptions contains the options for creating a team token."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    description: str | None = Field(default=None, alias="description")
    expired_at: datetime | None = Field(default=None, alias="expired-at")


class TeamTokenListOptions(BaseModel):
    """TeamTokenListOptions contains the options for listing team tokens."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    query: str | None = Field(default=None, alias="q")
    sort: str | None = Field(default=None, alias="sort")


class CreatedByChoice(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    organization: Organization | None = None
    user: User | None = None
    team: Team | None = None
