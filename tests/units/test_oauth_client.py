# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Comprehensive unit tests for OAuth client operations in the Python TFE SDK.

This test suite covers all OAuth client methods including CRUD operations,
project management, and validation.
"""

from unittest.mock import Mock, patch

import pytest

from src.pytfe._http import HTTPTransport
from src.pytfe.errors import (
    ERR_INVALID_OAUTH_CLIENT_ID,
    ERR_INVALID_ORG,
)
from src.pytfe.models.oauth_client import (
    OAuthClientAddProjectsOptions,
    OAuthClientCreateOptions,
    OAuthClientIncludeOpt,
    OAuthClientListOptions,
    OAuthClientReadOptions,
    OAuthClientRemoveProjectsOptions,
    OAuthClientUpdateOptions,
    ServiceProviderType,
)
from src.pytfe.resources.oauth_client import OAuthClients


class TestOAuthClientParsing:
    """Test the OAuth client parsing functionality."""

    @pytest.fixture
    def oauth_clients_service(self):
        """Create an OAuthClients service for testing parsing."""
        mock_transport = Mock(spec=HTTPTransport)
        return OAuthClients(mock_transport)

    def test_parse_oauth_client_minimal(self, oauth_clients_service):
        """Test _parse_oauth_client with minimal data."""
        data = {
            "id": "oc-test123",
            "attributes": {
                "name": "Test OAuth Client",
                "service-provider": "github",
            },
        }

        result = oauth_clients_service._parse_oauth_client(data)

        assert result.id == "oc-test123"
        assert result.name == "Test OAuth Client"
        assert result.service_provider == ServiceProviderType.GITHUB
        assert result.api_url is None
        assert result.callback_url is None
        assert result.connect_path is None
        assert result.created_at is None
        assert result.oauth_tokens is None
        assert result.projects is None

    def test_parse_oauth_client_comprehensive(self, oauth_clients_service):
        """Test _parse_oauth_client with comprehensive data."""
        data = {
            "id": "oc-test123",
            "attributes": {
                "name": "Test GitHub Client",
                "api-url": "https://api.github.com",
                "callback-url": "https://app.terraform.io/auth/callback",
                "connect-path": "/auth/connect",
                "created-at": "2023-10-02T10:30:00.000Z",
                "http-url": "https://github.com",
                "key": "test-key",
                "rsa-public-key": "ssh-rsa AAAAB3...",
                "secret": "test-secret",
                "service-provider": "github",
                "service-provider-display-name": "GitHub",
                "organization-scoped": True,
            },
            "relationships": {
                "oauth-tokens": {
                    "data": [
                        {"id": "ot-token1", "type": "oauth-tokens"},
                        {"id": "ot-token2", "type": "oauth-tokens"},
                    ]
                },
                "projects": {
                    "data": [
                        {"id": "prj-proj1", "type": "projects"},
                        {"id": "prj-proj2", "type": "projects"},
                    ]
                },
            },
        }

        result = oauth_clients_service._parse_oauth_client(data)

        assert result.id == "oc-test123"
        assert result.name == "Test GitHub Client"
        assert result.api_url == "https://api.github.com"
        assert result.callback_url == "https://app.terraform.io/auth/callback"
        assert result.connect_path == "/auth/connect"
        # Note: datetime parsing may need adjustment based on actual implementation
        assert result.http_url == "https://github.com"
        assert result.key == "test-key"
        assert result.rsa_public_key == "ssh-rsa AAAAB3..."
        assert result.secret == "test-secret"
        assert result.service_provider == ServiceProviderType.GITHUB
        assert result.service_provider_name == "GitHub"
        assert result.organization_scoped is True
        assert len(result.oauth_tokens) == 2
        assert result.oauth_tokens[0]["id"] == "ot-token1"
        assert result.oauth_tokens[1]["id"] == "ot-token2"
        assert len(result.projects) == 2
        assert result.projects[0]["id"] == "prj-proj1"
        assert result.projects[1]["id"] == "prj-proj2"

    def test_parse_oauth_client_empty_relationships(self, oauth_clients_service):
        """Test _parse_oauth_client with empty relationships."""
        data = {
            "id": "oc-test123",
            "attributes": {
                "name": "Test Client",
                "service-provider": "gitlab_hosted",
            },
            "relationships": {
                "oauth-tokens": {"data": []},
                "projects": {"data": []},
            },
        }

        result = oauth_clients_service._parse_oauth_client(data)

        assert result.id == "oc-test123"
        assert result.name == "Test Client"
        assert result.service_provider == ServiceProviderType.GITLAB_HOSTED
        assert result.oauth_tokens == []
        assert result.projects == []

    def test_parse_oauth_client_no_relationships(self, oauth_clients_service):
        """Test _parse_oauth_client with no relationships section."""
        data = {
            "id": "oc-test123",
            "attributes": {
                "name": "Test Client",
                "service-provider": "bitbucket_hosted",
                "organization-scoped": False,
            },
        }

        result = oauth_clients_service._parse_oauth_client(data)

        assert result.id == "oc-test123"
        assert result.name == "Test Client"
        assert result.service_provider == ServiceProviderType.BITBUCKET_HOSTED
        assert result.organization_scoped is False
        assert result.oauth_tokens is None
        assert result.projects is None


class TestOAuthClients:
    """Test the OAuthClients service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def oauth_clients_service(self, mock_transport):
        """Create an OAuthClients service with mocked transport."""
        return OAuthClients(mock_transport)

    def test_list_oauth_clients_basic(self, oauth_clients_service, mock_transport):
        """Test listing OAuth clients without options."""
        # Mock response data
        mock_response_data = {
            "data": [
                {
                    "id": "oc-test1",
                    "attributes": {
                        "name": "GitHub Client 1",
                        "service-provider": "github",
                    },
                },
                {
                    "id": "oc-test2",
                    "attributes": {
                        "name": "GitLab Client 1",
                        "service-provider": "gitlab_hosted",
                    },
                },
            ]
        }

        with patch.object(oauth_clients_service, "_list") as mock_list:
            mock_list.return_value = mock_response_data["data"]

            result = list(oauth_clients_service.list("test-org"))

            assert len(result) == 2
            assert result[0].id == "oc-test1"
            assert result[0].name == "GitHub Client 1"
            assert result[0].service_provider == ServiceProviderType.GITHUB
            assert result[1].id == "oc-test2"
            assert result[1].name == "GitLab Client 1"
            assert result[1].service_provider == ServiceProviderType.GITLAB_HOSTED

            mock_list.assert_called_once_with(
                "/api/v2/organizations/test-org/oauth-clients", params={}
            )

    def test_list_oauth_clients_with_options(
        self, oauth_clients_service, mock_transport
    ):
        """Test listing OAuth clients with options."""
        options = OAuthClientListOptions(
            page_number=2,
            page_size=50,
            include=[
                OAuthClientIncludeOpt.OAUTH_TOKENS,
                OAuthClientIncludeOpt.PROJECTS,
            ],
        )

        with patch.object(oauth_clients_service, "_list") as mock_list:
            mock_list.return_value = []

            list(oauth_clients_service.list("test-org", options))

            expected_params = {
                "page[number]": "2",
                "page[size]": "50",
                "include": "oauth_tokens,projects",
            }
            mock_list.assert_called_once_with(
                "/api/v2/organizations/test-org/oauth-clients", params=expected_params
            )

    def test_list_oauth_clients_invalid_org(self, oauth_clients_service):
        """Test listing OAuth clients with invalid organization."""
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            list(oauth_clients_service.list(""))

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            list(oauth_clients_service.list(None))

    def test_create_oauth_client_success(self, oauth_clients_service, mock_transport):
        """Test creating an OAuth client successfully."""
        create_options = OAuthClientCreateOptions(
            name="Test GitHub Client",
            api_url="https://api.github.com",
            http_url="https://github.com",
            oauth_token="ghp_test_token",
            service_provider=ServiceProviderType.GITHUB,
            organization_scoped=True,
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "oc-created",
                "attributes": {
                    "name": "Test GitHub Client",
                    "api-url": "https://api.github.com",
                    "http-url": "https://github.com",
                    "service-provider": "github",
                    "organization-scoped": True,
                },
            }
        }
        mock_transport.request.return_value = mock_response

        result = oauth_clients_service.create("test-org", create_options)

        assert result.id == "oc-created"
        assert result.name == "Test GitHub Client"
        assert result.api_url == "https://api.github.com"
        assert result.http_url == "https://github.com"
        assert result.service_provider == ServiceProviderType.GITHUB
        assert result.organization_scoped is True

        # Verify the request was made correctly
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api/v2/organizations/test-org/oauth-clients"

    def test_create_oauth_client_with_projects(
        self, oauth_clients_service, mock_transport
    ):
        """Test creating an OAuth client with projects."""
        create_options = OAuthClientCreateOptions(
            name="Test Client with Projects",
            api_url="https://api.github.com",
            http_url="https://github.com",
            oauth_token="ghp_test_token",
            service_provider=ServiceProviderType.GITHUB,
            projects=[{"type": "projects", "id": "prj-test1"}],
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "oc-with-projects",
                "attributes": {
                    "name": "Test Client with Projects",
                    "service-provider": "github",
                },
            }
        }
        mock_transport.request.return_value = mock_response

        result = oauth_clients_service.create("test-org", create_options)

        assert result.id == "oc-with-projects"
        assert result.name == "Test Client with Projects"

        # Verify the request included projects in relationships
        call_args = mock_transport.request.call_args
        json_body = call_args[1]["json_body"]
        assert "relationships" in json_body["data"]
        assert "projects" in json_body["data"]["relationships"]
        assert json_body["data"]["relationships"]["projects"]["data"] == [
            {"type": "projects", "id": "prj-test1"}
        ]

    def test_create_oauth_client_invalid_org(self, oauth_clients_service):
        """Test creating OAuth client with invalid organization."""
        create_options = OAuthClientCreateOptions(
            name="Test",
            api_url="https://api.github.com",
            http_url="https://github.com",
            oauth_token="token",
            service_provider=ServiceProviderType.GITHUB,
        )

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            oauth_clients_service.create("", create_options)

    def test_read_oauth_client_success(self, oauth_clients_service, mock_transport):
        """Test reading an OAuth client successfully."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "oc-test123",
                "attributes": {
                    "name": "Test OAuth Client",
                    "service-provider": "github",
                    "created-at": "2023-10-02T10:30:00.000Z",
                },
            }
        }
        mock_transport.request.return_value = mock_response

        result = oauth_clients_service.read("oc-test123")

        assert result.id == "oc-test123"
        assert result.name == "Test OAuth Client"
        assert result.service_provider == ServiceProviderType.GITHUB
        assert result.created_at is not None
        assert result.created_at.year == 2023
        assert result.created_at.month == 10
        assert result.created_at.day == 2

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/oauth-clients/oc-test123", params={}
        )

    def test_read_oauth_client_with_options(
        self, oauth_clients_service, mock_transport
    ):
        """Test reading an OAuth client with options."""
        read_options = OAuthClientReadOptions(
            include=[OAuthClientIncludeOpt.OAUTH_TOKENS, OAuthClientIncludeOpt.PROJECTS]
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "oc-test123",
                "attributes": {
                    "name": "Test OAuth Client",
                    "service-provider": "github",
                },
                "relationships": {
                    "oauth-tokens": {
                        "data": [{"id": "ot-token1", "type": "oauth-tokens"}]
                    },
                    "projects": {"data": [{"id": "prj-proj1", "type": "projects"}]},
                },
            }
        }
        mock_transport.request.return_value = mock_response

        result = oauth_clients_service.read_with_options("oc-test123", read_options)

        assert result.id == "oc-test123"
        assert result.name == "Test OAuth Client"
        assert len(result.oauth_tokens) == 1
        assert result.oauth_tokens[0]["id"] == "ot-token1"
        assert len(result.projects) == 1
        assert result.projects[0]["id"] == "prj-proj1"

        expected_params = {"include": "oauth_tokens,projects"}
        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/oauth-clients/oc-test123", params=expected_params
        )

    def test_read_oauth_client_invalid_id(self, oauth_clients_service):
        """Test reading OAuth client with invalid ID."""
        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_CLIENT_ID):
            oauth_clients_service.read("")

        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_CLIENT_ID):
            oauth_clients_service.read_with_options("", None)

    def test_update_oauth_client_success(self, oauth_clients_service, mock_transport):
        """Test updating an OAuth client successfully."""
        update_options = OAuthClientUpdateOptions(
            name="Updated OAuth Client",
            organization_scoped=False,
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "oc-test123",
                "attributes": {
                    "name": "Updated OAuth Client",
                    "service-provider": "github",
                    "organization-scoped": False,
                },
            }
        }
        mock_transport.request.return_value = mock_response

        result = oauth_clients_service.update("oc-test123", update_options)

        assert result.id == "oc-test123"
        assert result.name == "Updated OAuth Client"
        assert result.organization_scoped is False

        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == "/api/v2/oauth-clients/oc-test123"

    def test_update_oauth_client_invalid_id(self, oauth_clients_service):
        """Test updating OAuth client with invalid ID."""
        update_options = OAuthClientUpdateOptions(name="Test")

        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_CLIENT_ID):
            oauth_clients_service.update("", update_options)

    def test_delete_oauth_client_success(self, oauth_clients_service, mock_transport):
        """Test deleting an OAuth client successfully."""
        oauth_clients_service.delete("oc-test123")

        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/oauth-clients/oc-test123"
        )

    def test_delete_oauth_client_invalid_id(self, oauth_clients_service):
        """Test deleting OAuth client with invalid ID."""
        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_CLIENT_ID):
            oauth_clients_service.delete("")

    def test_add_projects_success(self, oauth_clients_service, mock_transport):
        """Test adding projects to an OAuth client successfully."""
        add_options = OAuthClientAddProjectsOptions(
            projects=[
                {"type": "projects", "id": "prj-test1"},
                {"type": "projects", "id": "prj-test2"},
            ]
        )

        oauth_clients_service.add_projects("oc-test123", add_options)

        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            call_args[0][1] == "/api/v2/oauth-clients/oc-test123/relationships/projects"
        )

        json_body = call_args[1]["json_body"]
        assert json_body["data"] == [
            {"type": "projects", "id": "prj-test1"},
            {"type": "projects", "id": "prj-test2"},
        ]

    def test_add_projects_invalid_id(self, oauth_clients_service):
        """Test adding projects with invalid OAuth client ID."""
        add_options = OAuthClientAddProjectsOptions(
            projects=[{"type": "projects", "id": "prj-test1"}]
        )

        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_CLIENT_ID):
            oauth_clients_service.add_projects("", add_options)

    def test_remove_projects_success(self, oauth_clients_service, mock_transport):
        """Test removing projects from an OAuth client successfully."""
        remove_options = OAuthClientRemoveProjectsOptions(
            projects=[
                {"type": "projects", "id": "prj-test1"},
                {"type": "projects", "id": "prj-test2"},
            ]
        )

        oauth_clients_service.remove_projects("oc-test123", remove_options)

        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "DELETE"
        assert (
            call_args[0][1] == "/api/v2/oauth-clients/oc-test123/relationships/projects"
        )

        json_body = call_args[1]["json_body"]
        assert json_body["data"] == [
            {"type": "projects", "id": "prj-test1"},
            {"type": "projects", "id": "prj-test2"},
        ]

    def test_remove_projects_invalid_id(self, oauth_clients_service):
        """Test removing projects with invalid OAuth client ID."""
        remove_options = OAuthClientRemoveProjectsOptions(
            projects=[{"type": "projects", "id": "prj-test1"}]
        )

        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_CLIENT_ID):
            oauth_clients_service.remove_projects("", remove_options)


class TestOAuthClientValidation:
    """Test OAuth client validation functions."""

    def test_oauth_client_create_options_validation(self):
        """Test validation of OAuthClientCreateOptions."""
        # Valid options
        valid_options = OAuthClientCreateOptions(
            name="Test Client",
            api_url="https://api.github.com",
            http_url="https://github.com",
            oauth_token="ghp_test_token",
            service_provider=ServiceProviderType.GITHUB,
        )
        assert valid_options.name == "Test Client"
        assert valid_options.api_url == "https://api.github.com"
        assert valid_options.service_provider == ServiceProviderType.GITHUB

        # Test various service provider types
        for provider in ServiceProviderType:
            options = OAuthClientCreateOptions(
                name="Test",
                api_url="https://api.example.com",
                http_url="https://example.com",
                oauth_token="token",
                service_provider=provider,
            )
            assert options.service_provider == provider

    def test_oauth_client_update_options(self):
        """Test OAuthClientUpdateOptions."""
        update_options = OAuthClientUpdateOptions(
            name="Updated Name",
            organization_scoped=True,
        )
        assert update_options.name == "Updated Name"
        assert update_options.organization_scoped is True

        # Test with minimal options
        minimal_options = OAuthClientUpdateOptions()
        assert minimal_options.name is None
        assert minimal_options.organization_scoped is None

    def test_oauth_client_project_options(self):
        """Test project-related options."""
        projects = [
            {"type": "projects", "id": "prj-test1"},
            {"type": "projects", "id": "prj-test2"},
        ]

        add_options = OAuthClientAddProjectsOptions(projects=projects)
        assert len(add_options.projects) == 2
        assert add_options.projects[0]["id"] == "prj-test1"

        remove_options = OAuthClientRemoveProjectsOptions(projects=projects)
        assert len(remove_options.projects) == 2
        assert remove_options.projects[1]["id"] == "prj-test2"

    def test_oauth_client_include_options(self):
        """Test include options."""
        list_options = OAuthClientListOptions(
            include=[OAuthClientIncludeOpt.OAUTH_TOKENS]
        )
        assert OAuthClientIncludeOpt.OAUTH_TOKENS in list_options.include

        read_options = OAuthClientReadOptions(
            include=[OAuthClientIncludeOpt.PROJECTS, OAuthClientIncludeOpt.OAUTH_TOKENS]
        )
        assert len(read_options.include) == 2
        assert OAuthClientIncludeOpt.PROJECTS in read_options.include
        assert OAuthClientIncludeOpt.OAUTH_TOKENS in read_options.include
