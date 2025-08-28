"""Unit tests for the BaseService abstract class."""

from unittest.mock import Mock

import pytest

from tfe.base_service import BaseService


# Mock model class for testing
class MockResource:
    """Mock resource model for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return (
            f"MockResource({', '.join(f'{k}={v}' for k, v in self.__dict__.items())})"
        )


# Mock service implementation for testing
class MockService(BaseService[MockResource]):
    """Mock service implementation for testing BaseService."""

    def __init__(self, client):
        super().__init__(client)
        self.resource_type = "mock-resources"

    def list(self, **kwargs):
        """List resources."""
        self._log_request("GET", "mock-resources", **kwargs)
        params = self._build_query_params(**kwargs)
        response = self._make_request("GET", "mock-resources", params=params)
        return self._handle_response(response, MockResource)

    def get(self, resource_id: str, **kwargs):
        """Get a single resource."""
        self._log_request("GET", f"mock-resources/{resource_id}", **kwargs)
        params = self._build_query_params(**kwargs)
        response = self._make_request(
            "GET", f"mock-resources/{resource_id}", params=params
        )
        return self._handle_response(response, MockResource)

    def create(self, data: dict):
        """Create a resource."""
        self._log_request("POST", "mock-resources", data=data)
        jsonapi_data = self._prepare_jsonapi_data(data, self.resource_type)
        response = self._make_request("POST", "mock-resources", json=jsonapi_data)
        return self._handle_response(response, MockResource)

    def update(self, resource_id: str, data: dict):
        """Update a resource."""
        self._log_request("PATCH", f"mock-resources/{resource_id}", data=data)
        jsonapi_data = self._prepare_jsonapi_data(data, self.resource_type)
        response = self._make_request(
            "PATCH", f"mock-resources/{resource_id}", json=jsonapi_data
        )
        return self._handle_response(response, MockResource)

    def delete(self, resource_id: str):
        """Delete a resource."""
        self._log_request("DELETE", f"mock-resources/{resource_id}")
        response = self._make_request("DELETE", f"mock-resources/{resource_id}")
        return response.status_code == 204


@pytest.fixture
def mock_client():
    """Provide a mock client for testing."""
    client = Mock()
    client.base_url = "https://app.terraform.io/api/v2/"
    return client


@pytest.fixture
def mock_http_client():
    """Provide a mock HTTP client for testing."""
    return Mock()


@pytest.fixture
def mock_service(mock_client, mock_http_client):
    """Provide a mock service instance for testing."""
    mock_client.config.http_client = mock_http_client
    return MockService(mock_client)


class TestBaseService:
    """Test the BaseService abstract class."""

    def test_initialization(self, mock_client):
        """Test service initialization."""
        service = MockService(mock_client)
        assert service.client == mock_client
        assert service.resource_type == "mock-resources"

    def test_make_request_get(self, mock_service, mock_http_client):
        """Test GET request handling."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.get.return_value = mock_response

        # Make request
        response = mock_service._make_request("GET", "test-endpoint")

        # Verify
        assert response == mock_response
        mock_http_client.get.assert_called_once_with(
            "https://app.terraform.io/api/v2/test-endpoint"
        )

    def test_make_request_post(self, mock_service, mock_http_client):
        """Test POST request handling."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_http_client.post.return_value = mock_response

        # Make request
        response = mock_service._make_request(
            "POST", "test-endpoint", json={"test": "data"}
        )

        # Verify
        assert response == mock_response
        mock_http_client.post.assert_called_once_with(
            "https://app.terraform.io/api/v2/test-endpoint", json={"test": "data"}
        )

    def test_make_request_put(self, mock_service, mock_http_client):
        """Test PUT request handling."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.put.return_value = mock_response

        # Make request
        response = mock_service._make_request(
            "PUT", "test-endpoint", json={"test": "data"}
        )

        # Verify
        assert response == mock_response
        mock_http_client.put.assert_called_once_with(
            "https://app.terraform.io/api/v2/test-endpoint", json={"test": "data"}
        )

    def test_make_request_patch(self, mock_service, mock_http_client):
        """Test PATCH request handling."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.patch.return_value = mock_response

        # Make request
        response = mock_service._make_request(
            "PATCH", "test-endpoint", json={"test": "data"}
        )

        # Verify
        assert response == mock_response
        mock_http_client.patch.assert_called_once_with(
            "https://app.terraform.io/api/v2/test-endpoint", json={"test": "data"}
        )

    def test_make_request_delete(self, mock_service, mock_http_client):
        """Test DELETE request handling."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_http_client.delete.return_value = mock_response

        # Make request
        response = mock_service._make_request("DELETE", "test-endpoint")

        # Verify
        assert response == mock_response
        mock_http_client.delete.assert_called_once_with(
            "https://app.terraform.io/api/v2/test-endpoint"
        )

    def test_make_request_invalid_method(self, mock_service):
        """Test invalid HTTP method handling."""
        with pytest.raises(ValueError, match="Unsupported HTTP method: INVALID"):
            mock_service._make_request("INVALID", "test-endpoint")

    def test_make_request_url_building(self, mock_service, mock_http_client):
        """Test URL building with different path combinations."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.get.return_value = mock_response

        # Test with leading slash in path
        mock_service._make_request("GET", "/test-endpoint")
        mock_http_client.get.assert_called_with(
            "https://app.terraform.io/api/v2/test-endpoint"
        )

        # Test with trailing slash in base_url
        mock_service.client.base_url = "https://app.terraform.io/api/v2/"
        mock_service._make_request("GET", "test-endpoint")
        mock_http_client.get.assert_called_with(
            "https://app.terraform.io/api/v2/test-endpoint"
        )

    def test_build_query_params(self, mock_service):
        """Test query parameter building."""
        params = mock_service._build_query_params(page=1, per_page=10, search="test")
        assert params["page"] == "1"
        assert params["per_page"] == "10"
        assert params["search"] == "test"

    def test_prepare_jsonapi_data(self, mock_service):
        """Test JSONAPI data preparation."""
        data = {"name": "test", "description": "test description"}
        jsonapi_data = mock_service._prepare_jsonapi_data(data, "workspaces")

        assert jsonapi_data["data"]["type"] == "workspaces"
        assert jsonapi_data["data"]["attributes"]["name"] == "test"

    def test_handle_response_no_content(self, mock_service):
        """Test handling of 204 No Content responses."""
        mock_response = Mock()
        mock_response.status_code = 204

        result = mock_service._handle_response(mock_response)
        assert result is None

    def test_handle_response_jsonapi(self, mock_service):
        """Test handling of JSONAPI responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
            }
        }

        result = mock_service._handle_response(mock_response, MockResource)
        assert isinstance(result, MockResource)
        assert result.id == "ws-123"
        assert result.name == "test-workspace"

    def test_handle_response_regular_json(self, mock_service):
        """Test handling of regular JSON responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "test", "id": "123"}

        result = mock_service._handle_response(mock_response, MockResource)
        assert isinstance(result, MockResource)
        assert result.name == "test"
        assert result.id == "123"

    def test_handle_response_parse_error(self, mock_service):
        """Test handling of JSON parse errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "raw response text"

        result = mock_service._handle_response(mock_response)
        assert result == "raw response text"

    def test_log_request(self, mock_service, caplog):
        """Test logging functionality."""
        with caplog.at_level("DEBUG"):
            mock_service._log_request("GET", "test-endpoint", page=1)

        assert "Making GET request to test-endpoint" in caplog.text
        assert "Request parameters: {'page': 1}" in caplog.text


class TestMockService:
    """Test the concrete mock service implementation."""

    def test_list_resources(self, mock_service, mock_http_client):
        """Test listing resources."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "ws-1",
                    "type": "workspaces",
                    "attributes": {"name": "workspace-1"},
                }
            ]
        }
        mock_http_client.get.return_value = mock_response

        # Call service method
        result = mock_service.list(page=1, per_page=10)

        # Verify
        assert len(result) == 1
        assert result[0].id == "ws-1"
        assert result[0].name == "workspace-1"

        # Verify HTTP call
        mock_http_client.get.assert_called_once()
        call_args = mock_http_client.get.call_args
        assert call_args[0][0] == "https://app.terraform.io/api/v2/mock-resources"
        assert call_args[1]["params"] == {"page": "1", "per_page": "10"}

    def test_get_resource(self, mock_service, mock_http_client):
        """Test getting a single resource."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
            }
        }
        mock_http_client.get.return_value = mock_response

        # Call service method
        result = mock_service.get("ws-123")

        # Verify
        assert result.id == "ws-123"
        assert result.name == "test-workspace"

        # Verify HTTP call
        mock_http_client.get.assert_called_once_with(
            "https://app.terraform.io/api/v2/mock-resources/ws-123", params={}
        )

    def test_create_resource(self, mock_service, mock_http_client):
        """Test creating a resource."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "data": {
                "id": "ws-new",
                "type": "workspaces",
                "attributes": {"name": "new-workspace"},
            }
        }
        mock_http_client.post.return_value = mock_response

        # Call service method
        data = {"name": "new-workspace"}
        result = mock_service.create(data)

        # Verify
        assert result.id == "ws-new"
        assert result.name == "new-workspace"

        # Verify HTTP call
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args[1]["json"]["data"]["type"] == "mock-resources"
        assert call_args[1]["json"]["data"]["attributes"]["name"] == "new-workspace"

    def test_update_resource(self, mock_service, mock_http_client):
        """Test updating a resource."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "updated-workspace"},
            }
        }
        mock_http_client.patch.return_value = mock_response

        # Call service method
        data = {"name": "updated-workspace"}
        result = mock_service.update("ws-123", data)

        # Verify
        assert result.id == "ws-123"
        assert result.name == "updated-workspace"

        # Verify HTTP call
        mock_http_client.patch.assert_called_once()
        call_args = mock_http_client.patch.call_args
        assert (
            call_args[0][0] == "https://app.terraform.io/api/v2/mock-resources/ws-123"
        )

    def test_delete_resource(self, mock_service, mock_http_client):
        """Test deleting a resource."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_http_client.delete.return_value = mock_response

        # Call service method
        result = mock_service.delete("ws-123")

        # Verify
        assert result is True

        # Verify HTTP call
        mock_http_client.delete.assert_called_once_with(
            "https://app.terraform.io/api/v2/mock-resources/ws-123"
        )

    def test_delete_resource_failure(self, mock_service, mock_http_client):
        """Test deleting a resource with failure response."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_http_client.delete.return_value = mock_response

        # Call service method
        result = mock_service.delete("ws-123")

        # Verify
        assert result is False
