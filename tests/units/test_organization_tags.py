"""Unit tests for the organization tags module."""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from pytfe._http import HTTPTransport
from pytfe.errors import (
    ERR_INVALID_ORG,
)
from pytfe.models.organization_tags import (
    AddWorkspacesToTagOptions,
    OrganizationTagsDeleteOptions,
    OrganizationTagsList,
    OrganizationTagsListOptions,
)
from pytfe.resources.organization_tags import OrganizationTags

ERR_INVALID_TAG = "invalid value for tag"
ERR_REQUIRED_TAG_ID = "tag ID is required"
ERR_REQUIRED_TAG_WORKSPACE_ID = "workspace ID is required"


class TestOrganizationTags:
    """Test the OrganizationTags service class."""

    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def organization_tags_service(self, mock_transport):
        return OrganizationTags(mock_transport)

    def test_list_success(self, organization_tags_service):
        mock_response_data = {
            "data": [
                {
                    "id": "tag-1",
                    "attributes": {
                        "name": "env:dev",
                        "instance-count": 2,
                    },
                    "relationships": {
                        "organization": {"data": {"id": "org-1", "type": "organizations"}}
                    },
                }
            ],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "total-count": 1,
                    "next-page": None,
                    "previous-page": None,
                    "total-pages": 1,
                }
            },
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(organization_tags_service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            options = OrganizationTagsListOptions(query="env")
            result = organization_tags_service.list("test-org", options)

            assert isinstance(result, OrganizationTagsList)
            assert len(result.items) == 1
            assert result.items[0].id == "tag-1"
            assert result.items[0].name == "env:dev"
            assert result.items[0].instance_count == 2
            assert result.items[0].organization is not None
            assert result.items[0].organization.id == "org-1"
            assert result.pagination is not None
            assert result.pagination.current_page == 1
            assert result.pagination.total_count == 1

            call_args = mock_t.request.call_args
            assert call_args[0][0] == "GET"
            assert call_args[0][1] == "/api/v2/organizations/test-org/tags"
            assert call_args[1]["params"]["q"] == "env"

    def test_list_validation_errors(self, organization_tags_service):
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            organization_tags_service.list("")

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            organization_tags_service.list(None)

    def test_delete_success(self, organization_tags_service):
        with patch.object(organization_tags_service, "t") as mock_t:
            mock_t.request.return_value = Mock()

            options = OrganizationTagsDeleteOptions(ids=["tag-1", "tag-2"])
            organization_tags_service.delete("test-org", options)

            call_args = mock_t.request.call_args
            assert call_args[0][0] == "DELETE"
            assert call_args[0][1] == "/api/v2/organizations/test-org/tags"
            assert call_args[1]["json_body"] == {
                "data": [
                    {"type": "tags", "id": "tag-1"},
                    {"type": "tags", "id": "tag-2"},
                ]
            }

    def test_delete_validation_errors(self, organization_tags_service):
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            organization_tags_service.delete(
                "", OrganizationTagsDeleteOptions(ids=["tag-1"])
            )

        with pytest.raises(ValueError, match=ERR_REQUIRED_TAG_ID):
            organization_tags_service.delete("test-org", OrganizationTagsDeleteOptions())

        with pytest.raises(ValueError, match="is not a valid id value"):
            organization_tags_service.delete(
                "test-org", OrganizationTagsDeleteOptions(ids=[""])
            )

    def test_add_workspaces_success(self, organization_tags_service):
        with patch.object(organization_tags_service, "t") as mock_t:
            mock_t.request.return_value = Mock()

            options = AddWorkspacesToTagOptions(workspace_ids=["ws-1", "ws-2"])
            organization_tags_service.add_workspaces("tag-1", options)

            call_args = mock_t.request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/api/v2/tags/tag-1/relationships/workspaces"
            assert call_args[1]["json_body"] == {
                "data": [
                    {"type": "workspaces", "id": "ws-1"},
                    {"type": "workspaces", "id": "ws-2"},
                ]
            }

    def test_add_workspaces_validation_errors(self, organization_tags_service):
        with pytest.raises(ValueError, match=ERR_INVALID_TAG):
            organization_tags_service.add_workspaces(
                "", AddWorkspacesToTagOptions(workspace_ids=["ws-1"])
            )

        with pytest.raises(ValueError, match=ERR_REQUIRED_TAG_WORKSPACE_ID):
            organization_tags_service.add_workspaces(
                "tag-1", AddWorkspacesToTagOptions()
            )

        with pytest.raises(ValueError, match="is not a valid id value"):
            organization_tags_service.add_workspaces(
                "tag-1", AddWorkspacesToTagOptions(workspace_ids=[""])
            )
