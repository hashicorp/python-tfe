# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Models for IP allowlists (JSON:API ``cidr-range-lists`` / ``cidr-ranges``).

HCP Terraform's "IP allowlist" feature is exposed on the wire as two JSON:API
resources: ``cidr-range-lists`` (the allowlist itself) and ``cidr-ranges`` (the
CIDR blocks it contains).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import RequiredCIDRBlockError, RequiredNameError
from ..utils import valid_string
from ._base import TFEModel


class EnforcementScope(str, Enum):
    """Where an IP allowlist applies.

    Wire values use underscores (per the API request body and sample payloads).
    """

    ORGANIZATION = "organization"
    ALL_AGENT_POOLS = "all_agent_pools"
    SELECTED_AGENT_POOLS = "selected_agent_pools"


class CIDRRange(TFEModel):
    """A single CIDR block belonging to an IP allowlist.

    The CIDR value is sent and returned on the wire as ``range``; it is exposed
    here as ``cidr_block`` for clarity (and to avoid shadowing the ``range``
    builtin).
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    cidr_block: str | None = Field(default=None, alias="range")
    description: str | None = Field(default=None)
    enabled: bool | None = Field(default=None)
    updated_at: datetime | None = Field(default=None, alias="updated-at")


class CIDRRangeList(TFEModel):
    """An IP allowlist (a named, scoped set of CIDR ranges)."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    enforcement_scope: EnforcementScope | None = Field(
        default=None, alias="enforcement-scope"
    )
    cidr_ranges: list[CIDRRange] | None = Field(default=None, alias="cidr-ranges")
    updated_at: datetime | None = Field(default=None, alias="updated-at")


class CIDRRangeListCreateOptions(BaseModel):
    """Options for creating an IP allowlist."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )

    name: str = Field(..., description="Name of the IP allowlist.")
    description: str | None = Field(default=None)
    enforcement_scope: EnforcementScope | None = Field(
        default=None, alias="enforcement-scope"
    )

    @model_validator(mode="after")
    def valid(self) -> CIDRRangeListCreateOptions:
        if not valid_string(self.name):
            raise RequiredNameError()
        return self


class CIDRRangeListUpdateOptions(BaseModel):
    """Options for updating an IP allowlist. Omitted fields are preserved."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )

    name: str | None = Field(default=None)
    description: str | None = Field(default=None)
    enforcement_scope: EnforcementScope | None = Field(
        default=None, alias="enforcement-scope"
    )


class CIDRRangeListListOptions(BaseModel):
    """Options for listing IP allowlists in an organization."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )

    q: str | None = Field(default=None, description="Case-insensitive name search.")
    page_number: int | None = Field(default=None, alias="page[number]")
    page_size: int | None = Field(default=None, alias="page[size]")


class CIDRRangeCreateOptions(BaseModel):
    """Options for adding a CIDR range to an IP allowlist."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )

    cidr_block: str = Field(
        ..., alias="range", description='A CIDR block (e.g. "192.168.1.0/24").'
    )
    description: str | None = Field(default=None)
    enabled: bool | None = Field(default=None)

    @model_validator(mode="after")
    def valid(self) -> CIDRRangeCreateOptions:
        if not valid_string(self.cidr_block):
            raise RequiredCIDRBlockError()
        return self


class CIDRRangeUpdateOptions(BaseModel):
    """Options for updating a CIDR range. Omitted fields are preserved."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )

    cidr_block: str | None = Field(default=None, alias="range")
    description: str | None = Field(default=None)
    enabled: bool | None = Field(default=None)
