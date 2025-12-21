from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class QueryRunStatus(str, Enum):
    """QueryRunStatus represents the status of a query run operation."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    ERRORED = "errored"
    CANCELED = "canceled"


class QueryRunSource(str, Enum):
    """QueryRunSource represents the source of a query run."""

    API = "tfe-api"


class QueryRunActions(BaseModel):
    """Actions available on a query run."""

    model_config = ConfigDict(populate_by_name=True)

    is_cancelable: bool = Field(
        ..., alias="is-cancelable", description="Whether the query run can be canceled"
    )
    is_force_cancelable: bool = Field(
        ...,
        alias="is-force-cancelable",
        description="Whether the query run can be force canceled",
    )


class QueryRunStatusTimestamps(BaseModel):
    """Timestamps for each status of a query run."""

    model_config = ConfigDict(populate_by_name=True)

    pending_at: datetime | None = Field(
        None, alias="pending-at", description="When the query run was created"
    )
    queued_at: datetime | None = Field(
        None, alias="queued-at", description="When the query run was queued"
    )
    running_at: datetime | None = Field(
        None, alias="running-at", description="When the query run started running"
    )
    finished_at: datetime | None = Field(
        None,
        alias="finished-at",
        description="When the query run finished successfully",
    )
    errored_at: datetime | None = Field(
        None, alias="errored-at", description="When the query run encountered an error"
    )
    canceled_at: datetime | None = Field(
        None, alias="canceled-at", description="When the query run was canceled"
    )


class QueryRunVariable(BaseModel):
    """A variable for a query run."""

    key: str = Field(..., description="Variable key")
    value: str = Field(..., description="Variable value")


class QueryRun(BaseModel):
    """Represents a query run in Terraform Enterprise."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="The unique identifier for this query run")
    type: str = Field(default="queries", description="The type of this resource")
    actions: QueryRunActions | None = Field(
        None, description="Actions available on this query run"
    )
    canceled_at: datetime | None = Field(
        None, alias="canceled-at", description="When the query run was canceled"
    )
    created_at: datetime = Field(
        ..., alias="created-at", description="The time this query run was created"
    )
    updated_at: datetime | None = Field(
        None, alias="updated-at", description="The time this query run was last updated"
    )
    source: QueryRunSource | str = Field(..., description="The source of the query run")
    status: QueryRunStatus = Field(
        ..., description="The current status of the query run"
    )
    status_timestamps: QueryRunStatusTimestamps | None = Field(
        None,
        alias="status-timestamps",
        description="Timestamps for each status of the query run",
    )
    variables: list[QueryRunVariable] | None = Field(
        None, description="Run-specific variable values"
    )
    log_read_url: str | None = Field(
        None, alias="log-read-url", description="URL to retrieve the query run logs"
    )
    # Relationships
    workspace_id: str | None = Field(
        None, description="The workspace ID associated with this query run"
    )
    configuration_version_id: str | None = Field(
        None, description="The configuration version ID used for this query run"
    )
    created_by_id: str | None = Field(
        None, description="The user ID who created this query run"
    )
    canceled_by_id: str | None = Field(
        None, description="The user ID who canceled this query run"
    )


class QueryRunCreateOptions(BaseModel):
    """Options for creating a new query run."""

    model_config = ConfigDict(populate_by_name=True)

    source: QueryRunSource | str = Field(..., description="The source of the query run")
    variables: list[QueryRunVariable] | None = Field(
        None, description="Run-specific variable values"
    )
    workspace_id: str = Field(
        ...,
        alias="workspace-id",
        description="The workspace ID to run the query against",
    )
    configuration_version_id: str | None = Field(
        None,
        alias="configuration-version-id",
        description="The configuration version ID to use for the query",
    )


class QueryRunIncludeOpt(str, Enum):
    """Options for including related resources in query run requests."""

    CREATED_BY = "created_by"
    CONFIGURATION_VERSION = "configuration_version"
    CONFIGURATION_VERSION_INGRESS_ATTRIBUTES = (
        "configuration_version.ingress_attributes"
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
    include: list[QueryRunIncludeOpt] | None = Field(
        None, description="List of related resources to include"
    )


class QueryRunReadOptions(BaseModel):
    """Options for reading a query run with additional data."""

    model_config = ConfigDict(populate_by_name=True)

    include: list[QueryRunIncludeOpt] | None = Field(
        None, description="List of related resources to include"
    )


class QueryRunCancelOptions(BaseModel):
    """Options for canceling a query run."""

    model_config = ConfigDict(populate_by_name=True)

    comment: str | None = Field(
        None, description="Optional comment about why the query run was canceled"
    )


class QueryRunForceCancelOptions(BaseModel):
    """Options for force canceling a query run."""

    model_config = ConfigDict(populate_by_name=True)

    comment: str | None = Field(
        None, description="Optional comment about why the query run was force canceled"
    )


class QueryRunList(BaseModel):
    """Represents a paginated list of query runs."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[QueryRun] = Field(
        default_factory=list, description="List of query runs"
    )
    current_page: int | None = Field(None, description="Current page number")
    total_pages: int | None = Field(None, description="Total number of pages")
    prev_page: int | str | None = Field(None, description="Previous page number or URL")
    next_page: int | str | None = Field(None, description="Next page number or URL")
    total_count: int | None = Field(None, description="Total number of items")
