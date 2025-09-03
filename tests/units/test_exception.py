"""Tests for the exception module."""

import pytest

from tfe.exception import (
    TFEConnectionException,
    TFEEndpointException,
    TFEForbiddenException,
    TFENotFoundException,
    TFEServerException,
    TFETimeoutException,
    TFEUnauthorizedException,
    TFEValidationException,
)


class TestTFEEndpointException:
    """Test cases for TFEEndpointException base class."""

    def test_exception_creation_and_properties(self):
        """Test exception creation with various parameter combinations."""
        # Full creation
        cause = ValueError("Original error")
        error_data = {"error": "test"}
        full = TFEEndpointException(
            message="Test message",
            status_code=400,
            error_data=error_data,
            cause=cause,
            method="GET",
            path="/test/path",
        )
        assert full.status_code == 400
        assert full.error_data == error_data
        assert full.cause == cause
        assert full.method == "GET"
        assert full.path == "/test/path"

        # Test string and repr representation
        expected_str = (
            "Test message for GET /test/path (HTTP 400) (Error Data: {'error': 'test'})"
        )
        expected_repr = "TFEEndpointException('Test message', status_code=400, method='GET', path='/test/path')"
        assert str(full) == expected_str
        assert repr(full) == expected_repr

    def test_exception_inheritance(self):
        """Test that TFEEndpointException inherits from Exception."""
        exception = TFEEndpointException("Test message")
        assert isinstance(exception, Exception)
        assert isinstance(exception, TFEEndpointException)

    @pytest.mark.parametrize(
        "message,status_code,method,path,error_data,expected_str",
        [
            # Test with minimal info
            ("Simple error", None, None, None, None, "Simple error"),
            # Test with method and path
            (
                "API error",
                None,
                "POST",
                "/api/test",
                None,
                "API error for POST /api/test",
            ),
            # Test with status code
            ("HTTP error", 404, None, None, None, "HTTP error (HTTP 404)"),
            # Test with error data
            (
                "Validation error",
                None,
                None,
                None,
                {"field": "name"},
                "Validation error (Error Data: {'field': 'name'})",
            ),
            # Test with all components
            (
                "Complete error",
                422,
                "PUT",
                "/api/workspaces",
                {"errors": ["Name is required"]},
                "Complete error for PUT /api/workspaces (HTTP 422) (Error Data: {'errors': ['Name is required']})",
            ),
        ],
    )
    def test_error_message_building(
        self, message, status_code, method, path, error_data, expected_str
    ):
        """Test error message building with different combinations."""
        exception = TFEEndpointException(
            message=message,
            status_code=status_code,
            method=method,
            path=path,
            error_data=error_data,
        )
        assert str(exception) == expected_str


class TestCustomEndpointExceptions:
    """Test cases for custom endpoint exception classes."""

    @pytest.mark.parametrize(
        "exception_class,status_code",
        [
            (TFEConnectionException, None),
            (TFETimeoutException, None),
            (TFEUnauthorizedException, 401),
            (TFEForbiddenException, 403),
            (TFENotFoundException, 404),
            (TFEValidationException, 422),
            (TFEServerException, 500),
        ],
    )
    def test_custom_exceptions(self, exception_class, status_code):
        """Test all custom exception classes."""
        exception = exception_class(
            message="Test message", method="GET", path="/test", status_code=status_code
        )

        assert exception.message == "Test message"
        assert exception.status_code == status_code
        assert isinstance(exception, TFEEndpointException)
        assert isinstance(exception, Exception)

    def test_exception_with_error_data(self):
        """Test exception with error data."""
        error_data = {
            "errors": [{"detail": "Name is required"}, {"detail": "Email is invalid"}]
        }
        exception = TFEValidationException(
            message="Validation failed",
            status_code=422,
            method="POST",
            path="/api/workspaces",
            error_data=error_data,
        )

        assert exception.error_data == error_data
        assert exception.error_data["errors"][0]["detail"] == "Name is required"
