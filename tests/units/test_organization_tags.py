from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from pytfe import TFEClient, TFEConfig
from pytfe.errors import (
    InvalidOrgError,
    InvalidTagIDError,
    RequiredTagIDError,
    RequiredTagWorkspaceIDError,
)
from pytfe.models.organization_tag import (
    AddWorkspacesToTagOptions,
    OrganizationTag,
    OrganizationTagsDeleteOptions,
    OrganizationTagsListOptions,
)


class TestOrganizationTagModels:
    """Test organization tag models and validation."""

    def test_organization_tag_model_basic(self):
        """Test basic OrganizationTag model creation."""
        tag = OrganizationTag(
            id="tag-test123",
            name="production",
            instance_count=5,
            created_at=datetime.now(),
            organization_name="test-org",
        )
        assert tag.id == "tag-test123"
        assert tag.name == "production"
        assert tag.instance_count == 5
        assert tag.organization_name == "test-org"

    def test_organization_tag_list_options(self):
        """Test OrganizationTagsListOptions model."""
        options = OrganizationTagsListOptions(
            page_number=2,
            page_size=50,
            filter="prod",
            query="production",
        )
        assert options.page_number == 2
        assert options.page_size == 50
        assert options.filter == "prod"
        assert options.query == "production"

    def test_organization_tags_delete_options(self):
        """Test OrganizationTagsDeleteOptions model."""
        options = OrganizationTagsDeleteOptions(
            ids=["tag-123", "tag-456", "tag-789"]
        )
        assert len(options.ids) == 3
        assert "tag-123" in options.ids

    def test_add_workspaces_to_tag_options(self):
        """Test AddWorkspacesToTagOptions model."""
        options = AddWorkspacesToTagOptions(
            workspace_ids=["ws-abc", "ws-def", "ws-ghi"]
        )
        assert len(options.workspace_ids) == 3
        assert "ws-abc" in options.workspace_ids


class TestOrganizationTagsList:
    """Test organization tags list operations."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        config = TFEConfig(address="https://test.terraform.io", token="test-token")
        return TFEClient(config)

    @pytest.fixture
    def mock_list_response(self):
        """Create a mock list response."""
        mock = Mock()
        mock.json.return_value = {
            "data": [
                {
                    "id": "tag-prod123",
                    "type": "tags",
                    "attributes": {
                        "name": "production",
                        "instance-count": 5,
                        "created-at": "2023-01-01T00:00:00Z",
                        "organization-name": "test-org",
                    },
                },
                {
                    "id": "tag-dev456",
                    "type": "tags",
                    "attributes": {
                        "name": "development",
                        "instance-count": 3,
                        "created-at": "2023-01-02T00:00:00Z",
                        "organization-name": "test-org",
                    },
                },
            ],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "total-pages": 1,
                    "prev-page": None,
                    "next-page": None,
                    "total-count": 2,
                }
            },
        }
        return mock

    def test_list_organization_tags(self, client, mock_list_response):
        """Test listing organization tags."""
        client._transport.request = MagicMock(return_value=mock_list_response)

        tags = list(client.organization_tags.list("test-org"))

        assert len(tags) == 2
        assert tags[0].id == "tag-prod123"
        assert tags[0].name == "production"
        assert tags[0].instance_count == 5
        assert tags[1].id == "tag-dev456"
        assert tags[1].name == "development"

        client._transport.request.assert_called_once_with(
            "GET",
            "/api/v2/organizations/test-org/tags",
            params={"page[number]": 1, "page[size]": 100},
        )

    def test_list_organization_tags_with_options(self, client, mock_list_response):
        """Test listing organization tags with filter options."""
        client._transport.request = MagicMock(return_value=mock_list_response)

        options = OrganizationTagsListOptions(
            page_number=1,
            page_size=20,
            filter="prod",
            query="production",
        )
        tags = list(client.organization_tags.list("test-org", options=options))

        assert len(tags) == 2

        client._transport.request.assert_called_once_with(
            "GET",
            "/api/v2/organizations/test-org/tags",
            params={
                "page[number]": 1,
                "page[size]": 20,
                "filter[exclude][taggable][id]": "prod",
                "q": "production",
            },
        )

    def test_list_organization_tags_pagination(self, client):
        """Test listing organization tags with pagination."""
        page1_response = Mock()
        page1_response.json.return_value = {
            "data": [
                {
                    "id": "tag-1",
                    "type": "tags",
                    "attributes": {
                        "name": "tag1",
                        "instance-count": 1,
                        "created-at": "2023-01-01T00:00:00Z",
                        "organization-name": "test-org",
                    },
                }
            ],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "total-pages": 2,
                    "prev-page": None,
                    "next-page": 2,
                    "total-count": 2,
                }
            },
        }

        page2_response = Mock()
        page2_response.json.return_value = {
            "data": [
                {
                    "id": "tag-2",
                    "type": "tags",
                    "attributes": {
                        "name": "tag2",
                        "instance-count": 2,
                        "created-at": "2023-01-02T00:00:00Z",
                        "organization-name": "test-org",
                    },
                }
            ],
            "meta": {
                "pagination": {
                    "current-page": 2,
                    "total-pages": 2,
                    "prev-page": 1,
                    "next-page": None,
                    "total-count": 2,
                }
            },
        }

        client._transport.request = MagicMock(
            side_effect=[page1_response, page2_response]
        )

        tags = list(client.organization_tags.list("test-org"))

        # With pagination, the first page returns only 1 item (less than page_size of 100)
        # so iteration stops
        assert len(tags) == 1
        assert tags[0].id == "tag-1"
        # Only called once because first page had less than page_size items
        assert client._transport.request.call_count == 1

    def test_list_organization_tags_invalid_org(self, client):
        """Test listing tags with invalid organization."""
        with pytest.raises(InvalidOrgError):
            list(client.organization_tags.list(""))

        with pytest.raises(InvalidOrgError):
            list(client.organization_tags.list(None))


class TestOrganizationTagsDelete:
    """Test organization tags delete operations."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        config = TFEConfig(address="https://test.terraform.io", token="test-token")
        return TFEClient(config)

    @pytest.fixture
    def mock_delete_response(self):
        """Create a mock delete response."""
        mock = Mock()
        mock.status_code = 204
        return mock

    def test_delete_organization_tags(self, client, mock_delete_response):
        """Test deleting organization tags."""
        client._transport.request = MagicMock(return_value=mock_delete_response)

        options = OrganizationTagsDeleteOptions(ids=["tag-123", "tag-456"])
        client.organization_tags.delete("test-org", options)

        client._transport.request.assert_called_once()
        call_args = client._transport.request.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/api/v2/organizations/test-org/tags"
        assert call_args[1]["json_body"]["data"][0]["type"] == "tags"
        assert call_args[1]["json_body"]["data"][0]["id"] == "tag-123"
        assert call_args[1]["json_body"]["data"][1]["id"] == "tag-456"

    def test_delete_organization_tags_single(self, client, mock_delete_response):
        """Test deleting a single organization tag."""
        client._transport.request = MagicMock(return_value=mock_delete_response)

        options = OrganizationTagsDeleteOptions(ids=["tag-single"])
        client.organization_tags.delete("test-org", options)

        client._transport.request.assert_called_once()
        call_args = client._transport.request.call_args
        assert len(call_args[1]["json_body"]["data"]) == 1
        assert call_args[1]["json_body"]["data"][0]["id"] == "tag-single"

    def test_delete_organization_tags_invalid_org(self, client):
        """Test deleting tags with invalid organization."""
        options = OrganizationTagsDeleteOptions(ids=["tag-123"])

        with pytest.raises(InvalidOrgError):
            client.organization_tags.delete("", options)

        with pytest.raises(InvalidOrgError):
            client.organization_tags.delete(None, options)

    def test_delete_organization_tags_no_ids(self, client):
        """Test deleting tags without tag IDs."""
        options = OrganizationTagsDeleteOptions(ids=[])

        with pytest.raises(RequiredTagIDError):
            client.organization_tags.delete("test-org", options)

    def test_delete_organization_tags_invalid_id(self, client):
        """Test deleting tags with invalid tag ID."""
        options = OrganizationTagsDeleteOptions(ids=["tag-123", "", "tag-456"])

        with pytest.raises(InvalidTagIDError):
            client.organization_tags.delete("test-org", options)


class TestOrganizationTagsAddWorkspaces:
    """Test adding workspaces to organization tags."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        config = TFEConfig(address="https://test.terraform.io", token="test-token")
        return TFEClient(config)

    @pytest.fixture
    def mock_add_response(self):
        """Create a mock add workspaces response."""
        mock = Mock()
        mock.status_code = 204
        return mock

    def test_add_workspaces_to_tag(self, client, mock_add_response):
        """Test adding workspaces to a tag."""
        client._transport.request = MagicMock(return_value=mock_add_response)

        options = AddWorkspacesToTagOptions(workspace_ids=["ws-123", "ws-456"])
        client.organization_tags.add_workspaces("tag-prod", options)

        client._transport.request.assert_called_once()
        call_args = client._transport.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v2/tags/tag-prod/relationships/workspaces"
        assert call_args[1]["json_body"]["data"][0]["type"] == "workspaces"
        assert call_args[1]["json_body"]["data"][0]["id"] == "ws-123"
        assert call_args[1]["json_body"]["data"][1]["id"] == "ws-456"

    def test_add_workspaces_to_tag_single(self, client, mock_add_response):
        """Test adding a single workspace to a tag."""
        client._transport.request = MagicMock(return_value=mock_add_response)

        options = AddWorkspacesToTagOptions(workspace_ids=["ws-single"])
        client.organization_tags.add_workspaces("tag-dev", options)

        client._transport.request.assert_called_once()
        call_args = client._transport.request.call_args
        assert len(call_args[1]["json_body"]["data"]) == 1
        assert call_args[1]["json_body"]["data"][0]["id"] == "ws-single"

    def test_add_workspaces_invalid_tag_id(self, client):
        """Test adding workspaces with invalid tag ID."""
        options = AddWorkspacesToTagOptions(workspace_ids=["ws-123"])

        with pytest.raises(InvalidTagIDError):
            client.organization_tags.add_workspaces("", options)

        with pytest.raises(InvalidTagIDError):
            client.organization_tags.add_workspaces(None, options)

    def test_add_workspaces_no_workspace_ids(self, client):
        """Test adding workspaces without workspace IDs."""
        options = AddWorkspacesToTagOptions(workspace_ids=[])

        with pytest.raises(RequiredTagWorkspaceIDError):
            client.organization_tags.add_workspaces("tag-prod", options)

    def test_add_workspaces_invalid_workspace_id(self, client):
        """Test adding workspaces with invalid workspace ID."""
        options = AddWorkspacesToTagOptions(workspace_ids=["ws-123", "", "ws-456"])

        with pytest.raises(RequiredTagWorkspaceIDError):
            client.organization_tags.add_workspaces("tag-prod", options)
