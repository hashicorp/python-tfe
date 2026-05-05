"""Unit tests for the organization token module."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import ERR_INVALID_ORG
from pytfe.models.organization_token import (
    OrganizationToken,
    OrganizationTokenCreateOptions,
    OrganizationTokenDeleteOptions,
    OrganizationTokenReadOptions,
    TokenType,
)
from pytfe.resources.organization_token import OrganizationTokens


class TestOrganizationTokens:
    """Test the OrganizationTokens service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def org_tokens_service(self, mock_transport):
        """Create an OrganizationTokens service with mocked transport."""
        return OrganizationTokens(mock_transport)

    def test_create_success(self, org_tokens_service):
        """Test successful create operation."""
        mock_response_data = {
            "data": {
                "id": "at-test123",
                "attributes": {
                    "created-at": "2023-01-01T00:00:00Z",
                    "description": "Test token",
                    "token": "test-token-value",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            result = org_tokens_service.create("test-org")

            mock_t.request.assert_called_once()
            call_args = mock_t.request.call_args

            assert call_args[0][0] == "POST"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/authentication-token"
            )
            assert "json_body" in call_args[1]
            assert "data" in call_args[1]["json_body"]
            assert "attributes" in call_args[1]["json_body"]["data"]
            assert isinstance(result, OrganizationToken)
            assert result.id == "at-test123"
            assert result.description == "Test token"

    def test_create_validation_errors(self, org_tokens_service):
        """Test create with invalid organization name."""
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            org_tokens_service.create("")

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            org_tokens_service.create(None)

    def test_create_with_options_expiration_success(self, org_tokens_service):
        """Test create with options including expiration date."""
        mock_response_data = {
            "data": {
                "id": "at-exp-123",
                "attributes": {
                    "created-at": "2023-01-01T00:00:00Z",
                    "token": "token-value",
                    "expired-at": "2024-01-01T00:00:00Z",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            expiry = datetime(2024, 1, 1, 0, 0, 0)
            options = OrganizationTokenCreateOptions(expired_at=expiry)

            result = org_tokens_service.create_with_options("test-org", options)

            assert isinstance(result, OrganizationToken)
            assert result.expired_at is not None

            call_args = mock_t.request.call_args
            assert call_args[0][0] == "POST"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/authentication-token"
            )
            body = call_args[1]["json_body"]
            assert "expired-at" in body["data"]["attributes"]
            assert body["data"]["attributes"]["expired-at"] == "2024-01-01T00:00:00"

    def test_create_with_options_token_type_success(self, org_tokens_service):
        """Test create with options including token type."""
        mock_response_data = {
            "data": {
                "id": "at-audit-123",
                "attributes": {
                    "created-at": "2023-01-01T00:00:00Z",
                    "token": "audit-token-value",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            options = OrganizationTokenCreateOptions(token_type=TokenType.AUDIT_TRAILS)
            result = org_tokens_service.create_with_options("test-org", options)

            assert isinstance(result, OrganizationToken)
            call_args = mock_t.request.call_args
            assert call_args[0][0] == "POST"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/authentication-token"
            )
            assert "params" in call_args[1]
            assert call_args[1]["params"]["token"] == "audit-trails"
            assert "json_body" in call_args[1]

    def test_read_success(self, org_tokens_service):
        """Test successful read operation."""
        mock_response_data = {
            "data": {
                "id": "at-read-123",
                "attributes": {
                    "created-at": "2023-01-01T00:00:00Z",
                    "description": "Read token",
                    "token": "read-token-value",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            result = org_tokens_service.read("test-org")

            assert isinstance(result, OrganizationToken)
            assert result.id == "at-read-123"

            call_args = mock_t.request.call_args
            assert call_args[0][0] == "GET"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/authentication-token"
            )

    def test_read_validation_errors(self, org_tokens_service):
        """Test read with invalid organization name."""
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            org_tokens_service.read("")

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            org_tokens_service.read(None)

    def test_read_with_options_token_type_success(self, org_tokens_service):
        """Test read with options including token type."""
        mock_response_data = {
            "data": {
                "id": "at-audit-read-123",
                "attributes": {
                    "created-at": "2023-01-01T00:00:00Z",
                    "token": "audit-read-value",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            options = OrganizationTokenReadOptions(token_type=TokenType.AUDIT_TRAILS)
            result = org_tokens_service.read_with_options("test-org", options)

            assert isinstance(result, OrganizationToken)
            call_args = mock_t.request.call_args
            assert call_args[0][0] == "GET"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/authentication-token"
            )
            assert call_args[1]["params"]["token"] == "audit-trails"

    def test_delete_success(self, org_tokens_service):
        """Test successful delete operation."""
        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = Mock()

            result = org_tokens_service.delete("test-org")

            assert result is None
            call_args = mock_t.request.call_args
            assert call_args[0][0] == "DELETE"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/authentication-token"
            )

    def test_delete_validation_errors(self, org_tokens_service):
        """Test delete with invalid organization name."""
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            org_tokens_service.delete("")

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            org_tokens_service.delete(None)

    def test_delete_with_options_token_type_success(self, org_tokens_service):
        """Test delete with options including token type."""
        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = Mock()

            options = OrganizationTokenDeleteOptions(token_type=TokenType.AUDIT_TRAILS)
            result = org_tokens_service.delete_with_options("test-org", options)

            assert result is None
            call_args = mock_t.request.call_args
            assert call_args[0][0] == "DELETE"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/authentication-token"
            )
            assert call_args[1]["params"]["token"] == "audit-trails"

    def test_parse_token_minimal(self, org_tokens_service):
        """Test parsing token with minimal data."""
        data = {
            "id": "at-minimal-123",
            "attributes": {
                "created-at": "2023-01-01T00:00:00Z",
                "description": "Minimal token",
                "token": "minimal-value",
            },
            "relationships": {},
        }

        result = org_tokens_service._parse_organization_token(data)

        assert result.id == "at-minimal-123"
        assert isinstance(result.created_at, datetime)
        assert result.description == "Minimal token"
        assert result.token == "minimal-value"
        assert result.last_used_at is None
        assert result.expired_at is None

    def test_parse_token_all_fields(self, org_tokens_service):
        """Test parsing token with all fields populated."""
        data = {
            "id": "at-full-123",
            "attributes": {
                "created-at": "2023-01-01T00:00:00Z",
                "description": "Full token",
                "token": "full-value",
                "last-used-at": "2023-01-15T12:30:00Z",
                "expired-at": "2024-01-01T00:00:00Z",
            },
            "relationships": {},
        }

        result = org_tokens_service._parse_organization_token(data)

        assert result.id == "at-full-123"
        assert result.description == "Full token"
        assert result.token == "full-value"
        assert result.last_used_at is not None
        assert result.expired_at is not None
        assert isinstance(result.last_used_at, datetime)
        assert isinstance(result.expired_at, datetime)

    def test_invalid_response_format_on_create(self, org_tokens_service):
        """Test handling of invalid response format when creating."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid"}

        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            with pytest.raises(ValueError, match="Invalid response format"):
                org_tokens_service.create("test-org")

    def test_invalid_response_format_on_read(self, org_tokens_service):
        """Test handling of invalid response format when reading."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid"}

        with patch.object(org_tokens_service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            with pytest.raises(ValueError, match="Invalid response format"):
                org_tokens_service.read("test-org")