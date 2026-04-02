# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .agent import AgentPool
from .common import EffectiveTagBinding, Pagination, Tag, TagBinding
from .data_retention_policy import DataRetentionPolicyChoice
from .organization import ExecutionMode, Organization
from .project import Project


class Workspace(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str = Field(
        json_schema_extra={"jsonapi_type": "primary", "jsonapi_name": "workspaces"}
    )
    name: str | None = Field(None, alias="name")

    # Core attributes
    actions: WorkspaceActions | None = Field(None, alias="actions")
    allow_destroy_plan: bool | None = Field(None, alias="allow-destroy-plan")
    assessments_enabled: bool | None = Field(None, alias="assessments-enabled")
    auto_apply: bool | None = Field(None, alias="auto-apply")
    auto_apply_run_trigger: bool | None = Field(None, alias="auto-apply-run-trigger")
    auto_destroy_at: datetime | None = Field(None, alias="auto-destroy-at")
    auto_destroy_activity_duration: str | None = Field(
        None, alias="auto-destroy-activity-duration"
    )
    can_queue_destroy_plan: bool | None = Field(None, alias="can-queue-destroy-plan")
    created_at: datetime | None = Field(None, alias="created-at")
    description: str | None = Field(None, alias="description")
    environment: str | None = Field(None, alias="environment")
    execution_mode: ExecutionMode | None = Field(None, alias="execution-mode")
    file_triggers_enabled: bool | None = Field(None, alias="file-triggers-enabled")
    global_remote_state: bool | None = Field(None, alias="global-remote-state")
    inherits_project_auto_destroy: bool | None = Field(
        None, alias="inherits-project-auto-destroy"
    )
    locked: bool | None = Field(None, alias="locked")
    migration_environment: str | None = Field(None, alias="migration-environment")
    no_code_upgrade_available: bool | None = Field(
        None, alias="no-code-upgrade-available"
    )
    operations: bool | None = Field(None, alias="operations")
    permissions: WorkspacePermissions | None = Field(None, alias="permissions")
    queue_all_runs: bool | None = Field(None, alias="queue-all-runs")
    speculative_enabled: bool | None = Field(None, alias="speculative-enabled")
    source: WorkspaceSource | None = Field(None, alias="source")
    source_name: str | None = Field(None, alias="source-name")
    source_url: str | None = Field(None, alias="source-url")
    structured_run_output_enabled: bool | None = Field(
        None, alias="structured-run-output-enabled"
    )
    terraform_version: str | None = Field(None, alias="terraform-version")
    trigger_prefixes: list[str] = Field(default_factory=list, alias="trigger-prefixes")
    trigger_patterns: list[str] = Field(default_factory=list, alias="trigger-patterns")
    vcs_repo: VCSRepo | None = Field(None, alias="vcs-repo")
    working_directory: str | None = Field(None, alias="working-directory")
    updated_at: datetime | None = Field(None, alias="updated-at")
    resource_count: int | None = Field(None, alias="resource-count")
    apply_duration_average: float | None = Field(None, alias="apply-duration-average")
    plan_duration_average: float | None = Field(None, alias="plan-duration-average")
    policy_check_failures: int | None = Field(None, alias="policy-check-failures")
    run_failures: int | None = Field(None, alias="run-failures")
    runs_count: int | None = Field(None, alias="workspace-kpis-runs-count")
    tag_names: list[str] = Field(default_factory=list, alias="tag-names")
    setting_overwrites: WorkspaceSettingOverwrites | None = Field(
        None, alias="setting-overwrites"
    )

    # Relations
    agent_pool: AgentPool | None = Field(
        None,
        json_schema_extra={"jsonapi_type": "relation", "jsonapi_name": "agent-pool"},
    )  # AgentPool object
    current_state_version: Any | None = Field(
        None,
        json_schema_extra={
            "jsonapi_type": "relation",
            "jsonapi_name": "current-state-version",
        },
    )  # StateVersion object
    organization: Organization | None = Field(
        None,
        json_schema_extra={"jsonapi_type": "relation", "jsonapi_name": "organization"},
    )
    project: Project | None = Field(
        None, json_schema_extra={"jsonapi_type": "relation", "jsonapi_name": "project"}
    )
    ssh_key: Any | None = Field(
        None, json_schema_extra={"jsonapi_type": "relation", "jsonapi_name": "ssh-key"}
    )  # SSHKey object
    outputs: list[WorkspaceOutputs] = Field(
        default_factory=list,
        json_schema_extra={"jsonapi_type": "relation", "jsonapi_name": "outputs"},
    )
    tags: list[Tag] = Field(
        default_factory=list,
        json_schema_extra={"jsonapi_type": "relation", "jsonapi_name": "tags"},
    )
    current_configuration_version: Any | None = Field(
        None,
        json_schema_extra={
            "jsonapi_type": "relation",
            "jsonapi_name": "current-configuration-version",
        },
    )  # ConfigurationVersion object
    locked_by: LockedByChoice | None = Field(
        None,
        json_schema_extra={"jsonapi_type": "polyrelation", "jsonapi_name": "locked-by"},
    )
    variables: list[Any] = Field(default_factory=list)  # Variable objects
    tag_bindings: list[TagBinding] = Field(default_factory=list)
    effective_tag_bindings: list[EffectiveTagBinding] = Field(default_factory=list)

    # Links
    links: dict[str, Any] | None = Field(None, alias="links")

    data_retention_policy: Any | None = None  # Legacy field, deprecated
    data_retention_policy_choice: DataRetentionPolicyChoice | None = None


class WorkspaceIncludeOpt(str, Enum):
    ORGANIZATION = "organization"
    CURRENT_CONFIG_VER = "current_configuration_version"
    CURRENT_CONFIG_VER_INGRESS = "current_configuration_version.ingress_attributes"
    CURRENT_RUN = "current_run"
    CURRENT_RUN_PLAN = "current_run.plan"
    CURRENT_RUN_CONFIG_VER = "current_run.configuration_version"
    CURRENT_RUN_CONFIG_VER_INGRESS = (
        "current_run.configuration_version.ingress_attributes"
    )
    EFFECTIVE_TAG_BINDINGS = "effective_tag_bindings"
    LOCKED_BY = "locked_by"
    README = "readme"
    OUTPUTS = "outputs"
    CURRENT_STATE_VER = "current-state-version"
    PROJECT = "project"


class WorkspaceSource(str, Enum):
    API = "tfe-api"
    MODULE = "tfe-module"
    UI = "tfe-ui"
    TERRAFORM = "terraform"


class WorkspaceActions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    is_destroyable: bool = Field(default=False, alias="is-destroyable")


class WorkspacePermissions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    can_destroy: bool = Field(default=False, alias="can-destroy")
    can_force_unlock: bool = Field(default=False, alias="can-force-unlock")
    can_lock: bool = Field(default=False, alias="can-lock")
    can_manage_run_tasks: bool = Field(default=False, alias="can-manage-run-tasks")
    can_queue_apply: bool = Field(default=False, alias="can-queue-apply")
    can_queue_destroy: bool = Field(default=False, alias="can-queue-destroy")
    can_queue_run: bool = Field(default=False, alias="can-queue-run")
    can_read_settings: bool = Field(default=False, alias="can-read-settings")
    can_unlock: bool = Field(default=False, alias="can-unlock")
    can_update: bool = Field(default=False, alias="can-update")
    can_update_variable: bool = Field(default=False, alias="can-update-variable")
    can_force_delete: bool | None = Field(default=None, alias="can-force-delete")


class WorkspaceSettingOverwrites(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    execution_mode: bool | None = Field(None, alias="execution-mode")
    agent_pool: bool | None = Field(None, alias="agent-pool")


class WorkspaceOutputs(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    name: str | None = Field(default=None, alias="name")
    sensitive: bool = Field(default=False, alias="sensitive")
    output_type: str | None = Field(default=None, alias="output-type")
    value: Any | None = Field(default=None, alias="value")


class LockedByChoice(BaseModel):
    run: Any | None = None
    user: Any | None = None
    team: Any | None = None


class WorkspaceListOptions(BaseModel):
    """Options for listing workspaces."""

    # Pagination options (from ListOptions)
    page_number: int | None = None
    page_size: int | None = None

    # Search and filter options
    search: str | None = None  # search[name] - partial workspace name
    tags: str | None = None  # search[tags] - comma-separated tag names
    exclude_tags: str | None = (
        None  # search[exclude-tags] - comma-separated tag names to exclude
    )
    wildcard_name: str | None = None  # search[wildcard-name] - substring matching
    project_id: str | None = None  # filter[project][id] - project ID filter
    current_run_status: str | None = (
        None  # filter[current-run][status] - run status filter
    )

    # Tag binding filters (not URL encoded, handled specially)
    tag_bindings: list[TagBinding] = Field(default_factory=list)

    # Include related resources
    include: list[WorkspaceIncludeOpt] = Field(default_factory=list)

    # Sorting options
    sort: str | None = (
        None  # "name" (default) or "current-run.created-at", prepend "-" to reverse
    )


class WorkspaceReadOptions(BaseModel):
    include: list[WorkspaceIncludeOpt] = Field(default_factory=list)


class WorkspaceCreateOptions(BaseModel):
    name: str
    type: str = "workspaces"
    agent_pool_id: str | None = None
    allow_destroy_plan: bool | None = None
    assessments_enabled: bool | None = None
    auto_apply: bool | None = None
    auto_apply_run_trigger: bool | None = None
    auto_destroy_at: datetime | None = None
    auto_destroy_activity_duration: str | None = None
    inherits_project_auto_destroy: bool | None = None
    description: str | None = None
    execution_mode: ExecutionMode | None = None
    file_triggers_enabled: bool | None = None
    global_remote_state: bool | None = None
    migration_environment: str | None = None
    operations: bool | None = None
    queue_all_runs: bool | None = None
    speculative_enabled: bool | None = None
    source_name: str | None = None
    source_url: str | None = None
    structured_run_output_enabled: bool | None = None
    terraform_version: str | None = None
    trigger_prefixes: list[str] = Field(default_factory=list)
    trigger_patterns: list[str] = Field(default_factory=list)
    vcs_repo: VCSRepo | None = None
    working_directory: str | None = None
    hyok_enabled: bool | None = None
    tags: list[Tag] = Field(default_factory=list)
    setting_overwrites: WorkspaceSettingOverwrites | None = None
    project: Project | None = None
    tag_bindings: list[TagBinding] = Field(default_factory=list)


class WorkspaceUpdateOptions(BaseModel):
    name: str
    type: str = "workspaces"
    agent_pool_id: str | None = None
    allow_destroy_plan: bool | None = None
    assessments_enabled: bool | None = None
    auto_apply: bool | None = None
    auto_apply_run_trigger: bool | None = None
    auto_destroy_at: datetime | None = None
    auto_destroy_activity_duration: str | None = None
    inherits_project_auto_destroy: bool | None = None
    description: str | None = None
    execution_mode: ExecutionMode | None = None
    file_triggers_enabled: bool | None = None
    global_remote_state: bool | None = None
    operations: bool | None = None
    queue_all_runs: bool | None = None
    speculative_enabled: bool | None = None
    structured_run_output_enabled: bool | None = None
    terraform_version: str | None = None
    trigger_prefixes: list[str] = Field(default_factory=list)
    trigger_patterns: list[str] = Field(default_factory=list)
    vcs_repo: VCSRepo | None = None
    working_directory: str | None = None
    hyok_enabled: bool | None = None
    setting_overwrites: WorkspaceSettingOverwrites | None = None
    project: Project | None = None
    tag_bindings: list[TagBinding] = Field(default_factory=list)


class WorkspaceList(BaseModel):
    items: list[Workspace] = Field(default_factory=list)
    pagination: Pagination | None = None


class WorkspaceRemoveVCSConnectionOptions(BaseModel):
    """Options for removing VCS connection from a workspace."""

    id: str
    vcs_repo: VCSRepoOptions | None = None


class WorkspaceLockOptions(BaseModel):
    """Options for locking a workspace."""

    # Specifies the reason for locking the workspace.
    reason: str


class WorkspaceAssignSSHKeyOptions(BaseModel):
    """Options for assigning an SSH key to a workspace."""

    ssh_key_id: str
    type: str = "workspaces"


class workspaceUnassignSSHKeyOptions(BaseModel):
    """Options for unassigning an SSH key from a workspace."""

    # Must be nil to unset the currently assigned SSH key.
    ssh_key_id: str
    type: str = "workspaces"


class WorkspaceListRemoteStateConsumersOptions(BaseModel):
    """Options for listing remote state consumers of a workspace."""

    # Pagination options (from ListOptions)
    page_number: int | None = None
    page_size: int | None = None


class WorkspaceAddRemoteStateConsumersOptions(BaseModel):
    """Options for adding remote state consumers to a workspace."""

    workspaces: list[Workspace] = Field(default_factory=list)


class WorkspaceRemoveRemoteStateConsumersOptions(BaseModel):
    """Options for removing remote state consumers from a workspace."""

    workspaces: list[Workspace] = Field(default_factory=list)


class WorkspaceUpdateRemoteStateConsumersOptions(BaseModel):
    """Options for updating remote state consumers of a workspace."""

    workspaces: list[Workspace] = Field(default_factory=list)


class WorkspaceTagListOptions(BaseModel):
    """Options for listing tags of a workspace."""

    # Pagination options (from ListOptions)
    page_number: int | None = None
    page_size: int | None = None
    query: str | None = None


class WorkspaceAddTagsOptions(BaseModel):
    """Options for adding tags to a workspace."""

    tags: list[Tag] = Field(default_factory=list)


class WorkspaceRemoveTagsOptions(BaseModel):
    """Options for removing tags from a workspace."""

    tags: list[Tag] = Field(default_factory=list)


class WorkspaceAddTagBindingsOptions(BaseModel):
    """Options for adding tag bindings to a workspace."""

    tag_bindings: list[TagBinding] = Field(default_factory=list)


class VCSRepo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    branch: str | None = Field(default=None, alias="branch")
    display_identifier: str | None = Field(default=None, alias="display-identifier")
    identifier: str | None = Field(default=None, alias="identifier")
    ingress_submodules: bool | None = Field(default=None, alias="ingress-submodules")
    oauth_token_id: str | None = Field(default=None, alias="oauth-token-id")
    tags_regex: str | None = Field(default=None, alias="tags-regex")
    gha_installation_id: str | None = Field(
        default=None, alias="github-app-installation-id"
    )
    repository_http_url: str | None = Field(default=None, alias="repository-http-url")
    service_provider: str | None = Field(default=None, alias="service-provider")
    tags: bool | None = Field(default=None, alias="tags")
    webhook_url: str | None = Field(default=None, alias="webhook-url")
    tag_prefix: str | None = Field(default=None, alias="tag-prefix")
    source_directory: str | None = Field(default=None, alias="source-directory")


class VCSRepoOptions(BaseModel):
    branch: str | None = None
    identifier: str | None = None
    ingress_submodules: bool | None = None
    oauth_token_id: str | None = None
    tags_regex: str | None = None
    gha_installation_id: str | None = None
