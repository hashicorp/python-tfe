"""Tests for the error_utils module."""

from unittest.mock import Mock

import pytest
from requests import exceptions

from tfe.error_utils import (
    extract_error_data,
    handle_http_error,
    parse_tfe_error_response,
)
from tfe.exception import (
    TFEEndpointException,
    TFEForbiddenException,
    TFENotFoundException,
    TFEServerException,
    TFEUnauthorizedException,
    TFEValidationException,
)


class TestExtractErrorData:
    """Test cases for extract_error_data function."""

    def test_extract_none_response(self):
        """Test handling None response."""
        result = extract_error_data(None)
        assert result is None

    @pytest.mark.parametrize(
        "json_return_value,json_side_effect,text_value,expected_result",
        [
            # Test extracting JSON error data
            ({"error": "test error"}, None, None, {"error": "test error"}),
            # Test extracting text when JSON fails
            (None, ValueError("Invalid JSON"), "Error text", {"text": "Error text"}),
            # Test handling non-dict JSON response
            ("simple string", None, None, {"text": "simple string"}),
            # Test handling JSON decode error
            (
                None,
                ValueError("JSON decode error"),
                "Raw response text",
                {"text": "Raw response text"},
            ),
        ],
    )
    def test_extract_data_scenarios(
        self, json_return_value, json_side_effect, text_value, expected_result
    ):
        """Test various data extraction scenarios."""
        mock_response = Mock()
        mock_response.json.return_value = json_return_value
        if json_side_effect:
            mock_response.json.side_effect = json_side_effect
        if text_value:
            mock_response.text = text_value

        result = extract_error_data(mock_response)

        assert result == expected_result
        if json_return_value is not None and json_side_effect is None:
            mock_response.json.assert_called_once()


class TestParseTfeErrorResponse:
    """Test cases for parse_tfe_error_response function."""

    @pytest.mark.parametrize(
        "response_data,expected_message,expected_errors,expected_code",
        [
            # JSON:API format with multiple errors
            (
                {
                    "errors": [
                        {"detail": "Name has already been taken"},
                        {"detail": "Email is invalid"},
                    ]
                },
                "Name has already been taken; Email is invalid",
                ["Name has already been taken", "Email is invalid"],
                None,
            ),
            # JSON:API format with error code
            (
                {
                    "errors": [
                        {"detail": "Name is required", "code": "VALIDATION_ERROR"}
                    ]
                },
                "Name is required",
                ["Name is required"],
                "VALIDATION_ERROR",
            ),
            # JSON:API format with title fallback
            (
                {"errors": [{"title": "Validation Failed", "code": "INVALID_DATA"}]},
                "Validation Failed",
                ["Validation Failed"],
                "INVALID_DATA",
            ),
            # Simple message format
            ({"message": "Resource not found"}, "Resource not found", [], None),
            # Error field format
            (
                {"error": "Invalid request parameters"},
                "Invalid request parameters",
                [],
                None,
            ),
            # Empty errors list
            ({"errors": []}, "Unknown API error", [], None),
            # Unknown format
            ({"unknown_field": "some value"}, "Unknown API error", [], None),
            # Malformed response (string)
            ("invalid json", "Unknown API error", [], None),
            # None response
            (None, "Failed to parse error response: None", [], None),
            # Multiple error codes (should use first one)
            (
                {
                    "errors": [
                        {"detail": "First error", "code": "FIRST_CODE"},
                        {"detail": "Second error", "code": "SECOND_CODE"},
                    ]
                },
                "First error; Second error",
                ["First error", "Second error"],
                "FIRST_CODE",
            ),
            # Non-dict error objects
            (
                {"errors": ["Simple string error", {"detail": "Dict error"}]},
                "Dict error",
                ["Dict error"],
                None,
            ),
        ],
    )
    def test_parse_various_formats(
        self, response_data, expected_message, expected_errors, expected_code
    ):
        """Test parsing various error response formats."""
        result = parse_tfe_error_response(response_data)

        assert result["message"] == expected_message
        assert result["errors"] == expected_errors
        assert result["error_code"] == expected_code


class TestHandleHttpError:
    """Test cases for handle_http_error function."""

    @pytest.mark.parametrize(
        "status_code,expected_exception_class,expected_message",
        [
            (
                401,
                TFEUnauthorizedException,
                "Authentication failed - invalid or missing token",
            ),
            (403, TFEForbiddenException, "Access forbidden - insufficient permissions"),
            (404, TFENotFoundException, "Resource not found"),
            (422, TFEValidationException, "Name is required; Email is invalid"),
            (500, TFEServerException, "TFE server error"),
            (502, TFEServerException, "TFE server error"),
            (503, TFEServerException, "TFE server error"),
            (504, TFEServerException, "TFE server error"),
            (418, TFEEndpointException, "HTTP error occurred"),  # Unknown status
        ],
    )
    def test_status_code_mapping(
        self, status_code, expected_exception_class, expected_message
    ):
        """Test that status codes map to correct exception types."""
        method, path = "GET", "/test/path"

        mock_response = Mock()
        mock_response.status_code = status_code
        if status_code == 422:
            mock_response.json.return_value = {
                "errors": [
                    {"detail": "Name is required"},
                    {"detail": "Email is invalid"},
                ]
            }
        else:
            mock_response.json.return_value = {"error": "Test error"}

        mock_http_error = exceptions.HTTPError(f"{status_code} Error")
        mock_http_error.response = mock_response

        with pytest.raises(expected_exception_class) as exc_info:
            handle_http_error(method, path, mock_http_error)

        exception = exc_info.value
        assert exception.message == expected_message
        assert exception.status_code == status_code
        assert exception.method == method
        assert exception.path == path
        assert exception.cause == mock_http_error

    @pytest.mark.parametrize(
        "method,path,json_response,expected_message",
        [
            # Test 422 validation error with parsed error message
            (
                "POST",
                "/api/workspaces",
                {
                    "errors": [
                        {"detail": "Name is required"},
                        {"detail": "Email format is invalid"},
                    ]
                },
                "Name is required; Email format is invalid",
            ),
            # Test 422 validation error with fallback message when parsing fails
            (
                "POST",
                "/api/workspaces",
                {"unknown_format": "data"},
                "Unknown API error",  # Actual fallback message from parse_tfe_error_response
            ),
        ],
    )
    def test_validation_error_scenarios(
        self, method, path, json_response, expected_message
    ):
        """Test various 422 validation error scenarios."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = json_response

        mock_http_error = exceptions.HTTPError("422 Validation Error")
        mock_http_error.response = mock_response

        with pytest.raises(TFEValidationException) as exc_info:
            handle_http_error(method, path, mock_http_error)

        exception = exc_info.value
        assert exception.message == expected_message
        assert exception.status_code == 422
        assert exception.error_data == json_response

    def test_error_data_preservation(self):
        """Test that error data is preserved in the exception."""
        method, path = "GET", "/test"

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "Bad Request",
            "details": {"field": "value"},
        }

        mock_http_error = exceptions.HTTPError("400 Bad Request")
        mock_http_error.response = mock_response

        with pytest.raises(TFEEndpointException) as exc_info:
            handle_http_error(method, path, mock_http_error)

        exception = exc_info.value
        assert exception.error_data == mock_response.json.return_value
        assert exception.error_data["error"] == "Bad Request"
        assert exception.error_data["details"]["field"] == "value"

    def test_logging_behavior(self, mocker):
        """Test that appropriate logging occurs."""
        mock_logger = mocker.patch("tfe.error_utils.logger")

        method, path = "GET", "/test"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}

        mock_http_error = exceptions.HTTPError("404 Not Found")
        mock_http_error.response = mock_response

        with pytest.raises(TFENotFoundException):
            handle_http_error(method, path, mock_http_error)

        # Verify that error logging occurred
        mock_logger.error.assert_called_once()
        log_call_args = mock_logger.error.call_args[0]
        assert "HTTP error while making" in log_call_args[0]
        assert method in log_call_args[1]
        assert path in log_call_args[2]
        assert (
            log_call_args[3] == mock_http_error
        )  # The error object is passed directly
        assert log_call_args[4] == 404  # Status code is an integer
