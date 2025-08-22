"""
Exceptions for the PyTFE SDK.

This module defines custom exceptions used throughout the PyTFE SDK
to provide meaningful error handling for different types of API errors.
"""

from typing import Optional, Dict, Any


class PyTFEException(Exception):
    """Base exception for all PyTFE SDK errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None, 
        response_data: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(PyTFEException):
    """Raised when authentication fails (401 Unauthorized)."""
    pass


class AuthorizationError(PyTFEException):
    """Raised when authorization fails (403 Forbidden)."""
    pass


class NotFoundError(PyTFEException):
    """Raised when a resource is not found (404 Not Found)."""
    pass


class ValidationError(PyTFEException):
    """Raised when request validation fails (422 Unprocessable Entity)."""
    pass


class ConflictError(PyTFEException):
    """Raised when there's a conflict (409 Conflict)."""
    pass


class ServerError(PyTFEException):
    """Raised when there's a server error (5xx status codes)."""
    pass


class RateLimitError(PyTFEException):
    """Raised when rate limit is exceeded (429 Too Many Requests)."""
    pass


class ConnectionError(PyTFEException):
    """Raised when there's a connection error."""
    pass
