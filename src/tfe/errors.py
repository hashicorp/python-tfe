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


# Error message constants
ERR_INVALID_NAME = "invalid value for name"
ERR_REQUIRED_NAME = "name is required"
ERR_INVALID_ORG = "invalid organization name"
ERR_REQUIRED_EMAIL = "email is required"


class WorkspaceNotFound(NotFound): ...


class WorkspaceNameConflict(ValidationError): ...


class WorkspaceLocked(TFEError): ...


class WorkspaceLockedStateVersionStillPending(TFEError): ...


# Workspace validation errors
class WorkspaceValidationError(ValidationError):
    """Base class for workspace validation errors."""

    pass


class RequiredNameError(WorkspaceValidationError):
    """Raised when workspace name is required but not provided."""

    def __init__(self) -> None:
        super().__init__("name is required")


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
class InvalidOrgError(WorkspaceValidationError):
    """Raised when organization parameter is invalid."""

    def __init__(self) -> None:
        super().__init__("invalid value for organization")


class InvalidWorkspaceIDError(WorkspaceValidationError):
    """Raised when workspace ID parameter is invalid."""

    def __init__(self) -> None:
        super().__init__("invalid value for workspace ID")


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
