"""Tests for the endpoint module."""

import pytest
from requests import Session, exceptions
from requests.models import Response as RequestResponse

from tfe.endpoint import Endpoint
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


@pytest.fixture
def mock_session(mocker):
    """Create a mock session for testing."""
    return mocker.Mock(spec=Session)


@pytest.fixture
def endpoint(mock_session):
    """Create an Endpoint instance for testing."""
    return Endpoint(client=mock_session)


@pytest.fixture
def mock_response(mocker):
    """Create a mock HTTP response."""
    response = mocker.Mock(spec=RequestResponse)
    response.status_code = 200
    response.json.return_value = {"data": "test"}
    return response


class TestEndpoint:
    """Test cases for the Endpoint class."""

    @pytest.mark.parametrize(
        "method,expected_method,json_data,expected_call",
        [
            ("GET", "get", None, ("get", "/test/path")),
            ("POST", "post", {"key": "value"}, ("post", "/test/path")),
            ("PUT", "put", {"key": "value"}, ("put", "/test/path")),
            ("PATCH", "patch", {"key": "value"}, ("patch", "/test/path")),
            ("DELETE", "delete", None, ("delete", "/test/path")),
            ("get", "get", None, ("get", "/test/path")),  # Test case insensitive
            (
                "post",
                "post",
                {"data": "test"},
                ("post", "/test/path"),
            ),  # Test case insensitive
        ],
    )
    def test_make_request_all_methods(
        self, endpoint, mock_response, method, expected_method, json_data, expected_call
    ):
        """Test _make_request with all supported HTTP methods."""
        # Setup the mock method to return our mock response
        getattr(endpoint._http_client, expected_method).return_value = mock_response

        # Make the request
        if json_data:
            response = endpoint._make_request(method, "/test/path", json=json_data)
            # Verify the correct method was called with the correct arguments
            getattr(endpoint._http_client, expected_method).assert_called_once_with(
                "/test/path", json=json_data
            )
        else:
            response = endpoint._make_request(method, "/test/path")
            # Verify the correct method was called with the correct arguments
            getattr(endpoint._http_client, expected_method).assert_called_once_with(
                "/test/path"
            )

        # Verify the response is returned correctly
        assert response == mock_response

    def test_make_request_unsupported_method(self, endpoint):
        """Test that unsupported HTTP methods raise TFEEndpointException."""
        with pytest.raises(
            TFEEndpointException,
            match="Unexpected error occurred during INVALID request",
        ):
            endpoint._make_request("INVALID", "/test/path")

    def test_get_method(self, endpoint, mock_response):
        """Test the _get convenience method."""
        endpoint._http_client.get.return_value = mock_response

        response = endpoint._get("/test/path")

        endpoint._http_client.get.assert_called_once_with("/test/path")
        assert response == mock_response

    def test_post_method(self, endpoint, mock_response):
        """Test the _post convenience method."""
        endpoint._http_client.post.return_value = mock_response
        test_data = {"key": "value"}

        response = endpoint._post("/test/path", test_data)

        endpoint._http_client.post.assert_called_once_with("/test/path", json=test_data)
        assert response == mock_response

    def test_put_method(self, endpoint, mock_response):
        """Test the _put convenience method."""
        endpoint._http_client.put.return_value = mock_response
        test_data = {"key": "value"}

        response = endpoint._put("/test/path", test_data)

        endpoint._http_client.put.assert_called_once_with("/test/path", json=test_data)
        assert response == mock_response

    def test_patch_method(self, endpoint, mock_response):
        """Test the _patch convenience method."""
        endpoint._http_client.patch.return_value = mock_response
        test_data = {"key": "value"}

        response = endpoint._patch("/test/path", test_data)

        endpoint._http_client.patch.assert_called_once_with(
            "/test/path", json=test_data
        )
        assert response == mock_response

    def test_delete_method(self, endpoint, mock_response):
        """Test the _delete convenience method."""
        endpoint._http_client.delete.return_value = mock_response

        response = endpoint._delete("/test/path")

        endpoint._http_client.delete.assert_called_once_with("/test/path")
        assert response == mock_response


class TestEndpointErrorHandling:
    """Test cases for endpoint error handling."""

    @pytest.mark.parametrize(
        "handler,error_class,error_msg,error_type",
        [
            (
                "_handle_connection_error",
                TFEConnectionException,
                "Failed to connect to TFE API",
                exceptions.ConnectionError,
            ),
            (
                "_handle_timeout_error",
                TFETimeoutException,
                "Request timed out",
                exceptions.Timeout,
            ),
            (
                "_handle_request_error",
                TFEEndpointException,
                "Request failed: Request failed",
                exceptions.RequestException,
            ),
            (
                "_handle_unexpected_error",
                TFEEndpointException,
                "Unexpected error occurred during DELETE request",
                ValueError,
            ),
        ],
    )
    def test_error_handlers(
        self, endpoint, handler, error_class, error_msg, error_type
    ):
        """Test all error handler methods."""
        method, path = "DELETE", "/test/path"
        error = error_type("Request failed")

        with pytest.raises(error_class) as exc_info:
            getattr(endpoint, handler)(method, path, error)

        exception = exc_info.value
        assert exception.message == error_msg
        assert exception.method == method
        assert exception.path == path
        assert exception.cause == error

    @pytest.mark.parametrize(
        "response_data,expected",
        [
            ({"error": "test"}, {"error": "test"}),
            ({"text": "Error text"}, {"text": "Error text"}),
            (None, None),
        ],
    )
    def test_extract_error_data(self, endpoint, mocker, response_data, expected):
        """Test error data extraction from various response types."""
        if response_data is None:
            result = endpoint._extract_error_data(None)
        else:
            mock_response = mocker.Mock()
            if "error" in response_data:
                mock_response.json.return_value = response_data
                result = endpoint._extract_error_data(mock_response)
            else:  # text case
                mock_response.json.side_effect = ValueError("Invalid JSON")
                mock_response.text = response_data["text"]
                result = endpoint._extract_error_data(mock_response)

        assert result == expected


class TestEndpointHTTPErrorHandling:
    """Test cases for HTTP error handling."""

    @pytest.mark.parametrize(
        "status_code,exception_class,expected_message",
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
            (418, TFEEndpointException, "HTTP error occurred"),  # Unknown status
        ],
    )
    def test_handle_http_error_status_codes(
        self, endpoint, mocker, status_code, exception_class, expected_message
    ):
        """Test HTTP error handling for different status codes."""
        method, path = "GET", "/test/path"

        mock_response = mocker.Mock()
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

        with pytest.raises(exception_class) as exc_info:
            endpoint._handle_http_error(method, path, mock_http_error)

        exception = exc_info.value
        assert exception.message == expected_message
        assert exception.status_code == status_code
        assert exception.method == method
        assert exception.path == path

    def test_handle_http_error_no_response(self, endpoint):
        """Test HTTP error handling with no response."""
        mock_http_error = exceptions.HTTPError("HTTP Error")
        mock_http_error.response = None

        with pytest.raises(TFEEndpointException) as exc_info:
            endpoint._handle_http_error("GET", "/test", mock_http_error)

        assert exc_info.value.message == "HTTP error occurred"
        assert exc_info.value.status_code is None


class TestEndpointIntegration:
    """Integration tests for endpoint error handling."""

    @pytest.mark.parametrize(
        "method,error_type,exception_class,expected_message",
        [
            (
                "GET",
                exceptions.ConnectionError,
                TFEConnectionException,
                "Failed to connect to TFE API",
            ),
            ("POST", exceptions.Timeout, TFETimeoutException, "Request timed out"),
        ],
    )
    def test_make_request_errors(
        self, endpoint, method, error_type, exception_class, expected_message
    ):
        """Test _make_request with various error types."""
        path = "/test/path"
        getattr(endpoint._http_client, method.lower()).side_effect = error_type(
            "Test error"
        )

        with pytest.raises(exception_class) as exc_info:
            endpoint._make_request(method, path)

        assert exc_info.value.message == expected_message
        assert exc_info.value.method == method
        assert exc_info.value.path == path

    def test_make_request_http_error(self, endpoint, mocker):
        """Test _make_request with HTTP error."""
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.raise_for_status.side_effect = exceptions.HTTPError(
            "401 Unauthorized"
        )
        mock_response.raise_for_status.side_effect.response = mock_response

        endpoint._http_client.get.return_value = mock_response

        with pytest.raises(TFEUnauthorizedException) as exc_info:
            endpoint._make_request("GET", "/test")

        assert exc_info.value.status_code == 401

    def test_make_request_success(self, endpoint, mock_response):
        """Test successful _make_request."""
        endpoint._http_client.get.return_value = mock_response
        response = endpoint._make_request("GET", "/test")
        assert response == mock_response


class TestEndpointErrorParsing:
    """Test cases for error response parsing."""

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
            # Malformed input
            ("invalid json", "Unknown API error", [], None),
        ],
    )
    def test_parse_tfe_error_response_formats(
        self, endpoint, response_data, expected_message, expected_errors, expected_code
    ):
        """Test parsing various error response formats."""
        result = endpoint.parse_tfe_error_response(response_data)

        assert result["message"] == expected_message
        assert result["errors"] == expected_errors
        assert result["error_code"] == expected_code

    def test_parse_tfe_error_response_none(self, endpoint):
        """Test parsing None response."""
        result = endpoint.parse_tfe_error_response(None)
        assert result["message"] == "Failed to parse error response: None"
