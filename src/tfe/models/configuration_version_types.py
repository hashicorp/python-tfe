from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ConfigurationStatus(str, Enum):
    """Configuration version status enumeration."""

    ARCHIVED = "archived"
    ERRORED = "errored"
    FETCHING = "fetching"
    PENDING = "pending"
    UPLOADED = "uploaded"


class ConfigurationSource(str, Enum):
    """Configuration version source enumeration."""

    API = "tfe-api"
    BITBUCKET = "bitbucket"
    GITHUB = "github"
    GITLAB = "gitlab"
    ADO = "ado"
    TERRAFORM = "terraform"


class ConfigVerIncludeOpt(str, Enum):
    """Configuration version include options."""

    INGRESS_ATTRIBUTES = "ingress_attributes"


class IngressAttributes(BaseModel):
    """Ingress attributes model."""

    branch: str | None = None
    clone_url: str | None = Field(alias="clone-url", default=None)
    commit_message: str | None = Field(alias="commit-message", default=None)
    commit_sha: str | None = Field(alias="commit-sha", default=None)
    commit_url: str | None = Field(alias="commit-url", default=None)
    compare_url: str | None = Field(alias="compare-url", default=None)
    identifier: str | None = None
    is_pull_request: bool | None = Field(alias="is-pull-request", default=None)
    on_default_branch: bool | None = Field(alias="on-default-branch", default=None)
    pull_request_number: int | None = Field(alias="pull-request-number", default=None)
    pull_request_url: str | None = Field(alias="pull-request-url", default=None)
    pull_request_title: str | None = Field(alias="pull-request-title", default=None)
    pull_request_body: str | None = Field(alias="pull-request-body", default=None)
    tag: str | None = None
    sender_username: str | None = Field(alias="sender-username", default=None)
    sender_avatar_url: str | None = Field(alias="sender-avatar-url", default=None)
    sender_html_url: str | None = Field(alias="sender-html-url", default=None)

    model_config = {"populate_by_name": True}


class ConfigurationVersion(BaseModel):
    """Configuration version model."""

    id: str
    auto_queue_runs: bool = Field(alias="auto-queue-runs")
    error: str | None = None
    error_message: str | None = Field(alias="error-message", default=None)
    source: ConfigurationSource
    speculative: bool = False
    status: ConfigurationStatus
    status_timestamps: dict[str, str] | None = Field(
        alias="status-timestamps", default=None
    )
    provisional: bool = False
    upload_url: str | None = Field(alias="upload-url", default=None)

    # Relations
    ingress_attributes: IngressAttributes | None = Field(
        alias="ingress-attributes", default=None
    )

    # Links
    links: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class ConfigurationVersionList(BaseModel):
    """Configuration version list response."""

    items: list[ConfigurationVersion]
    pagination: dict[str, Any] | None = None


class ConfigurationVersionListOptions(BaseModel):
    """Options for listing configuration versions."""

    # Pagination options
    page_number: int | None = Field(alias="page[number]", default=None)
    page_size: int | None = Field(alias="page[size]", default=None)

    # Include related resources
    include: list[ConfigVerIncludeOpt] | None = None

    model_config = {"populate_by_name": True}


class ConfigurationVersionCreateOptions(BaseModel):
    """Options for creating a configuration version."""

    # Optional: When true, runs are queued automatically when the configuration version is uploaded
    auto_queue_runs: bool | None = Field(alias="auto-queue-runs", default=None)

    # Optional: When true, this configuration version can only be used for planning
    speculative: bool | None = None

    # Optional: When true, this configuration version is provisional
    provisional: bool | None = None

    model_config = {"populate_by_name": True}


class ConfigurationVersionReadOptions(BaseModel):
    """Options for reading a configuration version."""

    # Include related resources
    include: list[ConfigVerIncludeOpt] | None = None


# Upload-related classes
class ConfigurationVersionUpload(BaseModel):
    """Configuration version upload response."""

    upload_url: str = Field(alias="upload-url")

    model_config = {"populate_by_name": True}
