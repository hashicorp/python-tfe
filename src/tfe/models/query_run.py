from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QueryRunStatus(str, Enum):
    """QueryRunStatus represents the status of a query run operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERRORED = "errored"
    CANCELED = "canceled"


class QueryRunType(str, Enum):
    """QueryRunType represents different types of query runs."""

    FILTER = "filter"
    SEARCH = "search"
    ANALYTICS = "analytics"


class QueryRun(BaseModel):
    """Represents a query run in Terraform Enterprise."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="The unique identifier for this query run")
    type: str = Field(default="query-runs", description="The type of this resource")
    query: str = Field(..., description="The query string used for this run")
    query_type: QueryRunType = Field(
        ..., alias="query-type", description="The type of query being executed"
    )
    status: QueryRunStatus = Field(
        ..., description="The current status of the query run"
    )
    results_count: int | None = Field(
        None, alias="results-count", description="The number of results returned"
    )
    created_at: datetime = Field(
        ..., alias="created-at", description="The time this query run was created"
    )
    updated_at: datetime = Field(
        ..., alias="updated-at", description="The time this query run was last updated"
    )
    started_at: datetime | None = Field(
        None, alias="started-at", description="The time this query run was started"
    )
    finished_at: datetime | None = Field(
        None, alias="finished-at", description="The time this query run was finished"
    )
    error_message: str | None = Field(
        None, alias="error-message", description="Error message if the query run failed"
    )
    logs_url: str | None = Field(
        None, alias="logs-url", description="URL to retrieve the query run logs"
    )
    results_url: str | None = Field(
        None, alias="results-url", description="URL to retrieve the query run results"
    )
    workspace_id: str | None = Field(
        None,
        alias="workspace-id",
        description="The workspace ID if query is workspace-scoped",
    )
    organization_name: str | None = Field(
        None, alias="organization-name", description="The organization name"
    )
    timeout_seconds: int | None = Field(
        None, alias="timeout-seconds", description="Query timeout in seconds"
    )
    max_results: int | None = Field(
        None, alias="max-results", description="Maximum number of results to return"
    )


class QueryRunCreateOptions(BaseModel):
    """Options for creating a new query run."""

    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(..., description="The query string to execute")
    query_type: QueryRunType = Field(
        ..., alias="query-type", description="The type of query being executed"
    )
    workspace_id: str | None = Field(
        None,
        alias="workspace-id",
        description="The workspace ID if query is workspace-scoped",
    )
    organization_name: str | None = Field(
        None, alias="organization-name", description="The organization name"
    )
    timeout_seconds: int | None = Field(
        None,
        alias="timeout-seconds",
        description="Query timeout in seconds",
        gt=0,
        le=3600,
    )
    max_results: int | None = Field(
        None,
        alias="max-results",
        description="Maximum number of results to return",
        gt=0,
        le=10000,
    )
    filters: dict[str, Any] | None = Field(
        None, description="Additional filters to apply to the query"
    )


class QueryRunListOptions(BaseModel):
    """Options for listing query runs."""

    model_config = ConfigDict(populate_by_name=True)

    page_number: int | None = Field(
        None, alias="page[number]", description="Page number to retrieve", ge=1
    )
    page_size: int | None = Field(
        None, alias="page[size]", description="Number of items per page", ge=1, le=100
    )
    query_type: QueryRunType | None = Field(
        None, alias="filter[query-type]", description="Filter by query type"
    )
    status: QueryRunStatus | None = Field(
        None, alias="filter[status]", description="Filter by status"
    )
    workspace_id: str | None = Field(
        None, alias="filter[workspace-id]", description="Filter by workspace ID"
    )
    organization_name: str | None = Field(
        None,
        alias="filter[organization-name]",
        description="Filter by organization name",
    )


class QueryRunReadOptions(BaseModel):
    """Options for reading a query run with additional data."""

    model_config = ConfigDict(populate_by_name=True)

    include_results: bool | None = Field(
        None, alias="include[results]", description="Include query results in response"
    )
    include_logs: bool | None = Field(
        None, alias="include[logs]", description="Include query logs in response"
    )


class QueryRunCancelOptions(BaseModel):
    """Options for canceling a query run."""

    model_config = ConfigDict(populate_by_name=True)

    reason: str | None = Field(None, description="Reason for canceling the query run")


class QueryRunForceCancelOptions(BaseModel):
    """Options for force canceling a query run."""

    model_config = ConfigDict(populate_by_name=True)

    reason: str | None = Field(
        None, description="Reason for force canceling the query run"
    )


class QueryRunList(BaseModel):
    """Represents a paginated list of query runs."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[QueryRun] = Field(
        default_factory=list, description="List of query runs"
    )
    current_page: int | None = Field(None, description="Current page number")
    total_pages: int | None = Field(None, description="Total number of pages")
    prev_page: str | None = Field(None, description="URL of the previous page")
    next_page: str | None = Field(None, description="URL of the next page")
    total_count: int | None = Field(None, description="Total number of items")


class QueryRunResults(BaseModel):
    """Represents the results of a query run."""

    model_config = ConfigDict(populate_by_name=True)

    query_run_id: str = Field(..., description="The ID of the query run")
    results: list[dict[str, Any]] = Field(
        default_factory=list, description="The query results"
    )
    total_count: int = Field(..., description="Total number of results")
    truncated: bool = Field(
        False, description="Whether the results were truncated due to limits"
    )


class QueryRunLogs(BaseModel):
    """Represents the logs of a query run."""

    model_config = ConfigDict(populate_by_name=True)

    query_run_id: str = Field(..., description="The ID of the query run")
    logs: str = Field(..., description="The query run logs")
    log_level: str | None = Field(None, description="The log level")
    timestamp: datetime | None = Field(None, description="When the logs were generated")
