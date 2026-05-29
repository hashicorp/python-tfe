# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .run import RunStatus


class AdminRunListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    run_status: str | None = Field(default=None, alias="filter[status]")
    query: str | None = Field(default=None, alias="q")
    page_number: int | None = Field(default=None, alias="page[number]")
    page_size: int | None = Field(default=None, alias="page[size]")


class AdminRun(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    id: str | None = None
    status: RunStatus | None = None
    has_changes: bool | None = Field(default=None, alias="has-changes")
    plan_only: bool | None = Field(default=None, alias="plan-only")
    # Populated from the `workspace` relationship (always present).
    workspace_id: str | None = None
    # Populated only when `?include=workspace.organization` is passed.
    organization_name: str | None = None
