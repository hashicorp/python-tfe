"""Types package for TFE client."""

# Import all types from the main types module by using importlib to avoid circular imports
import importlib.util
import os

# Re-export all agent and agent pool types
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

# Re-export all configuration version types
from .configuration_version_types import (
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

# Re-export all OAuth client types
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

# Re-export all query run types
from .query_run import (
    QueryRun,
    QueryRunCancelOptions,
    QueryRunCreateOptions,
    QueryRunForceCancelOptions,
    QueryRunList,
    QueryRunListOptions,
    QueryRunLogs,
    QueryRunReadOptions,
    QueryRunResults,
    QueryRunStatus,
    QueryRunType,
)

# Re-export all registry module types
from .registry_module_types import (
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

# Re-export all registry provider types
from .registry_provider_types import (
    RegistryProvider,
    RegistryProviderCreateOptions,
    RegistryProviderID,
    RegistryProviderIncludeOps,
    RegistryProviderList,
    RegistryProviderListOptions,
    RegistryProviderPermissions,
    RegistryProviderReadOptions,
)

# Re-export all SSH key types
from .ssh_key import (
    SSHKey,
    SSHKeyCreateOptions,
    SSHKeyList,
    SSHKeyListOptions,
    SSHKeyUpdateOptions,
)

# Define what should be available when importing with *
__all__ = [
    # OAuth client types
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
    # SSH key types
    "SSHKey",
    "SSHKeyCreateOptions",
    "SSHKeyList",
    "SSHKeyListOptions",
    "SSHKeyUpdateOptions",
    # Agent and agent pool types
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
    # Configuration version types
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
    # Registry module types
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
    # Registry provider types
    "RegistryProvider",
    "RegistryProviderCreateOptions",
    "RegistryProviderID",
    "RegistryProviderIncludeOps",
    "RegistryProviderList",
    "RegistryProviderListOptions",
    "RegistryProviderPermissions",
    "RegistryProviderReadOptions",
    # Query run types
    "QueryRun",
    "QueryRunCancelOptions",
    "QueryRunCreateOptions",
    "QueryRunForceCancelOptions",
    "QueryRunList",
    "QueryRunListOptions",
    "QueryRunLogs",
    "QueryRunReadOptions",
    "QueryRunResults",
    "QueryRunStatus",
    "QueryRunType",
    # Main types from types.py (will be dynamically added below)
    "Capacity",
    "DataRetentionPolicy",
    "DataRetentionPolicyChoice",
    "DataRetentionPolicyDeleteOlder",
    "DataRetentionPolicyDeleteOlderSetOptions",
    "DataRetentionPolicyDontDelete",
    "DataRetentionPolicyDontDeleteSetOptions",
    "DataRetentionPolicySetOptions",
    "EffectiveTagBinding",
    "Entitlements",
    "ExecutionMode",
    "LockedByChoice",
    "Organization",
    "OrganizationCreateOptions",
    "OrganizationUpdateOptions",
    "Pagination",
    "Project",
    "ReadRunQueueOptions",
    "Run",
    "RunQueue",
    "RunStatus",
    "Tag",
    "TagBinding",
    "TagList",
    "Variable",
    "VariableCreateOptions",
    "VariableListOptions",
    "VariableUpdateOptions",
    "VCSRepo",
    "Workspace",
    "WorkspaceActions",
    "WorkspaceAddRemoteStateConsumersOptions",
    "WorkspaceAddTagBindingsOptions",
    "WorkspaceAddTagsOptions",
    "WorkspaceAssignSSHKeyOptions",
    "WorkspaceCreateOptions",
    "WorkspaceIncludeOpt",
    "WorkspaceList",
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
]

# Load the main types.py file that's at the same level as this types/ directory
types_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "types.py")
spec = importlib.util.spec_from_file_location("main_types", types_py_path)
if spec is not None and spec.loader is not None:
    main_types = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_types)

    # Re-export all main types
    for name in dir(main_types):
        if not name.startswith("_"):
            globals()[name] = getattr(main_types, name)
