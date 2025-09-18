from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OrganizationUpdateOptions(BaseModel):
    name: str | None = None
    email: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    default_execution_mode: str | None = None
    external_id: str | None = None
    is_unified: bool | None = None
    owners_team_saml_role_id: str | None = None
    permissions: dict | None = None
    saml_enabled: bool | None = None
    session_remember: int | None = None
    session_timeout: int | None = None
    two_factor_conformant: bool | None = None
    send_passing_statuses_for_untriggered_speculative_plans: bool | None = None
    remaining_testable_count: int | None = None
    speculative_plan_management_enabled: bool | None = None
    aggregated_commit_status_enabled: bool | None = None
    allow_force_delete_workspaces: bool | None = None
    default_project: dict | None = None
    default_agent_pool: dict | None = None
    data_retention_policy: dict | None = None
    data_retention_policy_choice: dict | None = None


class OrganizationCreateOptions(BaseModel):
    name: str | None = None
    email: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    default_execution_mode: str | None = None
    external_id: str | None = None
    is_unified: bool | None = None
    owners_team_saml_role_id: str | None = None
    permissions: dict | None = None
    saml_enabled: bool | None = None
    session_remember: int | None = None
    session_timeout: int | None = None
    two_factor_conformant: bool | None = None
    send_passing_statuses_for_untriggered_speculative_plans: bool | None = None
    remaining_testable_count: int | None = None
    speculative_plan_management_enabled: bool | None = None
    aggregated_commit_status_enabled: bool | None = None
    allow_force_delete_workspaces: bool | None = None
    default_project: dict | None = None
    default_agent_pool: dict | None = None
    data_retention_policy: dict | None = None
    data_retention_policy_choice: dict | None = None


class ExecutionMode(str, Enum):
    REMOTE = "remote"
    AGENT = "agent"
    LOCAL = "local"


class RunStatus(str, Enum):
    PLANNING = "planning"
    PLANNED = "planned"
    APPLIED = "applied"
    CANCELED = "canceled"
    ERRORED = "errored"


class Organization(BaseModel):
    name: str | None = None
    assessments_enforced: bool | None = None
    collaborator_auth_policy: str | None = None
    cost_estimation_enabled: bool | None = None
    created_at: datetime | None = None
    default_execution_mode: str | None = None
    email: str | None = None
    external_id: str | None = None
    id: str | None = None
    is_unified: bool | None = None
    owners_team_saml_role_id: str | None = None
    permissions: dict | None = None
    saml_enabled: bool | None = None
    session_remember: int | None = None
    session_timeout: int | None = None
    trial_expires_at: datetime | None = None
    two_factor_conformant: bool | None = None
    send_passing_statuses_for_untriggered_speculative_plans: bool | None = None
    remaining_testable_count: int | None = None
    speculative_plan_management_enabled: bool | None = None
    aggregated_commit_status_enabled: bool | None = None
    allow_force_delete_workspaces: bool | None = None
    default_project: dict | None = None
    default_agent_pool: dict | None = None
    data_retention_policy: dict | None = None
    data_retention_policy_choice: dict | None = None


class Project(BaseModel):
    """Project represents a Terraform Enterprise project"""

    id: str
    name: str
    description: str = ""
    organization: str
    created_at: str = ""
    updated_at: str = ""
    workspace_count: int = 0
    default_execution_mode: str = "remote"


class ProjectListOptions(BaseModel):
    """Options for listing projects"""

    # Optional: String used to filter results by complete project name
    name: str | None = None
    # Optional: Query string to search projects by names
    query: str | None = None
    # Optional: Include related resources
    include: list[str] | None = None
    # Pagination options
    page_number: int | None = None
    page_size: int | None = None


class ProjectCreateOptions(BaseModel):
    """Options for creating a project"""

    # Required: A name to identify the project
    name: str
    # Optional: A description for the project
    description: str | None = None


class ProjectUpdateOptions(BaseModel):
    """Options for updating a project"""

    # Optional: A name to identify the project
    name: str | None = None
    # Optional: A description for the project
    description: str | None = None


class Workspace(BaseModel):
    id: str
    name: str
    organization: str
    execution_mode: ExecutionMode | None = None
    project_id: str | None = None

    # Core attributes
    actions: WorkspaceActions | None = None
    allow_destroy_plan: bool = False
    assessments_enabled: bool = False
    auto_apply: bool = False
    auto_apply_run_trigger: bool = False
    auto_destroy_at: datetime | None = None
    auto_destroy_activity_duration: str | None = None
    can_queue_destroy_plan: bool = False
    created_at: datetime | None = None
    description: str = ""
    environment: str = ""
    file_triggers_enabled: bool = False
    global_remote_state: bool = False
    inherits_project_auto_destroy: bool = False
    locked: bool = False
    migration_environment: str = ""
    no_code_upgrade_available: bool = False
    operations: bool = False
    permissions: WorkspacePermissions | None = None
    queue_all_runs: bool = False
    speculative_enabled: bool = False
    source: WorkspaceSource | None = None
    source_name: str = ""
    source_url: str = ""
    structured_run_output_enabled: bool = False
    terraform_version: str = ""
    trigger_prefixes: list[str] = Field(default_factory=list)
    trigger_patterns: list[str] = Field(default_factory=list)
    vcs_repo: VCSRepo | None = None
    working_directory: str = ""
    updated_at: datetime | None = None
    resource_count: int = 0
    apply_duration_average: float | None = None  # in seconds
    plan_duration_average: float | None = None  # in seconds
    policy_check_failures: int = 0
    run_failures: int = 0
    runs_count: int = 0
    tag_names: list[str] = Field(default_factory=list)
    setting_overwrites: WorkspaceSettingOverwrites | None = None

    # Relations
    agent_pool: Any | None = None  # AgentPool object
    current_run: Any | None = None  # Run object
    current_state_version: Any | None = None  # StateVersion object
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
    links: dict[str, Any] = Field(default_factory=dict)
    data_retention_policy: DataRetentionPolicy | None = None
    data_retention_policy_choice: DataRetentionPolicyChoice | None = None


class Capacity(BaseModel):
    organization: str
    pending: int
    running: int


class Entitlements(BaseModel):
    id: str
    agents: bool | None = None
    audit_logging: bool | None = None
    cost_estimation: bool | None = None
    global_run_tasks: bool | None = None
    operations: bool | None = None
    private_module_registry: bool | None = None
    private_run_tasks: bool | None = None
    run_tasks: bool | None = None
    sso: bool | None = None
    sentinel: bool | None = None
    state_storage: bool | None = None
    teams: bool | None = None
    vcs_integrations: bool | None = None
    waypoint_actions: bool | None = None
    waypoint_templates_and_addons: bool | None = None


class Run(BaseModel):
    id: str
    status: RunStatus
    # Add other Run fields as needed


class Pagination(BaseModel):
    current_page: int
    total_count: int
    previous_page: int | None = None
    next_page: int | None = None
    total_pages: int | None = None
    # Add other pagination fields as needed


class RunQueue(BaseModel):
    pagination: Pagination | None = None
    items: list[Run] = Field(default_factory=list)


class ReadRunQueueOptions(BaseModel):
    # List options for pagination
    page_number: int | None = None
    page_size: int | None = None


class DataRetentionPolicy(BaseModel):
    """Deprecated: Use DataRetentionPolicyDeleteOlder instead."""

    id: str
    delete_older_than_n_days: int


class DataRetentionPolicyDeleteOlder(BaseModel):
    id: str
    delete_older_than_n_days: int


class DataRetentionPolicyDontDelete(BaseModel):
    id: str


class DataRetentionPolicyChoice(BaseModel):
    """Polymorphic data retention policy choice."""

    data_retention_policy: DataRetentionPolicy | None = None
    data_retention_policy_delete_older: DataRetentionPolicyDeleteOlder | None = None
    data_retention_policy_dont_delete: DataRetentionPolicyDontDelete | None = None

    def is_populated(self) -> bool:
        """Returns whether one of the choices is populated."""
        return (
            self.data_retention_policy is not None
            or self.data_retention_policy_delete_older is not None
            or self.data_retention_policy_dont_delete is not None
        )

    def convert_to_legacy_struct(self) -> DataRetentionPolicy | None:
        """Convert the DataRetentionPolicyChoice to the legacy DataRetentionPolicy struct."""
        if not self.is_populated():
            return None

        if self.data_retention_policy is not None:
            return self.data_retention_policy
        elif self.data_retention_policy_delete_older is not None:
            return DataRetentionPolicy(
                id=self.data_retention_policy_delete_older.id,
                delete_older_than_n_days=self.data_retention_policy_delete_older.delete_older_than_n_days,
            )
        return None


class DataRetentionPolicySetOptions(BaseModel):
    """Deprecated: Use DataRetentionPolicyDeleteOlderSetOptions instead."""

    delete_older_than_n_days: int


class DataRetentionPolicyDeleteOlderSetOptions(BaseModel):
    delete_older_than_n_days: int


class DataRetentionPolicyDontDeleteSetOptions(BaseModel):
    pass  # No additional fields needed


# Variables related models
class CategoryType(str, Enum):
    ENV = "env"
    POLICY_SET = "policy-set"
    TERRAFORM = "terraform"


class Variable(BaseModel):
    id: str | None = None
    key: str | None = None
    value: str | None = None
    description: str | None = None
    category: CategoryType | None = None
    hcl: bool | None = None
    sensitive: bool | None = None
    version_id: str | None = None
    workspace: dict | None = None


class VariableListOptions(BaseModel):
    # Base pagination options would be handled by the service layer
    pass


class VariableCreateOptions(BaseModel):
    key: str | None = None
    value: str | None = None
    description: str | None = None
    category: CategoryType | None = None
    hcl: bool | None = None
    sensitive: bool | None = None


class VariableUpdateOptions(BaseModel):
    key: str | None = None
    value: str | None = None
    description: str | None = None
    category: CategoryType | None = None
    hcl: bool | None = None
    sensitive: bool | None = None


class Tag(BaseModel):
    id: str | None = None
    name: str = ""


class TagBinding(BaseModel):
    id: str | None = None
    key: str
    value: str | None = None


class EffectiveTagBinding(BaseModel):
    id: str
    key: str
    value: str | None = None
    links: dict[str, Any] = Field(default_factory=dict)


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


class VCSRepo(BaseModel):
    branch: str | None = None
    identifier: str | None = None
    ingress_submodules: bool | None = None
    oauth_token_id: str | None = None
    tags_regex: str | None = None
    gha_installation_id: str | None = None


class WorkspaceSource(str, Enum):
    API = "tfe-api"
    MODULE = "tfe-module"
    UI = "tfe-ui"
    TERRAFORM = "terraform"


class WorkspaceActions(BaseModel):
    is_destroyable: bool = False


class WorkspacePermissions(BaseModel):
    can_destroy: bool = False
    can_force_unlock: bool = False
    can_lock: bool = False
    can_manage_run_tasks: bool = False
    can_queue_apply: bool = False
    can_queue_destroy: bool = False
    can_queue_run: bool = False
    can_read_settings: bool = False
    can_unlock: bool = False
    can_update: bool = False
    can_update_variable: bool = False
    can_force_delete: bool | None = None


class WorkspaceSettingOverwrites(BaseModel):
    execution_mode: bool | None = None
    agent_pool: bool | None = None


class WorkspaceOutputs(BaseModel):
    id: str
    name: str
    sensitive: bool = False
    output_type: str
    value: Any | None = None


class LockedByChoice(BaseModel):
    run: Any | None = None
    user: Any | None = None
    team: Any | None = None


class WorkspaceListOptions(BaseModel):
    """Options for listing workspaces.

    Matches the Go-TFE WorkspaceListOptions struct.
    """

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


class TagList(BaseModel):
    items: list[Tag] = Field(default_factory=list)
    pagination: Pagination | None = None


class WorkspaceRemoveVCSConnectionOptions(BaseModel):
    """Options for removing VCS connection from a workspace."""

    # Currently no options are defined, but this class can be extended in the future
    id: str
    vcs_repo: VCSRepo | None = None


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
