from typing import Any


class TFEEndpointException(Exception):
    """Base exception for all TFE endpoint-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_data: dict[str, Any] | None = None,
        cause: Exception | None = None,
        method: str | None = None,
        path: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_data = error_data or {}
        self.cause = cause
        self.method = method
        self.path = path

        # Build the full error message
        full_message = self._build_error_message()
        super().__init__(full_message)

    def _build_error_message(self) -> str:
        """Build a comprehensive error message with request context."""
        parts = [self.message]

        if self.method and self.path:
            parts.append(f"for {self.method} {self.path}")

        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")

        if self.error_data:
            parts.append(f"(Error Data: {self.error_data})")

        return " ".join(parts)

    def __str__(self) -> str:
        return self._build_error_message()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, status_code={self.status_code}, method={self.method!r}, path={self.path!r})"


# Custom endpoint-specific exceptions
class TFEConnectionException(TFEEndpointException):
    """Exception for connection-related errors."""

    pass


class TFETimeoutException(TFEEndpointException):
    """Exception for timeout errors."""

    pass


class TFEUnauthorizedException(TFEEndpointException):
    """Exception for 401 Unauthorized errors."""

    pass


class TFEForbiddenException(TFEEndpointException):
    """Exception for 403 Forbidden errors."""

    pass


class TFENotFoundException(TFEEndpointException):
    """Exception for 404 Not Found errors."""

    pass


class TFEValidationException(TFEEndpointException):
    """Exception for 422 Validation errors."""

    pass


class TFEServerException(TFEEndpointException):
    """Exception for 5xx server errors."""

    pass
