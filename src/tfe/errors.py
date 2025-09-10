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
