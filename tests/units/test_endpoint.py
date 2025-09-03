"""Tests for the endpoint module."""

import pytest
from requests import Session, exceptions
from requests.models import Response as RequestResponse

from tfe.endpoint import Endpoint
from tfe.exception import (
    TFEConnectionException,
    TFEEndpointException,
    TFETimeoutException,
    TFEUnauthorizedException,
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


class TestEndpointErrorHandling:
    """Test cases for endpoint error handling."""

    @pytest.mark.parametrize(
        "method,http_method,exception_class,request_exception,expected_message,expected_cause_type",
        [
            (
                "GET",
                "get",
                TFEConnectionException,
                exceptions.ConnectionError("Connection failed"),
                "Failed to connect to TFE API",
                exceptions.ConnectionError,
            ),
            (
                "POST",
                "post",
                TFETimeoutException,
                exceptions.Timeout("Request timed out"),
                "Request timed out",
                exceptions.Timeout,
            ),
            (
                "PUT",
                "put",
                TFEEndpointException,
                exceptions.RequestException("Request failed"),
                "Request failed: Request failed",
                exceptions.RequestException,
            ),
            (
                "DELETE",
                "delete",
                TFEEndpointException,
                ValueError("Unexpected error"),
                "Unexpected error occurred during DELETE request",
                ValueError,
            ),
        ],
    )
    def test_error_handling(
        self,
        endpoint,
        method,
        http_method,
        exception_class,
        request_exception,
        expected_message,
        expected_cause_type,
    ):
        """Test various error handling scenarios."""
        path = "/test/path"
        getattr(endpoint._http_client, http_method).side_effect = request_exception

        with pytest.raises(exception_class) as exc_info:
            endpoint._make_request(method, path)

        exception = exc_info.value
        assert exception.message == expected_message
        assert exception.method == method
        assert exception.path == path
        assert isinstance(exception.cause, expected_cause_type)

    def test_http_error_handling(self, endpoint, mocker):
        """Test HTTP error handling (delegated to error_utils)."""
        method, path = "GET", "/test/path"

        # Mock the handle_http_error function to raise an exception
        mock_handle_http_error = mocker.patch("tfe.endpoint.handle_http_error")
        mock_handle_http_error.side_effect = TFEUnauthorizedException(
            message="Authentication failed", status_code=401, method=method, path=path
        )

        # Create mock response that raises HTTPError
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.raise_for_status.side_effect = exceptions.HTTPError(
            "401 Unauthorized"
        )
        mock_response.raise_for_status.side_effect.response = mock_response

        endpoint._http_client.get.return_value = mock_response

        # This should call handle_http_error and raise TFEUnauthorizedException
        with pytest.raises(TFEUnauthorizedException):
            endpoint._make_request(method, path)

        # Verify that handle_http_error was called
        mock_handle_http_error.assert_called_once()
