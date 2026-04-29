# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import (
    InvalidNameError,
    RequiredAgentModeError,
    RequiredAgentPoolIDError,
    RequiredNameError,
    UnsupportedBothTagsRegexAndFileTriggersEnabledError,
    UnsupportedBothTagsRegexAndTriggerPatternsError,
    UnsupportedBothTagsRegexAndTriggerPrefixesError,
    UnsupportedBothTriggerPatternsAndPrefixesError,
    UnsupportedOperationsError,
)
from ..utils import has_tags_regex_defined, is_valid_workspace_name, valid_string
from .agent import AgentPool
from .common import EffectiveTagBinding, Tag, TagBinding
from .data_retention_policy import DataRetentionPolicyChoice
from .organization import ExecutionMode, Organization
from .project import Project

if TYPE_CHECKING:
    from .run import Run


# Helper classes that need to be defined before Workspace
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
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    run: Any | None = None
    user: Any | None = None
    team: Any | None = None


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


class Workspace(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
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
    agent_pool: AgentPool | None = None  # AgentPool object
    current_run: Run | None = None  # Run object
    current_state_version: Any | None = None  # StateVersion object
    organization: Organization | None = None
    project: Project | None = None
    ssh_key: Any | None = None  # SSHKey object
    outputs: list[WorkspaceOutputs] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)
    current_configuration_version: Any | None = None  # ConfigurationVersion object
    locked_by: LockedByChoice | None = None
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


class WorkspaceListOptions(BaseModel):
    """Options for listing workspaces."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]")
    search: str | None = Field(None, alias="search[name]")
    tags: str | None = Field(None, alias="search[tags]")
    exclude_tags: str | None = Field(None, alias="search[exclude-tags]")
    wildcard_name: str | None = Field(None, alias="search[wildcard-name]")
    project_id: str | None = Field(None, alias="filter[project][id]")
    current_run_status: str | None = Field(None, alias="filter[current-run][status]")

    tag_bindings: list[TagBinding] = Field(default_factory=list)

    # Include related resources
    include: list[WorkspaceIncludeOpt] | None = Field(None, alias="include")

    # Sorting options
    sort: str | None = Field(None, alias="sort")


class WorkspaceReadOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[WorkspaceIncludeOpt] | None = Field(None, alias="include")


class WorkspaceCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str = Field(alias="name")
    type: str = Field(default="workspaces")
    agent_pool_id: str | None = Field(None, alias="agent-pool-id")
    allow_destroy_plan: bool | None = Field(None, alias="allow-destroy-plan")
    assessments_enabled: bool | None = Field(None, alias="assessments-enabled")
    auto_apply: bool | None = Field(None, alias="auto-apply")
    auto_apply_run_trigger: bool | None = Field(None, alias="auto-apply-run-trigger")
    auto_destroy_at: datetime | None = Field(None, alias="auto-destroy-at")
    auto_destroy_activity_duration: str | None = Field(
        None, alias="auto-destroy-activity-duration"
    )
    inherits_project_auto_destroy: bool | None = Field(
        None, alias="inherits-project-auto-destroy"
    )
    description: str | None = Field(None, alias="description")
    execution_mode: ExecutionMode | None = Field(None, alias="execution-mode")
    file_triggers_enabled: bool | None = Field(None, alias="file-triggers-enabled")
    global_remote_state: bool | None = Field(None, alias="global-remote-state")
    migration_environment: str | None = Field(None, alias="migration-environment")
    operations: bool | None = Field(None, alias="operations")
    queue_all_runs: bool | None = Field(None, alias="queue-all-runs")
    speculative_enabled: bool | None = Field(None, alias="speculative-enabled")
    source_name: str | None = Field(None, alias="source-name")
    source_url: str | None = Field(None, alias="source-url")
    structured_run_output_enabled: bool | None = Field(
        None, alias="structured-run-output-enabled"
    )
    terraform_version: str | None = Field(None, alias="terraform-version")
    trigger_prefixes: list[str] | None = Field(None, alias="trigger-prefixes")
    trigger_patterns: list[str] | None = Field(None, alias="trigger-patterns")
    vcs_repo: VCSRepoOptions | None = Field(None, alias="vcs-repo")
    working_directory: str | None = Field(None, alias="working-directory")
    hyok_enabled: bool | None = Field(None, alias="hyok-enabled")
    setting_overwrites: WorkspaceSettingOverwrites | None = Field(
        None, alias="setting-overwrites"
    )

    project: Project | None = Field(None, alias="project")
    tag_bindings: list[TagBinding] | None = Field(None, alias="tag-bindings")

    @model_validator(mode="after")
    def valid(self) -> WorkspaceCreateOptions:
        """
        Validate workspace create options for proper API usage.
        Raises specific validation errors if validation fails.
        """
        # Check required name
        if not valid_string(self.name):
            raise RequiredNameError()

        # Check name format
        if not is_valid_workspace_name(self.name):
            raise InvalidNameError()

        # Check operations and execution mode conflict
        if self.operations is not None and self.execution_mode is not None:
            raise UnsupportedOperationsError()

        # Check agent mode requirements
        if self.agent_pool_id is not None and (
            self.execution_mode is None or self.execution_mode != "agent"
        ):
            raise RequiredAgentModeError()

        if (
            self.agent_pool_id is None
            and self.execution_mode is not None
            and self.execution_mode == "agent"
        ):
            raise RequiredAgentPoolIDError()

        # Check trigger patterns and prefixes conflict
        if (
            self.trigger_prefixes
            and len(self.trigger_prefixes) > 0
            and self.trigger_patterns
            and len(self.trigger_patterns) > 0
        ):
            raise UnsupportedBothTriggerPatternsAndPrefixesError()

        # Check tags regex conflicts
        if has_tags_regex_defined(self.vcs_repo):
            if self.trigger_patterns and len(self.trigger_patterns) > 0:
                raise UnsupportedBothTagsRegexAndTriggerPatternsError()

            if self.trigger_prefixes and len(self.trigger_prefixes) > 0:
                raise UnsupportedBothTagsRegexAndTriggerPrefixesError()

            if self.file_triggers_enabled is not None and self.file_triggers_enabled:
                raise UnsupportedBothTagsRegexAndFileTriggersEnabledError()

        return self


class WorkspaceUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str | None = Field(None, alias="name")
    type: str = "workspaces"
    agent_pool_id: str | None = Field(None, alias="agent-pool-id")
    allow_destroy_plan: bool | None = Field(None, alias="allow-destroy-plan")
    assessments_enabled: bool | None = Field(None, alias="assessments-enabled")
    auto_apply: bool | None = Field(None, alias="auto-apply")
    auto_apply_run_trigger: bool | None = Field(None, alias="auto-apply-run-trigger")
    auto_destroy_at: datetime | None = Field(None, alias="auto-destroy-at")
    auto_destroy_activity_duration: str | None = Field(
        None, alias="auto-destroy-activity-duration"
    )
    inherits_project_auto_destroy: bool | None = Field(
        None, alias="inherits-project-auto-destroy"
    )
    description: str | None = Field(None, alias="description")
    execution_mode: ExecutionMode | None = Field(None, alias="execution-mode")
    file_triggers_enabled: bool | None = Field(None, alias="file-triggers-enabled")
    global_remote_state: bool | None = Field(None, alias="global-remote-state")
    operations: bool | None = Field(None, alias="operations")
    queue_all_runs: bool | None = Field(None, alias="queue-all-runs")
    speculative_enabled: bool | None = Field(None, alias="speculative-enabled")
    structured_run_output_enabled: bool | None = Field(
        None, alias="structured-run-output-enabled"
    )
    terraform_version: str | None = Field(None, alias="terraform-version")
    trigger_prefixes: list[str] | None = Field(None, alias="trigger-prefixes")
    trigger_patterns: list[str] | None = Field(None, alias="trigger-patterns")
    vcs_repo: VCSRepoOptions | None = Field(None, alias="vcs-repo")
    working_directory: str | None = Field(None, alias="working-directory")
    hyok_enabled: bool | None = Field(None, alias="hyok-enabled")
    setting_overwrites: WorkspaceSettingOverwrites | None = Field(
        None, alias="setting-overwrites"
    )
    project: Project | None = Field(None, alias="project")
    tag_bindings: list[TagBinding] | None = Field(None, alias="tag-bindings")

    @model_validator(mode="after")
    def valid(self) -> WorkspaceUpdateOptions:
        """
        Validate workspace update options for proper API usage.
        Raises specific validation errors if validation fails.
        """
        # Check name format if provided
        if self.name is not None and not is_valid_workspace_name(self.name):
            raise InvalidNameError()

        # Check operations and execution mode conflict
        if self.operations is not None and self.execution_mode is not None:
            raise UnsupportedOperationsError()

        # Check agent mode requirements
        if (
            self.agent_pool_id is None
            and self.execution_mode is not None
            and self.execution_mode == "agent"
        ):
            raise RequiredAgentPoolIDError()

        # Check trigger patterns and prefixes conflict
        if (
            self.trigger_prefixes
            and len(self.trigger_prefixes) > 0
            and self.trigger_patterns
            and len(self.trigger_patterns) > 0
        ):
            raise UnsupportedBothTriggerPatternsAndPrefixesError()

        # Check tags regex conflicts
        if has_tags_regex_defined(self.vcs_repo):
            if self.trigger_patterns and len(self.trigger_patterns) > 0:
                raise UnsupportedBothTagsRegexAndTriggerPatternsError()

            if self.trigger_prefixes and len(self.trigger_prefixes) > 0:
                raise UnsupportedBothTagsRegexAndTriggerPrefixesError()

            if self.file_triggers_enabled is not None and self.file_triggers_enabled:
                raise UnsupportedBothTagsRegexAndFileTriggersEnabledError()

        return self


class WorkspaceRemoveVCSConnectionOptions(BaseModel):
    """Options for removing VCS connection from a workspace."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    vcs_repo: VCSRepoOptions = Field(alias="vcs-repo")


class WorkspaceLockOptions(BaseModel):
    """Options for locking a workspace."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Specifies the reason for locking the workspace.
    reason: str | None = Field(None, alias="reason")


class WorkspaceAssignSSHKeyOptions(BaseModel):
    """Options for assigning an SSH key to a workspace."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    ssh_key_id: str = Field(alias="id")
    type: str = Field(default="workspaces")


class workspaceUnassignSSHKeyOptions(BaseModel):
    """Options for unassigning an SSH key from a workspace."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Must be nil to unset the currently assigned SSH key.
    ssh_key_id: str = Field(alias="id")
    type: str = Field(default="workspaces")


class WorkspaceListRemoteStateConsumersOptions(BaseModel):
    """Options for listing remote state consumers of a workspace."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]")


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

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]")
    query: str | None = Field(None, alias="name")


class WorkspaceAddTagsOptions(BaseModel):
    """Options for adding tags to a workspace."""

    tags: list[Tag] = Field(default_factory=list)


class WorkspaceRemoveTagsOptions(BaseModel):
    """Options for removing tags from a workspace."""

    tags: list[Tag] = Field(default_factory=list)


class WorkspaceAddTagBindingsOptions(BaseModel):
    """Options for adding tag bindings to a workspace."""

    tag_bindings: list[TagBinding] = Field(default_factory=list)


class VCSRepoOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    branch: str | None = Field(None, alias="branch")
    identifier: str | None = Field(None, alias="identifier")
    ingress_submodules: bool | None = Field(None, alias="ingress-submodules")
    oauth_token_id: str | None = Field(None, alias="oauth-token-id")
    tags_regex: str | None = Field(None, alias="tags-regex")
    gha_installation_id: str | None = Field(None, alias="github-app-installation-id")


# Rebuild Workspace model after all dependencies are defined
def _rebuild_workspace_model() -> None:
    """Rebuild Workspace model to resolve forward references."""
    try:
        from .run import Run  # noqa: F401

        Workspace.model_rebuild()
    except ImportError:
        # Run model not yet available, will be rebuilt later
        pass


_rebuild_workspace_model()
