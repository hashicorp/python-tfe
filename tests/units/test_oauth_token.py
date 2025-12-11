"""
Comprehensive unit tests for OAuth token operations in the Python TFE SDK.

This test suite covers all OAuth token methods including list, read, update, and delete operations.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.pytfe._http import HTTPTransport
from src.pytfe.errors import (
    ERR_INVALID_OAUTH_TOKEN_ID,
    ERR_INVALID_ORG,
)
from src.pytfe.models.oauth_token import (
    OAuthTokenListOptions,
    OAuthTokenUpdateOptions,
)
from src.pytfe.resources.oauth_token import OAuthTokens


class TestOAuthTokenParsing:
    """Test the OAuth token parsing functionality."""

    @pytest.fixture
    def oauth_tokens_service(self):
        """Create an OAuthTokens service for testing parsing."""
        mock_transport = Mock(spec=HTTPTransport)
        return OAuthTokens(mock_transport)

    def test_parse_oauth_token_minimal(self, oauth_tokens_service):
        """Test _parse_oauth_token with minimal data."""
        data = {
            "id": "ot-test123",
            "attributes": {
                "created-at": "2023-01-01T00:00:00Z",
                "has-ssh-key": False,
                "service-provider-user": "testuser",
            },
            "relationships": {},
        }

        result = oauth_tokens_service._parse_oauth_token(data)

        assert result.id == "ot-test123"
        assert isinstance(result.created_at, datetime)
        assert result.has_ssh_key is False
        assert result.service_provider_user == "testuser"
        assert result.oauth_client is None

    def test_parse_oauth_token_with_oauth_client(self, oauth_tokens_service):
        """Test _parse_oauth_token with OAuth client relationship."""
        data = {
            "id": "ot-test123",
            "attributes": {
                "created-at": "2023-01-01T00:00:00Z",
                "has-ssh-key": True,
                "service-provider-user": "testuser",
            },
            "relationships": {
                "oauth-client": {
                    "data": {
                        "id": "oc-client123",
                        "type": "oauth-clients",
                    }
                }
            },
        }

        result = oauth_tokens_service._parse_oauth_token(data)

        assert result.id == "ot-test123"
        assert result.has_ssh_key is True
        # For now, oauth_client relationship parsing is not implemented
        assert result.oauth_client is None

    def test_parse_oauth_token_empty_relationships(self, oauth_tokens_service):
        """Test _parse_oauth_token with empty relationships."""
        data = {
            "id": "ot-test123",
            "attributes": {
                "created-at": "2023-01-01T00:00:00Z",
                "has-ssh-key": False,
                "service-provider-user": "testuser",
            },
            "relationships": {"oauth-client": {"data": None}},
        }

        result = oauth_tokens_service._parse_oauth_token(data)

        assert result.id == "ot-test123"
        assert result.oauth_client is None


class TestOAuthTokens:
    """Test the OAuthTokens service methods."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport for testing."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def oauth_tokens_service(self, mock_transport):
        """Create an OAuthTokens service with mocked transport."""
        return OAuthTokens(mock_transport)

    def test_list_oauth_tokens_basic(self, oauth_tokens_service, mock_transport):
        """Test listing OAuth tokens without options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "ot-test1",
                    "attributes": {
                        "created-at": "2023-01-01T00:00:00Z",
                        "has-ssh-key": False,
                        "service-provider-user": "testuser1",
                    },
                    "relationships": {},
                },
                {
                    "id": "ot-test2",
                    "attributes": {
                        "created-at": "2023-01-02T00:00:00Z",
                        "has-ssh-key": True,
                        "service-provider-user": "testuser2",
                    },
                    "relationships": {},
                },
            ],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "prev-page": None,
                    "next-page": None,
                    "total-pages": 1,
                    "total-count": 2,
                }
            },
        }
        mock_transport.request.return_value = mock_response

        result = list(oauth_tokens_service.list("test-org"))

        assert mock_transport.request.call_count == 1
        assert len(result) == 2
        assert result[0].id == "ot-test1"
        assert result[1].id == "ot-test2"

    def test_list_oauth_tokens_with_options(self, oauth_tokens_service, mock_transport):
        """Test listing OAuth tokens with pagination options."""
        options = OAuthTokenListOptions(page_size=50)

        with patch.object(oauth_tokens_service, "_list") as mock_list:
            mock_list.return_value = []

            list(oauth_tokens_service.list("test-org", options))

            expected_params = {
                "page[size]": "50",
            }
            mock_list.assert_called_once_with(
                "/api/v2/organizations/test-org/oauth-tokens", params=expected_params
            )

    def test_list_oauth_tokens_invalid_org(self, oauth_tokens_service):
        """Test listing OAuth tokens with invalid organization ID."""
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            list(oauth_tokens_service.list(""))

    def test_read_oauth_token_success(self, oauth_tokens_service, mock_transport):
        """Test reading an OAuth token successfully."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "ot-test123",
                "attributes": {
                    "created-at": "2023-01-01T00:00:00Z",
                    "has-ssh-key": False,
                    "service-provider-user": "testuser",
                },
                "relationships": {},
            }
        }
        mock_transport.request.return_value = mock_response

        result = oauth_tokens_service.read("ot-test123")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/oauth-tokens/ot-test123"
        )
        assert result.id == "ot-test123"

    def test_read_oauth_token_invalid_id(self, oauth_tokens_service):
        """Test reading an OAuth token with invalid ID."""
        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_TOKEN_ID):
            oauth_tokens_service.read("")

    def test_update_oauth_token_success(self, oauth_tokens_service, mock_transport):
        """Test updating an OAuth token successfully."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "ot-test123",
                "attributes": {
                    "created-at": "2023-01-01T00:00:00Z",
                    "has-ssh-key": True,
                    "service-provider-user": "testuser",
                },
                "relationships": {},
            }
        }
        mock_transport.request.return_value = mock_response

        options = OAuthTokenUpdateOptions(private_ssh_key="test-ssh-key")
        result = oauth_tokens_service.update("ot-test123", options)

        expected_body = {
            "data": {
                "type": "oauth-tokens",
                "attributes": {
                    "ssh-key": "test-ssh-key",
                },
            }
        }
        mock_transport.request.assert_called_once_with(
            "PATCH", "/api/v2/oauth-tokens/ot-test123", json_body=expected_body
        )
        assert result.id == "ot-test123"
        assert result.has_ssh_key is True

    def test_update_oauth_token_no_ssh_key(self, oauth_tokens_service, mock_transport):
        """Test updating an OAuth token without SSH key."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "ot-test123",
                "attributes": {
                    "created-at": "2023-01-01T00:00:00Z",
                    "has-ssh-key": False,
                    "service-provider-user": "testuser",
                },
                "relationships": {},
            }
        }
        mock_transport.request.return_value = mock_response

        options = OAuthTokenUpdateOptions()
        result = oauth_tokens_service.update("ot-test123", options)

        expected_body = {
            "data": {
                "type": "oauth-tokens",
                "attributes": {},
            }
        }
        mock_transport.request.assert_called_once_with(
            "PATCH", "/api/v2/oauth-tokens/ot-test123", json_body=expected_body
        )
        assert result.id == "ot-test123"

    def test_update_oauth_token_invalid_id(self, oauth_tokens_service):
        """Test updating an OAuth token with invalid ID."""
        options = OAuthTokenUpdateOptions()
        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_TOKEN_ID):
            oauth_tokens_service.update("", options)

    def test_delete_oauth_token_success(self, oauth_tokens_service, mock_transport):
        """Test deleting an OAuth token successfully."""
        oauth_tokens_service.delete("ot-test123")

        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/oauth-tokens/ot-test123"
        )

    def test_delete_oauth_token_invalid_id(self, oauth_tokens_service):
        """Test deleting an OAuth token with invalid ID."""
        with pytest.raises(ValueError, match=ERR_INVALID_OAUTH_TOKEN_ID):
            oauth_tokens_service.delete("")


class TestOAuthTokenValidation:
    """Test OAuth token validation functionality."""

    @pytest.fixture
    def oauth_tokens_service(self):
        """Create an OAuthTokens service for testing validation."""
        mock_transport = Mock(spec=HTTPTransport)
        return OAuthTokens(mock_transport)

    def test_oauth_token_list_options(self, oauth_tokens_service):
        """Test OAuth token list options creation."""
        options = OAuthTokenListOptions(page_size=25)

        assert options.page_size == 25

    def test_oauth_token_update_options(self, oauth_tokens_service):
        """Test OAuth token update options creation."""
        options = OAuthTokenUpdateOptions(private_ssh_key="test-key")

        assert options.private_ssh_key == "test-key"

        # Test with no SSH key
        options_empty = OAuthTokenUpdateOptions()
        assert options_empty.private_ssh_key is None
