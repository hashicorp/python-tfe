# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AdminWorkspaceListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    query: str | None = Field(default=None, alias="q")
    page_number: int | None = Field(default=None, alias="page[number]")
    page_size: int | None = Field(default=None, alias="page[size]")


class AdminWorkspace(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    id: str | None = None
    name: str | None = None
    locked: bool | None = None
    execution_mode: str | None = Field(default=None, alias="execution-mode")
    organization_name: str | None = None
    current_run_id: str | None = None
