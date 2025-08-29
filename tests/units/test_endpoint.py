"""Tests for the endpoint module."""

import pytest
from requests import Session
from requests.models import Response as RequestResponse

from tfe.endpoint import Endpoint


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
        """Test that unsupported HTTP methods raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported HTTP method: INVALID"):
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
