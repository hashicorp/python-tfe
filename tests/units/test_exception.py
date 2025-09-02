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
        # Basic creation
        basic = TFEEndpointException("Test message")
        assert basic.message == "Test message"
        assert basic.status_code is None

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

    def test_exception_string_representations(self):
        """Test exception string and repr representations."""
        exception = TFEEndpointException(
            message="Test message",
            status_code=400,
            method="GET",
            path="/test/path",
            error_data={"error": "test"},
        )

        expected_str = (
            "Test message for GET /test/path (HTTP 400) (Error Data: {'error': 'test'})"
        )
        expected_repr = "TFEEndpointException('Test message', status_code=400, method='GET', path='/test/path')"

        assert str(exception) == expected_str
        assert repr(exception) == expected_repr

    def test_exception_inheritance(self):
        """Test that TFEEndpointException inherits from Exception."""
        exception = TFEEndpointException("Test message")
        assert isinstance(exception, Exception)
        assert isinstance(exception, TFEEndpointException)


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
        assert exception.method == "GET"
        assert exception.path == "/test"
        assert exception.status_code == status_code
        assert isinstance(exception, TFEEndpointException)
        assert isinstance(exception, Exception)
