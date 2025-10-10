from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .organization import Organization
from .policy import Policy
from .policy_set_version import PolicySetVersion
from .policy_types import PolicyKind
from .project import Project
from .workspace import VCSRepo, VCSRepoOptions, Workspace


class PolicySetIncludeOpt(str, Enum):
    POLICY_SET_POLICIES = "policies"
    POLICY_SET_WORKSPACES = "workspaces"
    POLICY_SET_PROJECTS = "projects"
    POLICY_SET_NEWEST_VERSION = "newest_version"
    POLICY_SET_CURRENT_VERSION = "current_version"
    POLICY_SET_WORKSPACE_EXCLUSIONS = "workspace_exclusions"


class PolicySet(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    name: str | None = Field(None, alias="name")
    description: str | None = Field(None, alias="description")
    kind: PolicyKind | None = Field(None, alias="kind")
    overridable: bool | None = Field(None, alias="overridable")
    Global: bool | None = Field(None, alias="global")
    policies_path: str | None = Field(None, alias="policies-path")

    # **Note: This field is still in BETA and subject to change.**
    policy_count: int | None = Field(None, alias="policy-count")
    vcs_repo: VCSRepo | None = Field(None, alias="vcs-repo")
    workspace_count: int | None = Field(None, alias="workspace-count")
    project_count: int | None = Field(None, alias="project-count")
    created_at: datetime | None = Field(None, alias="created-at")
    updated_at: datetime | None = Field(None, alias="updated-at")
    agent_enabled: bool | None = Field(None, alias="agent-enabled")
    policy_tool_version: str | None = Field(None, alias="policy-tool-version")

    # Relations
    organization: Organization | None = Field(None, alias="organization")
    workspaces: list[Workspace] = Field(default_factory=list, alias="workspaces")
    projects: list[Project] = Field(default_factory=list, alias="projects")
    policies: list[Policy] = Field(default_factory=list, alias="policies")
    newest_version: PolicySetVersion | None = Field(None, alias="newest-version")
    current_version: PolicySetVersion | None = Field(None, alias="current-version")
    workspace_exclusions: list[Workspace] = Field(
        default_factory=list, alias="workspace-exclusions"
    )


class PolicySetList(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: list[PolicySet] = Field(default_factory=list)
    current_page: int | None = None
    total_pages: int | None = None
    prev_page: int | None = None
    next_page: int | None = None
    total_count: int | None = None


class PolicySetListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    search: str | None = Field(None, alias="search[name]")
    kind: PolicyKind | None = Field(None, alias="filter[kind]")
    include: list[PolicySetIncludeOpt] | None = Field(None, alias="include")
    page_number: int | None = Field(None, alias="page[number]")
    page_size: int | None = Field(None, alias="page[size]")


class PolicySetReadOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[PolicySetIncludeOpt] | None = Field(None, alias="include")


class PolicySetCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str = Field(..., alias="name")
    description: str | None = Field(None, alias="description")
    Global: bool | None = Field(None, alias="global")
    kind: PolicyKind | None = Field(None, alias="kind")
    overridable: bool | None = Field(None, alias="overridable")
    agent_enabled: bool | None = Field(None, alias="agent-enabled")
    policy_tool_version: str | None = Field(None, alias="policy-tool-version")
    policies_path: str | None = Field(None, alias="policies-path")
    policies: list[Policy] | None = Field(None, alias="policies")

    vcs_repo: VCSRepoOptions | None = Field(None, alias="vcs-repo")
    workspaces: list[Workspace] | None = Field(None, alias="workspaces")
    projects: list[Project] | None = Field(None, alias="projects")
    workspace_exclusions: list[Workspace] | None = Field(
        None, alias="workspace-exclusions"
    )


class PolicySetUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str | None = Field(None, alias="name")
    description: str | None = Field(None, alias="description")
    Global: bool | None = Field(None, alias="global")
    overridable: bool | None = Field(None, alias="overridable")
    agent_enabled: bool | None = Field(None, alias="agent-enabled")
    policy_tool_version: str | None = Field(None, alias="policy-tool-version")
    policies_path: str | None = Field(None, alias="policies-path")
    vcs_repo: VCSRepoOptions | None = Field(None, alias="vcs-repo")


class PolicySetAddPoliciesOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    policies: list[Policy] = Field(default_factory=list)


class PolicySetRemovePoliciesOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    policies: list[Policy] = Field(default_factory=list)


class PolicySetAddWorkspacesOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    workspaces: list[Workspace] = Field(default_factory=list)


class PolicySetRemoveWorkspacesOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    workspaces: list[Workspace] = Field(default_factory=list)


class PolicySetAddWorkspaceExclusionsOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    workspace_exclusions: list[Workspace] = Field(default_factory=list)


class PolicySetRemoveWorkspaceExclusionsOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    workspace_exclusions: list[Workspace] = Field(default_factory=list)


class PolicySetAddProjectsOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    projects: list[Project] = Field(default_factory=list)


class PolicySetRemoveProjectsOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    projects: list[Project] = Field(default_factory=list)
