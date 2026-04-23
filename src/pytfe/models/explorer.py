# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Pydantic models for the Explorer API (query options, rows, saved views).

Aliases mirror JSON:API and Explorer query-string names (type, page[number], etc.).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExplorerViewType(str, Enum):
    """Explorer `type` / `query-type` discriminator (see product docs for supported views)."""

    WORKSPACES = "workspaces"
    TF_VERSIONS = "tf_versions"
    PROVIDERS = "providers"
    MODULES = "modules"
    RESOURCES = "resources"  # Present when the deployment exposes a resources view.


class ExplorerUrlFilter(BaseModel):
    """One slot in ExplorerQueryOptions.filters → filter[i][field][op][idx] query keys."""

    index: int = Field(..., ge=0, description="Filter index in the query string")
    field: str = Field(
        ..., min_length=1, description="Explorer field name in snake_case"
    )
    operator: str = Field(..., min_length=1, description="Explorer filter operator")
    value: str = Field(..., description="Filter value")
    value_index: int = Field(
        0,
        ge=0,
        description="Reserved index for filter value; currently expected as zero",
    )


class ExplorerQueryOptions(BaseModel):
    """GET /organizations/{org}/explorer (and export/csv) query string as structured fields."""

    model_config = ConfigDict(populate_by_name=True)

    view_type: ExplorerViewType = Field(..., alias="type")
    sort: str | None = Field(
        None,
        description="Sort field (snake_case); prefix with '-' for descending order",
    )
    fields: str | None = Field(
        None,
        description="Comma-separated list of fields to include in each row",
    )
    page_number: int | None = Field(None, alias="page[number]", ge=1)
    page_size: int | None = Field(None, alias="page[size]", ge=1, le=100)
    filters: list[ExplorerUrlFilter] | None = Field(
        None,
        description="Expanded filter objects mapped to filter[index][field][operator][value_index]",
    )


class ExplorerRow(BaseModel):
    """One Explorer result row: json:api id/type plus flat attributes for the view."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    row_type: str = Field(..., alias="type")
    attributes: dict[str, Any] = Field(default_factory=dict)


class ExplorerSavedQueryFilter(BaseModel):
    """One saved-view filter row (list-valued `value` matches create/update JSON)."""

    field: str = Field(..., min_length=1)
    operator: str = Field(..., min_length=1)
    value: list[str] = Field(default_factory=list)


class ExplorerSavedQuery(BaseModel):
    """Nested query on a saved view: view type, filters, optional fields and sort lists."""

    model_config = ConfigDict(populate_by_name=True)

    query_type: ExplorerViewType = Field(..., alias="type")
    filter: list[ExplorerSavedQueryFilter] | None = None
    fields: list[str] | None = None
    sort: list[str] | None = None


class ExplorerSavedView(BaseModel):
    """Saved view resource: metadata plus embedded query (response and some request paths)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    created_at: datetime | None = Field(None, alias="created-at")
    query: ExplorerSavedQuery = Field(...)
    query_type: ExplorerViewType = Field(..., alias="query-type")


class ExplorerSavedViewCreateOptions(BaseModel):
    """POST .../explorer/views attributes: display name, top-level query-type, nested query."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1)
    query_type: ExplorerViewType = Field(..., alias="query-type")
    query: ExplorerSavedQuery


class ExplorerSavedViewUpdateOptions(BaseModel):
    """PATCH .../explorer/views/{id} attributes: name and full replacement query."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1)
    query: ExplorerSavedQuery
