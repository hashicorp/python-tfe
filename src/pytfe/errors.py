# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any


class TFEError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        errors: list[dict | str] | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.errors = errors or []


class AuthError(TFEError): ...


class NotFound(TFEError): ...


class RateLimited(TFEError):
    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        **kw: Any,
    ) -> None:
        super().__init__(message, **kw)
        self.retry_after = retry_after


class ValidationError(TFEError): ...


class ServerError(TFEError): ...


class UnsupportedInCloud(TFEError): ...


class UnsupportedInEnterprise(TFEError): ...


class InvalidValues(TFEError): ...


class RequiredFieldMissing(TFEError): ...


class ErrStateVersionUploadNotSupported(TFEError): ...


class InvalidCallbackURLError(TFEError):
    def __init__(self, message: str = "Invalid callback URL") -> None:
        super().__init__(message)


class InvalidAccessTokenError(TFEError):
    def __init__(self, message: str = "Invalid access token") -> None:
        super().__init__(message)


class InvalidTaskResultsCallbackStatusError(TFEError):
    def __init__(
        self,
        message: str = "Invalid task result callback status; must be one of: passed, failed, running",
    ) -> None:
        super().__init__(message)


# Generic error constants
ERR_UNAUTHORIZED = "unauthorized"
ERR_RESOURCE_NOT_FOUND = "resource not found"
ERR_MISSING_DIRECTORY = "path needs to be an existing directory"
ERR_NAMESPACE_NOT_AUTHORIZED = "namespace not authorized"

# Error message constants
ERR_INVALID_NAME = "invalid value for name"
ERR_REQUIRED_NAME = "name is required"
ERR_INVALID_ORG = "invalid organization name"
ERR_REQUIRED_EMAIL = "email is required"
ERR_INVALID_EMAIL = "invalid email format"
ERR_INVALID_MEMBERSHIP_ID = "invalid value for organization membership ID"

# Registry Module Error Constants
ERR_REQUIRED_PROVIDER = "provider is required"
ERR_INVALID_PROVIDER = "invalid value for provider"
ERR_REQUIRED_VERSION = "version is required"
ERR_INVALID_VERSION = "invalid value for version"
ERR_INVALID_NAMESPACE = "invalid value for namespace"
ERR_REQUIRED_NAMESPACE = "namespace is required"
ERR_INVALID_REGISTRY_NAME = "invalid registry name"
ERR_UNSUPPORTED_BOTH_NAMESPACE_AND_PRIVATE_REGISTRY_NAME = (
    "namespace cannot be used with private registry"
)
ERR_REQUIRED_VCS_REPO = "VCS repo is required"
ERR_REQUIRED_BRANCH_WHEN_TESTS_ENABLED = "branch is required when tests are enabled"
ERR_BRANCH_MUST_BE_EMPTY_WHEN_TAGS_ENABLED = (
    "branch must be empty when tags are enabled"
)
ERR_AGENT_POOL_NOT_REQUIRED_FOR_REMOTE_EXECUTION = (
    "agent pool not required for remote execution"
)
ERR_INVALID_MODULE_ID = "invalid module ID"
# Workspaces
ERR_INVALID_WORKSPACE_ID = "invalid workspace ID"
ERR_INVALID_VARIABLE_ID = "invalid variable ID"
# Configuration Versions
ERR_INVALID_CONFIG_VERSION_ID = "invalid configuration version ID"
ERR_REQUIRED_KEY = "key is required"
ERR_REQUIRED_CATEGORY = "category is required"

# OAuth Client Error Constants
ERR_INVALID_OAUTH_CLIENT_ID = "invalid OAuth client ID"
ERR_REQUIRED_API_URL = "API URL is required"
ERR_REQUIRED_HTTP_URL = "HTTP URL is required"
ERR_REQUIRED_OAUTH_TOKEN = "OAuth token is required"
ERR_REQUIRED_SERVICE_PROVIDER = "service provider is required"
ERR_UNSUPPORTED_PRIVATE_KEY = "private key is not supported for this service provider"
ERR_REQUIRED_PROJECT = "projects are required"
ERR_PROJECT_MIN_LIMIT = "must specify at least one project"

# OAuth Token Error Constants
ERR_INVALID_OAUTH_TOKEN_ID = "invalid OAuth token ID"

# SSH Key Error Constants
ERR_INVALID_SSH_KEY_ID = "invalid SSH key ID"

# Reserved Tag Key Error Constants
ERR_INVALID_RESERVED_TAG_KEY_ID = "invalid reserved tag key ID"
ERR_REQUIRED_TAG_KEY = "tag key is required"
ERR_INVALID_TAG_KEY = "invalid tag key"

# Organization Tag Error Constants
ERR_INVALID_TAG = "invalid value for tag"
ERR_REQUIRED_TAG_ID = "tag ID is required"
ERR_REQUIRED_TAG_WORKSPACE_ID = "workspace ID is required"


class WorkspaceNotFound(NotFound): ...


class WorkspaceNameConflict(ValidationError): ...


class WorkspaceLocked(TFEError): ...


class WorkspaceLockedStateVersionStillPending(TFEError): ...


# Workspace validation errors
class WorkspaceValidationError(ValidationError):
    """Base class for workspace validation errors."""

    pass


class InvalidNameError(WorkspaceValidationError):
    """Raised when workspace name is invalid."""

    def __init__(self) -> None:
        super().__init__("invalid value for name")


class UnsupportedOperationsError(WorkspaceValidationError):
    """Raised when operations is specified with execution mode."""

    def __init__(self) -> None:
        super().__init__(
            "operations is deprecated and cannot be specified when execution mode is used"
        )


class RequiredAgentModeError(WorkspaceValidationError):
    """Raised when agent pool ID is specified without agent execution mode."""

    def __init__(self) -> None:
        super().__init__("specifying an agent pool ID requires 'agent' execution mode")


class RequiredAgentPoolIDError(WorkspaceValidationError):
    """Raised when agent execution mode is specified without agent pool ID."""

    def __init__(self) -> None:
        super().__init__(
            "'agent' execution mode requires an agent pool ID to be specified"
        )


class UnsupportedBothTriggerPatternsAndPrefixesError(WorkspaceValidationError):
    """Raised when both trigger patterns and prefixes are specified."""

    def __init__(self) -> None:
        super().__init__(
            '"TriggerPatterns" and "TriggerPrefixes" cannot be populated at the same time'
        )


class UnsupportedBothTagsRegexAndTriggerPatternsError(WorkspaceValidationError):
    """Raised when both tags regex and trigger patterns are specified."""

    def __init__(self) -> None:
        super().__init__(
            '"TagsRegex" and "TriggerPatterns" cannot be populated at the same time'
        )


class UnsupportedBothTagsRegexAndTriggerPrefixesError(WorkspaceValidationError):
    """Raised when both tags regex and trigger prefixes are specified."""

    def __init__(self) -> None:
        super().__init__(
            '"TagsRegex" and "TriggerPrefixes" cannot be populated at the same time'
        )


class UnsupportedBothTagsRegexAndFileTriggersEnabledError(WorkspaceValidationError):
    """Raised when both tags regex and file triggers are enabled."""

    def __init__(self) -> None:
        super().__init__(
            '"TagsRegex" cannot be populated when "FileTriggersEnabled" is true'
        )


# Parameter validation errors
class InvalidWorkspaceValueError(WorkspaceValidationError):
    """Raised when workspace name parameter is invalid."""

    def __init__(self) -> None:
        super().__init__("invalid value for workspace")


class RequiredSSHKeyIDError(WorkspaceValidationError):
    """Raised when SSH key ID parameter is required but not provided."""

    def __init__(self) -> None:
        super().__init__("SSH key ID is required")


class InvalidSSHKeyIDError(WorkspaceValidationError):
    """Raised when SSH key ID parameter is invalid."""

    def __init__(self) -> None:
        super().__init__("invalid value for SSH key ID")


class WorkspaceRequiredError(WorkspaceValidationError):
    """Raised when workspace parameter is required but not provided."""

    def __init__(self) -> None:
        super().__init__("workspace is required")


class WorkspaceMinimumLimitError(WorkspaceValidationError):
    """Raised when at least one workspace is required but not provided."""

    def __init__(self) -> None:
        super().__init__("must provide at least one workspace")


class MissingTagIdentifierError(WorkspaceValidationError):
    """Raised when tag identifier is missing."""

    def __init__(self) -> None:
        super().__init__("must specify at least one tag by ID or name")


class MissingTagBindingIdentifierError(WorkspaceValidationError):
    """Raised when tag binding identifier is missing."""

    def __init__(self) -> None:
        super().__init__("TagBindings are required")


class InvalidOrgError(InvalidValues):
    """Raised when an invalid run task ID is provided."""

    def __init__(self, message: str = "invalid value for organization"):
        super().__init__(message)


class InvalidWorkspaceIDError(InvalidValues):
    """Raised when an invalid run workspace ID is provided."""

    def __init__(self, message: str = "invalid value for workspace ID"):
        super().__init__(message)


class RequiredNameError(RequiredFieldMissing):
    """Raised when a required name field is missing."""

    def __init__(self, message: str = "name is required"):
        super().__init__(message)


class RequiredWorkspaceError(RequiredFieldMissing):
    """Raised when a required workspace field is missing."""

    def __init__(self, message: str = "workspace is required"):
        super().__init__(message)


# Run Task errors
class InvalidRunTaskIDError(InvalidValues):
    """Raised when an invalid run task ID is provided."""

    def __init__(self, message: str = "invalid value for run task ID"):
        super().__init__(message)


class InvalidRunTaskNameError(InvalidValues):
    """Raised when an invalid run task name is provided."""

    pass


class InvalidRunTaskURLError(InvalidValues):
    """Raised when an invalid run task URL is provided."""

    def __init__(self, message: str = "invalid url for run task URL"):
        super().__init__(message)


class InvalidRunTaskCategoryError(InvalidValues):
    """Raised when an invalid run task category is provided."""

    def __init__(self, message: str = 'category must be "task"'):
        super().__init__(message)


class InvalidWorkspaceRunTaskIDError(InvalidValues):
    """Raised when an invalid workspace run task ID is provided."""

    def __init__(self, message: str = "invalid value for workspace run task ID"):
        super().__init__(message)


# Run Trigger errors
class RequiredRunTriggerListOpsError(RequiredFieldMissing):
    """Raised when required run trigger list options are missing."""

    def __init__(self, message: str = "required run trigger list options"):
        super().__init__(message)


class RequiredSourceableError(RequiredFieldMissing):
    """Raised when a required sourceable field is missing."""

    def __init__(self, message: str = "sourceable is required"):
        super().__init__(message)


class InvalidRunTriggerTypeError(InvalidValues):
    """Raised when an invalid run trigger type is provided."""

    def __init__(
        self,
        message: str = 'invalid value or no value for RunTriggerType. It must be either "inbound" or "outbound"',
    ):
        super().__init__(message)


class UnsupportedRunTriggerTypeError(InvalidValues):
    """Raised when an unsupported run trigger type is provided with include params."""

    def __init__(
        self,
        message: str = 'unsupported RunTriggerType. It must be "inbound" when requesting "include" query params',
    ):
        super().__init__(message)


class InvalidRunTriggerIDError(InvalidValues):
    """Raised when an invalid run trigger ID is provided."""

    def __init__(self, message: str = "invalid value for run trigger ID"):
        super().__init__(message)


# Run errors
class InvalidRunIDError(InvalidValues):
    """Raised when an invalid run ID is provided."""

    def __init__(self, message: str = "invalid value for run ID"):
        super().__init__(message)


class InvalidQueryRunIDError(InvalidValues):
    """Raised when an invalid query run ID is provided."""

    def __init__(self, message: str = "invalid value for query run ID"):
        super().__init__(message)


class InvalidExplorerSavedViewIDError(InvalidValues):
    """Raised when a saved view id is missing or blank (Explorer view-scoped routes)."""

    def __init__(self, message: str = "invalid value for explorer saved view ID"):
        super().__init__(message)


class TerraformVersionValidForPlanOnlyError(ValidationError):
    """Raised when terraform_version is set without plan_only being true."""

    def __init__(
        self,
        message: str = "setting terraform-version is only valid when plan-only is set to true",
    ):
        super().__init__(message)


# Plan errors
class InvalidPlanIDError(InvalidValues):
    """Raised when an invalid plan ID is provided."""

    def __init__(self, message: str = "invalid value for plan ID"):
        super().__init__(message)


# Apply errors
class InvalidApplyIDError(InvalidValues):
    """Raised when an invalid apply ID is provided."""

    def __init__(self, message: str = "invalid value for apply ID"):
        super().__init__(message)


# Plan export errors
class InvalidPlanExportIDError(InvalidValues):
    """Raised when an invalid plan export ID is provided."""

    def __init__(self, message: str = "invalid value for plan export ID"):
        super().__init__(message)


class RequiredPlanError(RequiredFieldMissing):
    """Raised when a plan is required but was not provided."""

    def __init__(self, message: str = "plan is required"):
        super().__init__(message)


# Cost estimate errors
class InvalidCostEstimateIDError(InvalidValues):
    """Raised when an invalid cost estimate ID is provided."""

    def __init__(self, message: str = "invalid value for cost estimate ID"):
        super().__init__(message)


# Assessment result errors
class InvalidAssessmentResultIDError(InvalidValues):
    """Raised when an invalid assessment result ID is provided."""

    def __init__(self, message: str = "invalid value for assessment result ID"):
        super().__init__(message)


# HYOK (Hold Your Own Key) configuration errors
class InvalidHYOKConfigurationIDError(InvalidValues):
    """Raised when an invalid HYOK configuration ID is provided."""

    def __init__(self, message: str = "invalid value for HYOK configuration ID"):
        super().__init__(message)


class RequiredKEKIDError(RequiredFieldMissing):
    """Raised when a key-encryption-key id (kek-id) is required but not provided."""

    def __init__(self, message: str = "kek-id is required"):
        super().__init__(message)


# Subscription errors
class InvalidSubscriptionIDError(InvalidValues):
    """Raised when an invalid subscription ID is provided."""

    def __init__(self, message: str = "invalid value for subscription ID"):
        super().__init__(message)


# IP allowlist (CIDR range list) errors
class InvalidCIDRRangeListIDError(InvalidValues):
    """Raised when an invalid CIDR range list (IP allowlist) ID is provided."""

    def __init__(self, message: str = "invalid value for CIDR range list ID"):
        super().__init__(message)


class InvalidCIDRRangeIDError(InvalidValues):
    """Raised when an invalid CIDR range ID is provided."""

    def __init__(self, message: str = "invalid value for CIDR range ID"):
        super().__init__(message)


class RequiredCIDRBlockError(RequiredFieldMissing):
    """Raised when a CIDR block is required but was not provided."""

    def __init__(self, message: str = "cidr-block is required"):
        super().__init__(message)


# Public Terraform Registry (module) errors
class InvalidModuleNamespaceError(InvalidValues):
    """Raised when an invalid registry module namespace is provided."""

    def __init__(self, message: str = "invalid value for module namespace"):
        super().__init__(message)


class InvalidModuleNameError(InvalidValues):
    """Raised when an invalid registry module name is provided."""

    def __init__(self, message: str = "invalid value for module name"):
        super().__init__(message)


class InvalidModuleProviderError(InvalidValues):
    """Raised when an invalid registry module provider is provided."""

    def __init__(self, message: str = "invalid value for module provider"):
        super().__init__(message)


class InvalidModuleVersionError(InvalidValues):
    """Raised when an invalid registry module version is provided."""

    def __init__(self, message: str = "invalid value for module version"):
        super().__init__(message)


# Run Event errors
class InvalidRunEventIDError(InvalidValues):
    """Raised when an invalid run event ID is provided."""

    def __init__(self, message: str = "invalid value for run event ID"):
        super().__init__(message)


# Policy errors
class InvalidPolicyIDError(InvalidValues):
    """Raised when an invalid policy ID is provided."""

    def __init__(self, message: str = "invalid value for policy ID"):
        super().__init__(message)


class RequiredQueryError(RequiredFieldMissing):
    """Raised when a required query field is missing."""

    def __init__(self, message: str = "query is required"):
        super().__init__(message)


class RequiredEnforceError(RequiredFieldMissing):
    """Raised when a required enforce field is missing."""

    def __init__(self, message: str = "enforce or enforcement-level is required"):
        super().__init__(message)


# Policy Check errors
class InvalidPolicyCheckIDError(InvalidValues):
    """Raised when an invalid policy check ID is provided."""

    def __init__(self, message: str = "invalid value for policy check ID"):
        super().__init__(message)


# Policy Set errors
class InvalidPolicySetIDError(InvalidValues):
    """Raised when an invalid policy set ID is provided."""

    def __init__(self, message: str = "invalid value for policy set ID"):
        super().__init__(message)


class RequiredPoliciesError(RequiredFieldMissing):
    """Raised when a required policies field is missing."""

    def __init__(self, message: str = "policies are required"):
        super().__init__(message)


class InvalidPoliciesError(InvalidValues):
    """Raised when an invalid policies field is provided."""

    def __init__(self, message: str = "must provide at least one policy"):
        super().__init__(message)


# Policy Evaluation errors
class InvalidTaskStageIDError(InvalidValues):
    """Raised when a task stage ID is invalid."""

    def __init__(self, message: str = "invalid value for task stage ID"):
        super().__init__(message)


class InvalidPolicyEvaluationIDError(InvalidValues):
    """Raised when an invalid policy evaluation ID is provided."""

    def __init__(self, message: str = "invalid value for policy evaluation ID"):
        super().__init__(message)


# Policy Set Parameter errors
class InvalidParamIDError(InvalidValues):
    """Raised when an invalid policy set parameter ID is provided."""

    def __init__(self, message: str = "invalid value for parameter ID"):
        super().__init__(message)


class RequiredCategoryError(RequiredFieldMissing):
    """Raised when a required category field is missing."""

    def __init__(self, message: str = "category is required"):
        super().__init__(message)


class InvalidCategoryError(InvalidValues):
    """Raised when an invalid category field is provided."""

    def __init__(self, message: str = "category must be policy-set"):
        super().__init__(message)


class RequiredKeyError(RequiredFieldMissing):
    """Raised when a required key field is missing."""

    def __init__(self, message: str = "key is required"):
        super().__init__(message)


# Policy Set Outcome errors
class InvalidPolicySetOutcomeIDError(InvalidValues):
    """Raised when an invalid policy set outcome ID is provided."""

    def __init__(self, message: str = "invalid value for policy set outcome ID"):
        super().__init__(message)


# Registry Provider Version errors
class RequiredPrivateRegistryError(RequiredFieldMissing):
    """Raised when a required private registry field is missing."""

    def __init__(self, message: str = "only private registry is allowed"):
        super().__init__(message)


class InvalidVersionError(InvalidValues):
    """Raised when an invalid version is provided."""

    def __init__(self, message: str = "invalid value for version"):
        super().__init__(message)


class InvalidKeyIDError(InvalidValues):
    """Raised when an invalid key ID is provided."""

    def __init__(self, message: str = "invalid value for key-id"):
        super().__init__(message)


# Team errors
class EmptyTeamNameError(InvalidValues):
    """Raised when a team name is empty."""

    def __init__(self, message: str = "team names cannot be empty"):
        super().__init__(message)


class InvalidTeamIDError(InvalidValues):
    """Raised when an invalid team ID is provided."""

    def __init__(self, message: str = "invalid value for team ID"):
        super().__init__(message)


# Team Project Access errors
class InvalidProjectIDError(InvalidValues):
    """Raised when an invalid project ID is provided."""

    def __init__(self, message: str = "invalid value for project ID"):
        super().__init__(message)


class RequiredTeamError(RequiredFieldMissing):
    """Raised when a required team field is missing."""

    def __init__(self, message: str = "team is required"):
        super().__init__(message)


class InvalidTeamProjectAccessIDError(InvalidValues):
    """Raised when an invalid team project access ID is provided."""

    def __init__(self, message: str = "invalid value for team project access ID"):
        super().__init__(message)


# Registry Provider Platform errors
class RequiredOSError(RequiredFieldMissing):
    """Raised when a required OS field is missing."""

    def __init__(self, message: str = "os is required"):
        super().__init__(message)


class RequiredArchError(RequiredFieldMissing):
    """Raised when a required architecture field is missing."""

    def __init__(self, message: str = "arch is required"):
        super().__init__(message)


class RequiredShasumError(RequiredFieldMissing):
    """Raised when a required shasum field is missing."""

    def __init__(self, message: str = "shasum is required"):
        super().__init__(message)


class RequiredFilenameError(RequiredFieldMissing):
    """Raised when a required filename field is missing."""

    def __init__(self, message: str = "filename is required"):
        super().__init__(message)


class InvalidOSError(InvalidValues):
    """Raised when an invalid OS field is provided."""

    def __init__(self, message: str = "invalid value for os"):
        super().__init__(message)


class InvalidArchError(InvalidValues):
    """Raised when an invalid architecture field is provided."""

    def __init__(self, message: str = "invalid value for arch"):
        super().__init__(message)


class InvalidNamespaceError(InvalidValues):
    """Raised when an invalid namespace field is provided."""

    def __init__(self, message: str = "invalid value for namespace"):
        super().__init__(message)


class InvalidRegistryNameError(InvalidValues):
    """Raised when an invalid registry name field is provided."""

    def __init__(
        self,
        message: str = "invalid value for registry-name. It must be either private or public",
    ):
        super().__init__(message)


# Stack Configuration errors
class InvalidStackIDError(InvalidValues):
    """Raised when an invalid stack ID is provided."""

    def __init__(self, message: str = "invalid value for stack ID"):
        super().__init__(message)


class InvalidStackConfigurationIDError(InvalidValues):
    """Raised when an invalid stack configuration ID is provided."""

    def __init__(self, message: str = "invalid value for stack configuration ID"):
        super().__init__(message)


# Comment errors
class InvalidCommentIDError(InvalidValues):
    """Raised when an invalid comment ID is provided."""

    def __init__(self, message: str = "invalid value for comment ID"):
        super().__init__(message)


class RequiredCommentBodyError(TFEError):
    """Raised when comment body is empty or missing."""

    def __init__(self, message: str = "comment body is required"):
        super().__init__(message)


# Team Token errors
class InvalidTokenIDError(InvalidValues):
    """Raised when an invalid authentication token ID is provided."""

    def __init__(self, message: str = "invalid value for token ID"):
        super().__init__(message)


# Agent Pool errors
class InvalidAgentPoolIDError(InvalidValues):
    """Raised when an invalid agent pool ID is provided."""

    def __init__(self, message: str = "invalid value for agent pool ID"):
        super().__init__(message)


class RequiredProjectError(RequiredFieldMissing):
    """Raised when a required project field is missing."""

    def __init__(self, message: str = "project is required"):
        super().__init__(message)


# No-code module errors
class InvalidNoCodeModuleIDError(InvalidValues):
    """Raised when an invalid no-code module ID is provided."""

    def __init__(self, message: str = "invalid value for no-code module ID"):
        super().__init__(message)


class InvalidWorkspaceUpgradeIDError(InvalidValues):
    """Raised when an invalid workspace upgrade ID is provided."""

    def __init__(self, message: str = "invalid value for workspace upgrade ID"):
        super().__init__(message)


class RequiredRegistryModuleIDError(RequiredFieldMissing):
    """Raised when a registry module ID is required but missing."""

    def __init__(self, message: str = "registry module ID is required"):
        super().__init__(message)


# OIDC configuration errors
class InvalidOIDCConfigurationIDError(InvalidValues):
    """Raised when an invalid OIDC configuration ID is provided."""

    def __init__(self, message: str = "invalid value for OIDC configuration ID"):
        super().__init__(message)


# Admin SAML/SCIM + GitHub App installation errors
class InvalidSAMLProviderTypeError(InvalidValues):
    """Raised when an unrecognised SAML provider type is supplied."""

    def __init__(self, message: str = "invalid value for SAML provider type") -> None:
        super().__init__(message)


class InvalidSCIMTokenIDError(InvalidValues):
    """Raised when an invalid SCIM token ID is supplied."""

    def __init__(self, message: str = "invalid value for SCIM token ID") -> None:
        super().__init__(message)


class RequiredSCIMTokenDescriptionError(RequiredFieldMissing):
    """Raised when a SCIM token is created without a non-empty description."""

    def __init__(self, message: str = "SCIM token description is required") -> None:
        super().__init__(message)


class InvalidGitHubAppInstallationIDError(InvalidValues):
    """Raised when an invalid GitHub App installation ID is supplied."""

    def __init__(
        self, message: str = "invalid value for GitHub App installation ID"
    ) -> None:
        super().__init__(message)
