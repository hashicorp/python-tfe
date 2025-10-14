from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .policy_set import PolicySet


class PolicySetVersionSource(str, Enum):
    """
    PolicySetVersionSource represents a source type of a policy set version.
    List all available sources for a Policy Set Version.
    """

    POLICY_SET_VERSION_SOURCE_API = "tfe-api"
    POLICY_SET_VERSION_SOURCE_ADO = "ado"
    POLICY_SET_VERSION_SOURCE_BITBUCKET = "bitbucket"
    POLICY_SET_VERSION_SOURCE_GITHUB = "github"
    POLICY_SET_VERSION_SOURCE_GITLAB = "gitlab"


class PolicySetVersionStatus(str, Enum):
    """
    PolicySetVersionStatus represents a policy set version status.
    List all available policy set version statuses.
    """

    POLICY_SET_VERSION_STATUS_ERRORED = "errored"
    POLICY_SET_VERSION_STATUS_INGRESSING = "ingressing"
    POLICY_SET_VERSION_STATUS_PENDING = "pending"
    POLICY_SET_VERSION_STATUS_READY = "ready"


class PolicySetVersionStatusTimestamps(BaseModel):
    """PolicySetVersionStatusTimestamps holds the timestamps for individual policy set version statuses."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    pending_at: datetime | None = Field(None, alias="pending-at")
    ingressing_at: datetime | None = Field(None, alias="ingressing-at")
    ready_at: datetime | None = Field(None, alias="ready-at")
    errored_at: datetime | None = Field(None, alias="errored-at")


class PolicySetIngressAttributes(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    commit_sha: str | None = Field(None, alias="commit-sha")
    commit_url: str | None = Field(None, alias="commit-url")
    identifier: str | None = Field(None, alias="identifier")


class PolicySetVersion(BaseModel):
    """PolicySetVersion represents a Terraform Enterprise Policy Set Version"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    source: PolicySetVersionSource | None = Field(None, alias="source")
    status: PolicySetVersionStatus | None = Field(None, alias="status")
    status_timestamps: PolicySetVersionStatusTimestamps | None = Field(
        None, alias="status-timestamps"
    )
    error_message: str | None = Field(None, alias="error-message")
    error: str | None = Field(None, alias="error")
    created_at: datetime | None = Field(None, alias="created-at")
    updated_at: datetime | None = Field(None, alias="updated-at")
    ingress_attributes: PolicySetIngressAttributes | None = Field(
        None, alias="ingress-attributes"
    )
    policy_set: PolicySet | None = Field(None, alias="policy-set")
    links: dict[str, str] | None = Field(None, alias="links")
