# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import ERR_REQUIRED_NAME, ERR_REQUIRED_PROJECT
from .agent import AgentPool
from .project import Project


class StackSortColumn(str, Enum):
    """StackSortColumn represents a string that can be used to sort items when using the List method."""

    STACK_SORT_BY_NAME = "name"
    STACK_SORT_BY_UPDATED_AT = "updated-at"
    STACK_SORT_BY_NAME_DESC = "-name"
    STACK_SORT_BY_UPDATED_AT_DESC = "-updated-at"


class StackVcsRepo(BaseModel):
    """StackVCSRepo represents the version control system repository for a stack."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    identifier: str = Field(alias="identifier")
    branch: str | None = Field(default=None, alias="branch")
    gha_installation_id: str | None = Field(
        default=None, alias="github-app-installation-id"
    )
    oauth_token_id: str | None = Field(default=None, alias="oauth-token-id")


class StackVcsRepoOptions(BaseModel):
    """StackVCSRepoOptions represents the options for the version control system repository for a stack."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    identifier: str = Field(alias="identifier")
    branch: str | None = Field(default=None, alias="branch")
    gha_installation_id: str | None = Field(
        default=None, alias="github-app-installation-id"
    )
    oauth_token_id: str | None = Field(default=None, alias="oauth-token-id")


class Stack(BaseModel):
    """Stack represents a stack in Terraform Cloud."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    name: str | None = Field(default=None, alias="name")
    description: str | None = Field(default=None, alias="description")
    created_at: datetime | None = Field(default=None, alias="created-at")
    updated_at: datetime | None = Field(default=None, alias="updated-at")
    vcs_repo: StackVcsRepo | None = Field(default=None, alias="vcs-repo")
    speculation_enabled: bool | None = Field(default=None, alias="speculation-enabled")
    upstream_count: int | None = Field(default=None, alias="upstream-count")
    downstream_count: int | None = Field(default=None, alias="downstream-count")
    inputs_count: int | None = Field(default=None, alias="inputs-count")
    outputs_count: int | None = Field(default=None, alias="outputs-count")
    creation_source: str | None = Field(default=None, alias="creation-source")

    # Relations
    project: Project | None = Field(default=None, alias="project")
    agent_pool: AgentPool | None = Field(default=None, alias="agent-pool")
    # latest_stack_configuration: dict[str, Any] | None = Field(default=None, alias="latest-stack-configuration")


class StackListOptions(BaseModel):
    """StackListOptions represents the options for listing stacks."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    project_id: str | None = Field(default=None, alias="filter[project][id]")
    sort: StackSortColumn | None = Field(default=None, alias="sort")
    search_by_name: str | None = Field(default=None, alias="search[name]")


class StackCreateOptions(BaseModel):
    """StackCreateOptions represents the options for creating a stack."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str = Field(alias="name")
    migration: bool | None = Field(default=None, alias="migration")
    description: str | None = Field(default=None, alias="description")
    speculation_enabled: bool | None = Field(default=None, alias="speculation-enabled")
    vcs_repo: StackVcsRepoOptions | None = Field(default=None, alias="vcs-repo")
    project: Project = Field(alias="project")
    agent_pool: AgentPool | None = Field(default=None, alias="agent-pool")

    @model_validator(mode="after")
    def valid(self) -> StackCreateOptions:
        if self.name == "":
            raise ValueError(ERR_REQUIRED_NAME)

        if self.project and self.project.id == "":
            raise ValueError(ERR_REQUIRED_PROJECT)

        return self


class StackUpdateOptions(BaseModel):
    """StackUpdateOptions represents the options for updating a stack."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str | None = Field(default=None, alias="name")
    description: str | None = Field(default=None, alias="description")
    speculation_enabled: bool | None = Field(default=None, alias="speculation-enabled")
    vcs_repo: StackVcsRepoOptions | None = Field(default=None, alias="vcs-repo")
    project: Project | None = Field(default=None, alias="project")
    agent_pool: AgentPool | None = Field(default=None, alias="agent-pool")
