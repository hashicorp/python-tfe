"""Unit tests for workspace resources service."""

from unittest.mock import Mock

import pytest

from pytfe.models.workspace_resource import (
    WorkspaceResource,
    WorkspaceResourceListOptions,
)
from pytfe.resources.workspace_resources import WorkspaceResourcesService


class TestWorkspaceResourcesService:
    """Test suite for WorkspaceResourcesService."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock transport for testing."""
        return Mock()

    @pytest.fixture
    def service(self, mock_transport):
        """Create a WorkspaceResourcesService instance for testing."""
        return WorkspaceResourcesService(mock_transport)

    @pytest.fixture
    def sample_workspace_resource_response(self):
        """Sample API response for workspace resources list."""
        return {
            "data": [
                {
                    "id": "resource-1",
                    "type": "resources",
                    "attributes": {
                        "address": "media_bucket.aws_s3_bucket_public_access_block.this[0]",
                        "name": "this",
                        "created-at": "2023-01-01T00:00:00Z",
                        "updated-at": "2023-01-01T00:00:00Z",
                        "module": "media_bucket",
                        "provider": "hashicorp/aws",
                        "provider-type": "aws",
                        "modified-by-state-version-id": "sv-abc123",
                        "name-index": "0",
                    },
                },
                {
                    "id": "resource-2",
                    "type": "resources",
                    "attributes": {
                        "address": "aws_instance.example",
                        "name": "example",
                        "created-at": "2023-01-02T00:00:00Z",
                        "updated-at": "2023-01-02T00:00:00Z",
                        "module": "root",
                        "provider": "hashicorp/aws",
                        "provider-type": "aws",
                        "modified-by-state-version-id": "sv-def456",
                        "name-index": None,
                    },
                },
            ],
            "meta": {
                "pagination": {
                    "current_page": 1,
                    "total_pages": 1,
                    "total_count": 2,
                    "page_size": 20,
                }
            },
        }

    @pytest.fixture
    def sample_empty_response(self):
        """Sample API response for empty workspace resources list."""
        return {
            "data": [],
            "meta": {
                "pagination": {
                    "current_page": 1,
                    "total_pages": 1,
                    "total_count": 0,
                    "page_size": 20,
                }
            },
        }

    def test_list_workspace_resources_success(
        self, service, mock_transport, sample_workspace_resource_response
    ):
        """Test successful listing of workspace resources."""
        # Mock the transport response
        mock_response = Mock()
        mock_response.json.return_value = sample_workspace_resource_response
        mock_transport.request.return_value = mock_response

        # Call the service
        result = list(service.list("ws-abc123"))

        # Verify request was made correctly
        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/workspaces/ws-abc123/resources",
            params={"page[number]": 1, "page[size]": 100},
        )

        # Verify response parsing
        assert isinstance(result, list)
        assert len(result) == 2

        # Check first resource
        resource1 = result[0]
        assert isinstance(resource1, WorkspaceResource)
        assert resource1.id == "resource-1"
        assert (
            resource1.address
            == "media_bucket.aws_s3_bucket_public_access_block.this[0]"
        )
        assert resource1.name == "this"
        assert resource1.module == "media_bucket"
        assert resource1.provider == "hashicorp/aws"
        assert resource1.provider_type == "aws"
        assert resource1.modified_by_state_version_id == "sv-abc123"
        assert resource1.name_index == "0"
        assert resource1.created_at == "2023-01-01T00:00:00Z"
        assert resource1.updated_at == "2023-01-01T00:00:00Z"

        # Check second resource
        resource2 = result[1]
        assert resource2.id == "resource-2"
        assert resource2.address == "aws_instance.example"
        assert resource2.name == "example"
        assert resource2.module == "root"
        assert resource2.name_index is None

    def test_list_workspace_resources_with_options(
        self, service, mock_transport, sample_workspace_resource_response
    ):
        """Test listing workspace resources with pagination options."""
        # Mock the transport response
        mock_response = Mock()
        mock_response.json.return_value = sample_workspace_resource_response
        mock_transport.request.return_value = mock_response

        # Create options
        options = WorkspaceResourceListOptions(page_number=2, page_size=50)

        # Call the service
        result = list(service.list("ws-abc123", options))

        # Verify request was made correctly
        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/workspaces/ws-abc123/resources",
            params={"page[number]": 2, "page[size]": 50},
        )

        # Verify response
        assert isinstance(result, list)
        assert len(result) == 2

    def test_list_workspace_resources_empty(
        self, service, mock_transport, sample_empty_response
    ):
        """Test listing workspace resources when no resources exist."""
        # Mock the transport response
        mock_response = Mock()
        mock_response.json.return_value = sample_empty_response
        mock_transport.request.return_value = mock_response

        # Call the service
        result = list(service.list("ws-abc123"))

        # Verify request was made correctly
        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/workspaces/ws-abc123/resources",
            params={"page[number]": 1, "page[size]": 100},
        )

        # Verify response
        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_workspace_resources_invalid_workspace_id(self, service):
        """Test listing workspace resources with invalid workspace ID."""
        with pytest.raises(ValueError, match="workspace_id is required"):
            list(service.list(""))

        with pytest.raises(ValueError, match="workspace_id is required"):
            list(service.list(None))

    def test_list_workspace_resources_malformed_response(self, service, mock_transport):
        """Test handling of malformed API response."""
        # Mock malformed response
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "response"}
        mock_transport.request.return_value = mock_response

        # Call the service
        result = list(service.list("ws-abc123"))

        # Should handle gracefully and return empty list
        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_workspace_resources_api_error(self, service, mock_transport):
        """Test handling of API errors."""
        # Mock API error
        mock_transport.request.side_effect = Exception("API Error")

        # Should propagate the exception
        with pytest.raises(Exception, match="API Error"):
            list(service.list("ws-abc123"))


class TestWorkspaceResourceModel:
    """Test suite for WorkspaceResource model."""

    def test_workspace_resource_creation(self):
        """Test creating a WorkspaceResource instance."""
        resource = WorkspaceResource(
            id="resource-1",
            address="aws_instance.example",
            name="example",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            module="root",
            provider="hashicorp/aws",
            provider_type="aws",
            modified_by_state_version_id="sv-abc123",
            name_index="0",
        )

        assert resource.id == "resource-1"
        assert resource.address == "aws_instance.example"
        assert resource.name == "example"
        assert resource.module == "root"
        assert resource.provider == "hashicorp/aws"
        assert resource.provider_type == "aws"
        assert resource.modified_by_state_version_id == "sv-abc123"
        assert resource.name_index == "0"

    def test_workspace_resource_optional_fields(self):
        """Test WorkspaceResource with optional fields."""
        resource = WorkspaceResource(
            id="resource-1",
            address="aws_instance.example",
            name="example",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            module="root",
            provider="hashicorp/aws",
            provider_type="aws",
            modified_by_state_version_id="sv-abc123",
            # name_index is optional
        )

        assert resource.name_index is None


class TestWorkspaceResourceListOptions:
    """Test suite for WorkspaceResourceListOptions model."""

    def test_workspace_resource_list_options_creation(self):
        """Test creating WorkspaceResourceListOptions."""
        options = WorkspaceResourceListOptions(page_number=2, page_size=50)

        assert options.page_number == 2
        assert options.page_size == 50

    def test_workspace_resource_list_options_defaults(self):
        """Test WorkspaceResourceListOptions with defaults."""
        options = WorkspaceResourceListOptions()

        # Should use default values from BaseListOptions
        assert options.page_number is None
        assert options.page_size is None
