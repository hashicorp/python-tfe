from __future__ import annotations

from typing import Any


class TFEError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        errors: list[dict] | None = None,
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


# Error message constants
ERR_INVALID_NAME = "invalid value for name"
ERR_REQUIRED_NAME = "name is required"
ERR_INVALID_ORG = "invalid organization name"
ERR_REQUIRED_EMAIL = "email is required"

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
ERR_REQUIRED_KEY = "key is required"
ERR_REQUIRED_CATEGORY = "category is required"


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
