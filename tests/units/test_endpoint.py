"""Unit tests for the Endpoint class."""

from typing import Any
from unittest.mock import Mock

import pytest

from tfe.endpoint import Endpoint, ResourceDataProtocol, ResourceResponseProtocol


class MockResourceData:
    """Mock resource data for testing."""

    def __init__(self, id: str, type: str, **attributes: Any):
        self.id = id
        self.type = type
        self.attributes = attributes


class MockResourceResponse:
    """Mock resource response for testing."""

    def __init__(self, data: ResourceDataProtocol | list[ResourceDataProtocol]):
        self.data = data


# Mock service implementation for testing
class MockService(Endpoint):
    """Mock service implementation for testing Endpoint."""

    def list_resources(
        self,
        page: int | None = None,
        per_page: int | None = None,
        search: str | None = None,
        include: list[str] | None = None,
        filter: dict[str, str] | None = None,
        sort: str | None = None,
        **additional_params: Any,
    ) -> ResourceResponseProtocol:
        """List resources."""
        # Build parameters dict
        params = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if search is not None:
            params["search"] = search
        if include is not None:
            params["include"] = include
        if filter is not None:
            params["filter"] = filter
        if sort is not None:
            params["sort"] = sort
        # Add additional params
        params.update(additional_params)

        self._make_request("GET", "mock-resources", **params)
        mock_data = MockResourceData(id="1", type="mock", name="test")
        return MockResourceResponse(data=[mock_data])

    def get_resource(
        self,
        resource_id: str,
        include: list[str] | None = None,
        **additional_params: Any,
    ) -> ResourceResponseProtocol:
        """Get a single resource."""
        self._make_request("GET", f"mock-resources/{resource_id}", **additional_params)
        mock_data = MockResourceData(id=resource_id, type="mock", name="test")
        return MockResourceResponse(data=mock_data)

    def create_resource(
        self, data: dict[str, Any], **additional_params: Any
    ) -> ResourceResponseProtocol:
        """Create a resource."""
        self._make_request("POST", "mock-resources", json=data)
        mock_data = MockResourceData(id="new", type="mock", **data)
        return MockResourceResponse(data=mock_data)

    def update_resource(
        self, resource_id: str, data: dict[str, Any], **additional_params: Any
    ) -> ResourceResponseProtocol:
        """Update a resource."""
        self._make_request("PATCH", f"mock-resources/{resource_id}", json=data)
        mock_data = MockResourceData(id=resource_id, type="mock", **data)
        return MockResourceResponse(data=mock_data)

    def delete_resource(self, resource_id: str, **additional_params: Any) -> bool:
        """Delete a resource."""
        response = self._make_request("DELETE", f"mock-resources/{resource_id}")
        return response.status_code == 204


class TestEndpoint:
    """Test the Endpoint class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client with standard configuration."""
        mock_client = Mock()
        mock_client.config = Mock()
        mock_client.config.http_client = Mock()
        mock_client.base_url = "https://api.example.com"
        return mock_client

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        return Mock()

    @pytest.fixture
    def mock_response(self):
        """Create a mock response."""
        return Mock()

    def _setup_endpoint(self, mock_client, mock_http_client, mock_response):
        """Helper method to setup endpoint with mocked dependencies."""
        mock_http_client.get.return_value = mock_response
        mock_http_client.post.return_value = mock_response
        mock_http_client.put.return_value = mock_response
        mock_http_client.patch.return_value = mock_response
        mock_http_client.delete.return_value = mock_response

        mock_client.config.http_client = mock_http_client
        return MockService(mock_client)

    def test_init(self, mock_client):
        """Test endpoint initialization."""
        endpoint = MockService(mock_client)

        assert endpoint._http_client == mock_client.config.http_client
        assert endpoint._base_url == "https://api.example.com"

    def test_make_request_get(self, mock_client, mock_http_client, mock_response):
        """Test making a GET request."""
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint._make_request("GET", "test-endpoint")

        mock_http_client.get.assert_called_once_with(
            "https://api.example.com/test-endpoint"
        )
        assert result == mock_response

    def test_make_request_post(self, mock_client, mock_http_client, mock_response):
        """Test making a POST request."""
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint._make_request("POST", "test-endpoint", json={"key": "value"})

        mock_http_client.post.assert_called_once_with(
            "https://api.example.com/test-endpoint", json={"key": "value"}
        )
        assert result == mock_response

    def test_make_request_put(self, mock_client, mock_http_client, mock_response):
        """Test making a PUT request."""
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint._make_request("PUT", "test-endpoint", json={"key": "value"})

        mock_http_client.put.assert_called_once_with(
            "https://api.example.com/test-endpoint", json={"key": "value"}
        )
        assert result == mock_response

    def test_make_request_patch(self, mock_client, mock_http_client, mock_response):
        """Test making a PATCH request."""
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint._make_request("PATCH", "test-endpoint", json={"key": "value"})

        mock_http_client.patch.assert_called_once_with(
            "https://api.example.com/test-endpoint", json={"key": "value"}
        )
        assert result == mock_response

    def test_make_request_delete(self, mock_client, mock_http_client, mock_response):
        """Test making a DELETE request."""
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint._make_request("DELETE", "test-endpoint")

        mock_http_client.delete.assert_called_once_with(
            "https://api.example.com/test-endpoint"
        )
        assert result == mock_response

    def test_make_request_invalid_method(self, mock_client):
        """Test making a request with an invalid HTTP method."""
        endpoint = MockService(mock_client)

        with pytest.raises(ValueError, match="Unsupported HTTP method: INVALID"):
            endpoint._make_request("INVALID", "test-endpoint")

    def test_make_request_with_base_url_trailing_slash(
        self, mock_client, mock_http_client, mock_response
    ):
        """Test making a request with a base URL that has a trailing slash."""
        mock_client.base_url = "https://api.example.com/"
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint._make_request("GET", "test-endpoint")

        mock_http_client.get.assert_called_once_with(
            "https://api.example.com/test-endpoint"
        )
        assert result == mock_response

    def test_make_request_with_path_leading_slash(
        self, mock_client, mock_http_client, mock_response
    ):
        """Test making a request with a path that has a leading slash."""
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint._make_request("GET", "/test-endpoint")

        mock_http_client.get.assert_called_once_with(
            "https://api.example.com/test-endpoint"
        )
        assert result == mock_response

    def test_list_resources(self, mock_client, mock_http_client, mock_response):
        """Test list_resources method."""
        mock_response.status_code = 200
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint.list_resources(page=1, per_page=10)

        mock_http_client.get.assert_called_once_with(
            "https://api.example.com/mock-resources", page=1, per_page=10
        )
        assert isinstance(result, MockResourceResponse)
        assert isinstance(result.data, list)
        assert len(result.data) == 1
        assert result.data[0].id == "1"
        assert result.data[0].type == "mock"
        assert result.data[0].attributes["name"] == "test"

    def test_get_resource(self, mock_client, mock_http_client, mock_response):
        """Test get_resource method."""
        mock_response.status_code = 200
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint.get_resource("test-123")

        mock_http_client.get.assert_called_once_with(
            "https://api.example.com/mock-resources/test-123"
        )
        assert isinstance(result, MockResourceResponse)
        assert isinstance(result.data, MockResourceData)
        assert result.data.id == "test-123"
        assert result.data.type == "mock"
        assert result.data.attributes["name"] == "test"

    def test_create_resource(self, mock_client, mock_http_client, mock_response):
        """Test create_resource method."""
        mock_response.status_code = 201
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        data = {"name": "new-resource", "description": "A new resource"}
        result = endpoint.create_resource(data)

        mock_http_client.post.assert_called_once_with(
            "https://api.example.com/mock-resources", json=data
        )
        assert isinstance(result, MockResourceResponse)
        assert isinstance(result.data, MockResourceData)
        assert result.data.id == "new"
        assert result.data.type == "mock"
        assert result.data.attributes["name"] == "new-resource"
        assert result.data.attributes["description"] == "A new resource"

    def test_update_resource(self, mock_client, mock_http_client, mock_response):
        """Test update_resource method."""
        mock_response.status_code = 200
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        data = {"name": "updated-resource"}
        result = endpoint.update_resource("test-123", data)

        mock_http_client.patch.assert_called_once_with(
            "https://api.example.com/mock-resources/test-123", json=data
        )
        assert isinstance(result, MockResourceResponse)
        assert isinstance(result.data, MockResourceData)
        assert result.data.id == "test-123"
        assert result.data.type == "mock"
        assert result.data.attributes["name"] == "updated-resource"

    def test_delete_resource(self, mock_client, mock_http_client, mock_response):
        """Test delete_resource method."""
        mock_response.status_code = 204
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint.delete_resource("test-123")

        mock_http_client.delete.assert_called_once_with(
            "https://api.example.com/mock-resources/test-123"
        )
        assert result is True

    def test_delete_resource_failure(
        self, mock_client, mock_http_client, mock_response
    ):
        """Test delete_resource method when deletion fails."""
        mock_response.status_code = 404
        endpoint = self._setup_endpoint(mock_client, mock_http_client, mock_response)
        result = endpoint.delete_resource("test-123")

        mock_http_client.delete.assert_called_once_with(
            "https://api.example.com/mock-resources/test-123"
        )
        assert result is False