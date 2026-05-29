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
    # vcs-repo is an attribute object; only the identifier is surfaced here.
    vcs_repo_identifier: str | None = None
    # Lifted from the `organization` relationship at parse time.
    organization_name: str | None = None
    # Lifted from the `current-run` relationship at parse time.
    current_run_id: str | None = None
