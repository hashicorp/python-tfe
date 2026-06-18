# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class IPRange(BaseModel):
    """HCP Terraform / Terraform Enterprise outbound IP ranges (CIDR notation).

    Returned by ``GET /api/meta/ip-ranges``. This is a bare JSON object (not a
    JSON:API resource), so it inherits ``BaseModel`` rather than ``TFEModel``.
    The published ranges for each feature may overlap.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    api: list[str] = Field(default_factory=list)
    notifications: list[str] = Field(default_factory=list)
    sentinel: list[str] = Field(default_factory=list)
    vcs: list[str] = Field(default_factory=list)
