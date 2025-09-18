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

# Registry Module Error Constants
ERR_REQUIRED_PROVIDER = "provider is required"
ERR_INVALID_PROVIDER = "invalid value for provider"
ERR_REQUIRED_VERSION = "version is required"
ERR_INVALID_VERSION = "invalid value for version"
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
