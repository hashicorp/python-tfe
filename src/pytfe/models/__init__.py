# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

# ── Agent & Agent Pools ────────────────────────────────────────────────────────
from .agent import (
    Agent,
    AgentListOptions,
    AgentPool,
    AgentPoolAllowedWorkspacePolicy,
    AgentPoolAssignToWorkspacesOptions,
    AgentPoolCreateOptions,
    AgentPoolListOptions,
    AgentPoolReadOptions,
    AgentPoolRemoveFromWorkspacesOptions,
    AgentPoolUpdateOptions,
    AgentReadOptions,
    AgentStatus,
    AgentToken,
    AgentTokenCreateOptions,
    AgentTokenListOptions,
)
from .comment import (
    Comment,
    CommentCreateOptions,
)

# ── Core models split out of old types.py ─────────────────────────────────────
# Adjust these imports to match where you placed them during the split.
# Common / pagination / enums
from .common import (
    EffectiveTagBinding,
    Pagination,
    Tag,
    TagBinding,
    TagList,
)  # if you put ExecutionMode enum here

# ── Configuration Versions ────────────────────────────────────────────────────
# (Old: .configuration_version_types) → import directly from real module
from .configuration_version import (
    ConfigurationSource,
    ConfigurationStatus,
    ConfigurationVersion,
    ConfigurationVersionCreateOptions,
    ConfigurationVersionList,
    ConfigurationVersionListOptions,
    ConfigurationVersionReadOptions,
    ConfigurationVersionUpload,
    ConfigVerIncludeOpt,
    IngressAttributes,
)

# Data retention policy family
from .data_retention_policy import (
    DataRetentionPolicy,
    DataRetentionPolicyChoice,
    DataRetentionPolicyDeleteOlder,
    DataRetentionPolicyDeleteOlderSetOptions,
    DataRetentionPolicyDontDelete,
    DataRetentionPolicyDontDeleteSetOptions,
    DataRetentionPolicySetOptions,
)
from .explorer import (
    ExplorerQueryOptions,
    ExplorerRow,
    ExplorerSavedQuery,
    ExplorerSavedQueryFilter,
    ExplorerSavedView,
    ExplorerSavedViewCreateOptions,
    ExplorerSavedViewUpdateOptions,
    ExplorerUrlFilter,
    ExplorerViewType,
)

# ── Notification Configurations ───────────────────────────────────────────────
from .notification_configuration import (
    DeliveryResponse,
    NotificationConfiguration,
    NotificationConfigurationCreateOptions,
    NotificationConfigurationList,
    NotificationConfigurationListOptions,
    NotificationConfigurationSubscribableChoice,
    NotificationConfigurationUpdateOptions,
    NotificationDestinationType,
    NotificationTriggerType,
)

# ── OAuth ─────────────────────────────────────────────────────────────────────
from .oauth_client import (
    OAuthClient,
    OAuthClientAddProjectsOptions,
    OAuthClientCreateOptions,
    OAuthClientIncludeOpt,
    OAuthClientList,
    OAuthClientListOptions,
    OAuthClientReadOptions,
    OAuthClientRemoveProjectsOptions,
    OAuthClientUpdateOptions,
    ServiceProviderType,
)
from .oauth_token import (
    OAuthToken,
    OAuthTokenListOptions,
    OAuthTokenUpdateOptions,
)

# Organization / Project
from .organization import (
    Entitlements,
    ExecutionMode,
    Organization,
    OrganizationCreateOptions,
    OrganizationUpdateOptions,
    ReadRunQueueOptions,
    RunQueue,
)
from .organization_audit_configuration import (
    OrganizationAuditConfigAuditStreaming,
    OrganizationAuditConfigAuditTrails,
    OrganizationAuditConfigPermissions,
    OrganizationAuditConfigTimestamps,
    OrganizationAuditConfiguration,
    OrganizationAuditConfigurationOptions,
    OrganizationAuditConfigurationTest,
)
from .organization_membership import (
    OrganizationMembership,
    OrganizationMembershipCreateOptions,
    OrganizationMembershipListOptions,
    OrganizationMembershipReadOptions,
    OrganizationMembershipStatus,
    OrgMembershipIncludeOpt,
)
from .policy import (
    Policy,
    PolicyCreateOptions,
    PolicyList,
    PolicyListOptions,
    PolicyUpdateOptions,
)

# ── Policy ─────────────────────────────────────────────────────────────
from .policy_check import (
    PolicyActions,
    PolicyCheck,
    PolicyCheckIncludeOpt,
    PolicyCheckListOptions,
    PolicyPermissions,
    PolicyResult,
    PolicyScope,
    PolicyStatus,
    PolicyStatusTimestamps,
)
from .policy_evaluation import (
    PolicyAttachable,
    PolicyEvaluation,
    PolicyEvaluationListOptions,
    PolicyEvaluationStatus,
    PolicyEvaluationStatusTimestamps,
    PolicyResultCount,
)
from .policy_set import (
    PolicySet,
    PolicySetAddPoliciesOptions,
    PolicySetAddProjectsOptions,
    PolicySetAddWorkspaceExclusionsOptions,
    PolicySetAddWorkspacesOptions,
    PolicySetCreateOptions,
    PolicySetIncludeOpt,
    PolicySetList,
    PolicySetListOptions,
    PolicySetReadOptions,
    PolicySetRemovePoliciesOptions,
    PolicySetRemoveProjectsOptions,
    PolicySetRemoveWorkspaceExclusionsOptions,
    PolicySetRemoveWorkspacesOptions,
    PolicySetUpdateOptions,
)
from .policy_set_parameter import (
    PolicySetParameter,
    PolicySetParameterCreateOptions,
    PolicySetParameterListOptions,
    PolicySetParameterUpdateOptions,
)
from .policy_types import (
    EnforcementLevel,
    PolicyKind,
)
from .project import (
    Project,
    ProjectAddTagBindingsOptions,
    ProjectCreateOptions,
    ProjectListOptions,
    ProjectSettingOverwrites,
    ProjectUpdateOptions,
)

# ── Query Runs ────────────────────────────────────────────────────────────────
from .query_run import (
    QueryRun,
    QueryRunActions,
    QueryRunCreateOptions,
    QueryRunIncludeOpt,
    QueryRunListOptions,
    QueryRunReadOptions,
    QueryRunSource,
    QueryRunStatus,
    QueryRunStatusTimestamps,
    QueryRunVariable,
)

# ── Registry Modules / Providers ──────────────────────────────────────────────
# (Old: .registry_module_types / .registry_provider_types) → import from real modules
from .registry_module import (
    AgentExecutionMode,
    Commit,
    CommitList,
    Input,
    Output,
    ProviderDependency,
    PublishingMechanism,
    RegistryModule,
    RegistryModuleCreateOptions,
    RegistryModuleCreateVersionOptions,
    RegistryModuleCreateWithVCSConnectionOptions,
    RegistryModuleID,
    RegistryModuleList,
    RegistryModuleListIncludeOpt,
    RegistryModuleListOptions,
    RegistryModulePermissions,
    RegistryModuleStatus,
    RegistryModuleUpdateOptions,
    RegistryModuleVCSRepo,
    RegistryModuleVCSRepoOptions,
    RegistryModuleVCSRepoUpdateOptions,
    RegistryModuleVersion,
    RegistryModuleVersionStatus,
    RegistryModuleVersionStatuses,
    RegistryName,
    Resource,
    Root,
    TerraformRegistryModule,
    TestConfig,
)
from .registry_provider import (
    RegistryProvider,
    RegistryProviderCreateOptions,
    RegistryProviderID,
    RegistryProviderIncludeOps,
    RegistryProviderList,
    RegistryProviderListOptions,
    RegistryProviderPermissions,
    RegistryProviderReadOptions,
)
from .registry_provider_platform import (
    RegistryProviderPlatform,
    RegistryProviderPlatformCreateOptions,
    RegistryProviderPlatformID,
    RegistryProviderPlatformListOptions,
    RegistryProviderPlatformPermissions,
)
from .registry_provider_version import (
    RegistryProviderVersion,
    RegistryProviderVersionCreateOptions,
    RegistryProviderVersionID,
    RegistryProviderVersionListOptions,
    RegistryProviderVersionPermissions,
)

# ── Reserved Tag Keys ─────────────────────────────────────────────────────────
from .reserved_tag_key import (
    ReservedTagKey,
    ReservedTagKeyCreateOptions,
    ReservedTagKeyListOptions,
    ReservedTagKeyUpdateOptions,
)

# Runs
from .run import (
    OrganizationRunList,
    Run,
    RunActions,
    RunApplyOptions,
    RunCancelOptions,
    RunCreateOptions,
    RunDiscardOptions,
    RunForceCancelOptions,
    RunIncludeOpt,
    RunList,
    RunListForOrganizationOptions,
    RunListOptions,
    RunOperation,
    RunPermissions,
    RunReadOptions,
    RunSource,
    RunStatus,
    RunStatusTimestamps,
    RunVariable,
    RunVariableAttr,
)
from .run_event import (
    RunEvent,
    RunEventIncludeOpt,
    RunEventList,
    RunEventListOptions,
    RunEventReadOptions,
)
from .run_task import (
    GlobalRunTask,
    GlobalRunTaskOptions,
    RunTask,
    RunTaskCreateOptions,
    RunTaskIncludeOptions,
    RunTaskList,
    RunTaskListOptions,
    RunTaskReadOptions,
    RunTaskUpdateOptions,
    Stage,
    TaskEnforcementLevel,
)
from .run_task_request import (
    RunTaskRequest,
    RunTaskRequestCapabilitites,
)
from .run_task_integration import (
    TaskResultCallbackRequestOptions,
    TaskResultOutcome,
    TaskResultTag,
)
from .run_task_integration import (
    TaskResultStatus as TaskResultCallbackStatus,
)
from .run_trigger import (
    RunTrigger,
    RunTriggerCreateOptions,
    RunTriggerFilterOp,
    RunTriggerIncludeOp,
    RunTriggerList,
    RunTriggerListOptions,
    SourceableChoice,
)

# ── SSH Keys ──────────────────────────────────────────────────────────────────
from .ssh_key import (
    SSHKey,
    SSHKeyCreateOptions,
    SSHKeyListOptions,
    SSHKeyUpdateOptions,
)
from .stack_configuration import (
    StackComponent,
    StackConfiguration,
    StackConfigurationCreateOptions,
    StackConfigurationIncludeOps,
    StackConfigurationListOptions,
    StackConfigurationReadOptions,
    StackConfigurationSource,
    StackConfigurationStatus,
)
from .state_version import (
    StateVersion,
    StateVersionCreateOptions,
    StateVersionCurrentOptions,
    StateVersionListOptions,
    StateVersionReadOptions,
)
from .state_version_output import (
    StateVersionOutput,
    StateVersionOutputsListOptions,
)

# ── Task Result ───────────────────────────────────────────────────────────────
from .task_result import (
    TaskEnforcementLevel as TaskResultEnforcementLevel,
)
from .task_result import (
    TaskResult,
    TaskResultStatus,
    TaskResultStatusTimestamps,
)
from .task_stage import TaskStage
from .team import (
    OrganizationAccess,
    Team,
    TeamCreateOptions,
    TeamIncludeOpt,
    TeamListOptions,
    TeamPermissions,
    TeamUpdateOptions,
)
from .team_token import (
    CreatedByChoice,
    TeamToken,
    TeamTokenCreateOptions,
    TeamTokenListOptions,
)

# Variables
from .variable import (
    CategoryType,
    Variable,
    VariableCreateOptions,
    VariableListOptions,
    VariableUpdateOptions,
)

# ── Variable Sets ──────────────────────────────────────────────────────────────
from .variable_set import (
    Parent,
    VariableSet,
    VariableSetApplyToProjectsOptions,
    VariableSetApplyToWorkspacesOptions,
    VariableSetCreateOptions,
    VariableSetIncludeOpt,
    VariableSetListOptions,
    VariableSetReadOptions,
    VariableSetRemoveFromProjectsOptions,
    VariableSetRemoveFromWorkspacesOptions,
    VariableSetUpdateOptions,
    VariableSetUpdateWorkspacesOptions,
    VariableSetVariable,
    VariableSetVariableCreateOptions,
    VariableSetVariableListOptions,
    VariableSetVariableUpdateOptions,
)

# Workspaces
from .workspace import (
    LockedByChoice,
    VCSRepo,
    VCSRepoOptions,
    Workspace,
    WorkspaceActions,
    WorkspaceAddRemoteStateConsumersOptions,
    WorkspaceAddTagBindingsOptions,
    WorkspaceAddTagsOptions,
    WorkspaceAssignSSHKeyOptions,
    WorkspaceCreateOptions,
    WorkspaceIncludeOpt,
    WorkspaceListOptions,
    WorkspaceListRemoteStateConsumersOptions,
    WorkspaceLockOptions,
    WorkspaceOutputs,
    WorkspacePermissions,
    WorkspaceReadOptions,
    WorkspaceRemoveRemoteStateConsumersOptions,
    WorkspaceRemoveTagsOptions,
    WorkspaceRemoveVCSConnectionOptions,
    WorkspaceSettingOverwrites,
    WorkspaceSource,
    WorkspaceTagListOptions,
    WorkspaceUpdateOptions,
    WorkspaceUpdateRemoteStateConsumersOptions,
)

# ── Workspace Resources ───────────────────────────────────────────────────────
from .workspace_resource import (
    WorkspaceResource,
    WorkspaceResourceListOptions,
)
from .workspace_run_task import (
    RunTaskReference,
    WorkspaceRunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskEnforcementLevel,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskStage,
    WorkspaceRunTaskUpdateOptions,
)

# ── Public surface ────────────────────────────────────────────────────────────
__all__ = [
    # Notification configurations
    "DeliveryResponse",
    "NotificationConfiguration",
    "NotificationConfigurationCreateOptions",
    "NotificationConfigurationList",
    "NotificationConfigurationListOptions",
    "NotificationConfigurationSubscribableChoice",
    "NotificationConfigurationUpdateOptions",
    "NotificationDestinationType",
    "NotificationTriggerType",
    # OAuth
    "OAuthClient",
    "OAuthClientAddProjectsOptions",
    "OAuthClientCreateOptions",
    "OAuthClientIncludeOpt",
    "OAuthClientList",
    "OAuthClientListOptions",
    "OAuthClientReadOptions",
    "OAuthClientRemoveProjectsOptions",
    "OAuthClientUpdateOptions",
    "ServiceProviderType",
    # OAuth token
    "OAuthToken",
    "OAuthTokenListOptions",
    "OAuthTokenUpdateOptions",
    # SSH keys
    "SSHKey",
    "SSHKeyCreateOptions",
    "SSHKeyListOptions",
    "SSHKeyUpdateOptions",
    # Reserved tag keys
    "ReservedTagKey",
    "ReservedTagKeyCreateOptions",
    "ReservedTagKeyListOptions",
    "ReservedTagKeyUpdateOptions",
    # Agent & pools
    "Agent",
    "AgentPool",
    "AgentPoolAllowedWorkspacePolicy",
    "AgentPoolAssignToWorkspacesOptions",
    "AgentPoolCreateOptions",
    "AgentPoolListOptions",
    "AgentPoolReadOptions",
    "AgentPoolRemoveFromWorkspacesOptions",
    "AgentPoolUpdateOptions",
    "AgentStatus",
    "AgentListOptions",
    "AgentReadOptions",
    "AgentToken",
    "AgentTokenCreateOptions",
    "AgentTokenListOptions",
    # Configuration versions
    "ConfigurationSource",
    "ConfigurationStatus",
    "ConfigurationVersion",
    "ConfigurationVersionCreateOptions",
    "ConfigurationVersionList",
    "ConfigurationVersionListOptions",
    "ConfigurationVersionReadOptions",
    "ConfigurationVersionUpload",
    "ConfigVerIncludeOpt",
    "IngressAttributes",
    # Registry modules
    "AgentExecutionMode",
    "Commit",
    "CommitList",
    "Input",
    "Output",
    "ProviderDependency",
    "PublishingMechanism",
    "RegistryModule",
    "RegistryModuleCreateOptions",
    "RegistryModuleCreateVersionOptions",
    "RegistryModuleCreateWithVCSConnectionOptions",
    "RegistryModuleID",
    "RegistryModuleList",
    "RegistryModuleListIncludeOpt",
    "RegistryModuleListOptions",
    "RegistryModulePermissions",
    "RegistryModuleStatus",
    "RegistryModuleUpdateOptions",
    "RegistryModuleVCSRepo",
    "RegistryModuleVCSRepoOptions",
    "RegistryModuleVCSRepoUpdateOptions",
    "RegistryModuleVersion",
    "RegistryModuleVersionStatus",
    "RegistryModuleVersionStatuses",
    "RegistryName",
    "Resource",
    "Root",
    "TestConfig",
    "TerraformRegistryModule",
    # Registry providers
    "RegistryProvider",
    "RegistryProviderCreateOptions",
    "RegistryProviderID",
    "RegistryProviderIncludeOps",
    "RegistryProviderList",
    "RegistryProviderListOptions",
    "RegistryProviderPermissions",
    "RegistryProviderReadOptions",
    # Registry provider versions
    "RegistryProviderVersion",
    "RegistryProviderVersionCreateOptions",
    "RegistryProviderVersionID",
    "RegistryProviderVersionListOptions",
    "RegistryProviderVersionPermissions",
    # Registry provider platforms
    "RegistryProviderPlatform",
    "RegistryProviderPlatformCreateOptions",
    "RegistryProviderPlatformID",
    "RegistryProviderPlatformListOptions",
    "RegistryProviderPlatformPermissions",
    # Stack Configuration
    "StackComponent",
    "StackConfiguration",
    "StackConfigurationCreateOptions",
    "StackConfigurationIncludeOps",
    "StackConfigurationListOptions",
    "StackConfigurationReadOptions",
    "StackConfigurationSource",
    "StackConfigurationStatus",
    # Query runs
    "QueryRun",
    "QueryRunActions",
    "QueryRunCreateOptions",
    "QueryRunIncludeOpt",
    "QueryRunListOptions",
    "QueryRunReadOptions",
    "QueryRunSource",
    "QueryRunStatus",
    "QueryRunStatusTimestamps",
    "QueryRunVariable",
    # Explorer
    "ExplorerQueryOptions",
    "ExplorerRow",
    "ExplorerSavedQuery",
    "ExplorerSavedQueryFilter",
    "ExplorerSavedView",
    "ExplorerSavedViewCreateOptions",
    "ExplorerSavedViewUpdateOptions",
    "ExplorerUrlFilter",
    "ExplorerViewType",
    # Core (from old types.py, now split)
    "Entitlements",
    "ExecutionMode",
    "Pagination",
    "Organization",
    "OrganizationCreateOptions",
    "OrganizationUpdateOptions",
    "OrganizationAuditConfigAuditStreaming",
    "OrganizationAuditConfigAuditTrails",
    "OrganizationAuditConfigPermissions",
    "OrganizationAuditConfigTimestamps",
    "OrganizationAuditConfiguration",
    "OrganizationAuditConfigurationOptions",
    "OrganizationAuditConfigurationTest",
    "OrganizationMembership",
    "OrganizationMembershipCreateOptions",
    "OrganizationMembershipListOptions",
    "OrganizationMembershipReadOptions",
    "OrganizationMembershipStatus",
    "OrgMembershipIncludeOpt",
    "OrganizationAccess",
    "Team",
    "TeamPermissions",
    "TeamCreateOptions",
    "TeamIncludeOpt",
    "TeamListOptions",
    "TeamUpdateOptions",
    # Team Tokens
    "CreatedByChoice",
    "TeamToken",
    "TeamTokenCreateOptions",
    "TeamTokenListOptions",
    "Project",
    "ProjectAddTagBindingsOptions",
    "ProjectCreateOptions",
    "ProjectListOptions",
    "ProjectUpdateOptions",
    "ProjectSettingOverwrites",
    "DataRetentionPolicy",
    "DataRetentionPolicyChoice",
    "DataRetentionPolicyDeleteOlder",
    "DataRetentionPolicyDeleteOlderSetOptions",
    "DataRetentionPolicyDontDelete",
    "DataRetentionPolicyDontDeleteSetOptions",
    "DataRetentionPolicySetOptions",
    "EffectiveTagBinding",
    "Tag",
    "TagBinding",
    "TagList",
    "CategoryType",
    "Variable",
    "VariableCreateOptions",
    "VariableListOptions",
    "VariableUpdateOptions",
    "LockedByChoice",
    "VCSRepo",
    "VCSRepoOptions",
    "Workspace",
    "WorkspaceActions",
    "WorkspaceAddRemoteStateConsumersOptions",
    "WorkspaceAddTagBindingsOptions",
    "WorkspaceAddTagsOptions",
    "WorkspaceAssignSSHKeyOptions",
    "WorkspaceCreateOptions",
    "WorkspaceIncludeOpt",
    "WorkspaceListOptions",
    "WorkspaceListRemoteStateConsumersOptions",
    "WorkspaceLockOptions",
    "WorkspaceOutputs",
    "WorkspacePermissions",
    "WorkspaceReadOptions",
    "WorkspaceRemoveRemoteStateConsumersOptions",
    "WorkspaceRemoveTagsOptions",
    "WorkspaceRemoveVCSConnectionOptions",
    "WorkspaceSettingOverwrites",
    "WorkspaceSource",
    "WorkspaceTagListOptions",
    "WorkspaceUpdateOptions",
    "WorkspaceUpdateRemoteStateConsumersOptions",
    # Workspace Resources
    "WorkspaceResource",
    "WorkspaceResourceListOptions",
    # Workspace Run Tasks
    "RunTaskReference",
    "WorkspaceRunTask",
    "WorkspaceRunTaskEnforcementLevel",
    "WorkspaceRunTaskStage",
    "WorkspaceRunTaskListOptions",
    "WorkspaceRunTaskCreateOptions",
    "WorkspaceRunTaskUpdateOptions",
    "RunQueue",
    "ReadRunQueueOptions",
    # Runs
    "Run",
    "RunStatus",
    "RunSource",
    "RunIncludeOpt",
    "RunOperation",
    "RunActions",
    "RunPermissions",
    "RunStatusTimestamps",
    "RunVariable",
    "RunVariableAttr",
    "RunList",
    "RunListOptions",
    "OrganizationRunList",
    "RunListForOrganizationOptions",
    "RunCreateOptions",
    "RunReadOptions",
    "RunApplyOptions",
    "RunCancelOptions",
    "RunForceCancelOptions",
    "RunDiscardOptions",
    # Run events
    "RunEvent",
    "RunEventIncludeOpt",
    "RunEventList",
    "RunEventListOptions",
    "RunEventReadOptions",
    # Comments
    "Comment",
    "CommentCreateOptions",
    # Run tasks
    "RunTask",
    "RunTaskIncludeOptions",
    "GlobalRunTask",
    "GlobalRunTaskOptions",
    "Stage",
    "TaskEnforcementLevel",
    "RunTaskList",
    "RunTaskListOptions",
    "RunTaskCreateOptions",
    "RunTaskUpdateOptions",
    "RunTaskReadOptions",
    # Run Task Request
    "RunTaskRequest",
    "RunTaskRequestCapabilitites",
    # Task Result
    "TaskResult",
    "TaskResultEnforcementLevel",
    "TaskResultStatus",
    "TaskResultStatusTimestamps",
    "TaskStage",
    # Run task integration (callback)
    "TaskResultCallbackRequestOptions",
    "TaskResultCallbackStatus",
    "TaskResultOutcome",
    "TaskResultTag",
    # Run triggers
    "RunTrigger",
    "RunTriggerCreateOptions",
    "RunTriggerList",
    "RunTriggerListOptions",
    "SourceableChoice",
    "RunTriggerFilterOp",
    "RunTriggerIncludeOp",
    # Policy Checks
    "PolicyCheck",
    "PolicyCheckIncludeOpt",
    "PolicyScope",
    "PolicyStatus",
    "PolicyActions",
    "PolicyPermissions",
    "PolicyResult",
    "PolicyStatusTimestamps",
    "PolicyCheckListOptions",
    # Policy Evaluation
    "PolicyAttachable",
    "PolicyEvaluation",
    "PolicyEvaluationListOptions",
    "PolicyEvaluationStatus",
    "PolicyEvaluationStatusTimestamps",
    "PolicyResultCount",
    # Policy
    "Policy",
    "PolicyCreateOptions",
    "PolicyList",
    "PolicyListOptions",
    "PolicyUpdateOptions",
    # Policy Sets
    "PolicySet",
    "PolicySetIncludeOpt",
    "PolicySetList",
    "PolicySetAddPoliciesOptions",
    "PolicySetAddProjectsOptions",
    "PolicySetAddWorkspacesOptions",
    "PolicySetAddWorkspaceExclusionsOptions",
    "PolicySetCreateOptions",
    "PolicySetListOptions",
    "PolicySetReadOptions",
    "PolicySetRemovePoliciesOptions",
    "PolicySetRemoveWorkspacesOptions",
    "PolicySetRemoveWorkspaceExclusionsOptions",
    "PolicySetRemoveProjectsOptions",
    "PolicySetUpdateOptions",
    # Policy Set Parameters
    "PolicySetParameter",
    "PolicySetParameterCreateOptions",
    "PolicySetParameterListOptions",
    "PolicySetParameterUpdateOptions",
    "PolicyKind",
    "EnforcementLevel",
    # Variable Sets
    "Parent",
    "VariableSet",
    "VariableSetApplyToProjectsOptions",
    "VariableSetApplyToWorkspacesOptions",
    "VariableSetCreateOptions",
    "VariableSetIncludeOpt",
    "VariableSetListOptions",
    "VariableSetReadOptions",
    "VariableSetRemoveFromProjectsOptions",
    "VariableSetRemoveFromWorkspacesOptions",
    "VariableSetUpdateOptions",
    "VariableSetUpdateWorkspacesOptions",
    "VariableSetVariable",
    "VariableSetVariableCreateOptions",
    "VariableSetVariableListOptions",
    "VariableSetVariableUpdateOptions",
    # State Versions
    "StateVersion",
    "StateVersionCreateOptions",
    "StateVersionCurrentOptions",
    "StateVersionListOptions",
    "StateVersionReadOptions",
    # State Version Outputs
    "StateVersionOutput",
    "StateVersionOutputsListOptions",
]

# Rebuild models with forward references after all models are loaded
PolicyCheck.model_rebuild()
RegistryProvider.model_rebuild()
RegistryProviderVersion.model_rebuild()
RegistryProviderPlatform.model_rebuild()

# Rebuild TaskResult to resolve Run, Workspace, PolicyEvaluation, TaskStage refs
TaskResult.model_rebuild(
    raise_errors=False,
    _types_namespace={
        "PolicyEvaluation": PolicyEvaluation,
        "Run": Run,
        "TaskStage": TaskStage,
        "Workspace": Workspace,
    },
)
