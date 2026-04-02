# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .agent import AgentPool
from .common import TagBinding
from .organization import Organization


class Project(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    name: str | None = Field(default=None, alias="name")
    description: str | None = Field(default=None, alias="description")
    created_at: str | None = Field(default=None, alias="created-at")
    updated_at: str | None = Field(default=None, alias="updated-at")
    workspace_count: int = Field(default=0, alias="workspace-count")
    default_execution_mode: str = Field(
        default="remote", alias="default-execution-mode"
    )
    auto_destroy_activity_duration: str | None = Field(
        default=None, alias="auto-destroy-activity-duration"
    )
    setting_overwrites: ProjectSettingOverwrites | None = Field(
        default=None, alias="setting-overwrites"
    )

    # relations
    default_agent_pool: AgentPool | None = Field(
        default=None, alias="default-agent-pool"
    )
    organization: Organization | None = Field(default=None, alias="organization")


class ProjectListOptions(BaseModel):
    """Options for listing projects"""

    # Optional: String used to filter results by complete project name
    name: str | None = None
    # Optional: Query string to search projects by names
    query: str | None = None
    # Optional: Include related resources
    include: list[str] | None = None
    # Pagination options
    page_size: int | None = None


class ProjectCreateOptions(BaseModel):
    """Options for creating a project"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Required: A name to identify the project
    name: str
    # Optional: A description for the project
    description: str | None = Field(default=None, alias="description")
    auto_destroy_activity_duration: str | None = Field(
        default=None,
        alias="auto-destroy-activity-duration",
    )
    default_execution_mode: str | None = Field(
        default="remote", alias="default-execution-mode"
    )
    # Optional: DefaultAgentPoolID default agent pool for workspaces in the project,
    # required when DefaultExecutionMode is set to `agent`
    default_agent_pool_id: str | None = Field(
        default=None,
        alias="default-agent-pool-id",
    )
    setting_overwrites: ProjectSettingOverwrites | None = Field(
        default=None,
        alias="setting-overwrites",
    )
    tag_bindings: list[TagBinding] | None = Field(
        default_factory=list, alias="tag-bindings"
    )


class ProjectUpdateOptions(BaseModel):
    """Options for updating a project"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Optional: A name to identify the project
    name: str | None = None
    # Optional: A description for the project
    description: str | None = Field(default=None, alias="description")
    auto_destroy_activity_duration: str | None = Field(
        default=None,
        alias="auto-destroy-activity-duration",
    )
    default_execution_mode: str | None = Field(
        default="remote", alias="default-execution-mode"
    )
    # Optional: DefaultAgentPoolID default agent pool for workspaces in the project,
    # required when DefaultExecutionMode is set to `agent`
    default_agent_pool_id: str | None = Field(
        default=None,
        alias="default-agent-pool-id",
    )
    setting_overwrites: ProjectSettingOverwrites | None = Field(
        default=None,
        alias="setting-overwrites",
    )
    tag_bindings: list[TagBinding] | None = Field(
        default_factory=list, alias="tag-bindings"
    )


class ProjectAddTagBindingsOptions(BaseModel):
    """Options for adding tag bindings to a project"""

    tag_bindings: list[TagBinding] = Field(default_factory=list)


class ProjectSettingOverwrites(BaseModel):
    """Options for overwriting project settings"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    execution_mode: bool | None = Field(alias="default-execution-mode")
    agent_pool: bool | None = Field(alias="default-agent-pool")
