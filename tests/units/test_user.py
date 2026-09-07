# Copyright IBM Corp. 2025, 2026

"""Unit tests for the Users resource."""

import copy
from unittest.mock import Mock

import pytest

from pytfe.models.user import User, UserPermissions, UserUpdateCurrentOptions
from pytfe.resources.user import Users


class TestUsers:
    """Test suite for user resource operations."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        return Mock()

    @pytest.fixture
    def users_service(self, mock_transport):
        """Create users service with mocked transport."""
        return Users(mock_transport)

    @pytest.fixture
    def sample_user_response(self):
        """Sample JSON:API response for a user."""
        return {
            "data": {
                "id": "user-MA4GL63FmYRpSFxa",
                "type": "users",
                "attributes": {
                    "username": "admin",
                    "email": "admin@example.com",
                    "is-service-account": False,
                    "auth-method": "hcp_sso",
                    "avatar-url": "https://example.com/avatar.png",
                    "v2-only": True,
                    "permissions": {
                        "can-create-organizations": False,
                        "can-change-email": True,
                        "can-change-username": True,
                    },
                },
            }
        }

    def test_read_user(self, users_service, mock_transport, sample_user_response):
        """Test reading a specific user by ID."""
        mock_transport.request.return_value.json.return_value = sample_user_response

        user_id = "user-MA4GL63FmYRpSFxa"
        user = users_service.read(user_id)

        mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/users/{user_id}"
        )
        assert isinstance(user, User)
        assert user.id == user_id
        assert user.username == "admin"
        assert user.email == "admin@example.com"
        assert user.is_service_account is False
        assert user.auth_method == "hcp_sso"
        assert user.avatar_url == "https://example.com/avatar.png"
        assert user.v2_only is True
        assert isinstance(user.permissions, UserPermissions)
        assert user.permissions is not None
        assert user.permissions.can_create_organizations is False
        assert user.permissions.can_change_email is True
        assert user.permissions.can_change_username is True
        assert user.permissions.can_manage_user_tokens is False
        assert user.permissions.can_view_2fa_settings is False
        assert user.permissions.can_manage_hcp_account is False

    def test_read_user_invalid_id(self, users_service):
        """Test reading a user with an invalid user ID."""
        with pytest.raises(ValueError, match="invalid user id"):
            users_service.read("")

    def test_read_user_with_null_unconfirmed_email(
        self, users_service, mock_transport, sample_user_response
    ):
        """Test reading a user when unconfirmed-email is null."""
        sample_user_response["data"]["attributes"]["unconfirmed-email"] = None
        mock_transport.request.return_value.json.return_value = sample_user_response

        user = users_service.read("user-MA4GL63FmYRpSFxa")

        assert isinstance(user, User)
        assert user.unconfirmed_email is None

    def test_read_user_two_factor_parsing(
        self, users_service, mock_transport, sample_user_response
    ):
        """Test reading a user with two-factor data."""
        modified_response = copy.deepcopy(sample_user_response)
        modified_response["data"]["attributes"]["two-factor"] = {
            "enabled": True,
            "verified": False,
        }
        mock_transport.request.return_value.json.return_value = modified_response

        user_id = "user-MA4GL63FmYRpSFxa"
        user = users_service.read(user_id)

        assert user.two_factor is not None
        assert user.two_factor.enabled is True
        assert user.two_factor.verified is False

    def test_read_user_nullable_bools(
        self, users_service, mock_transport, sample_user_response
    ):
        """Test reading a user when pointer-style boolean fields are null."""
        modified_response = copy.deepcopy(sample_user_response)
        modified_response["data"]["attributes"]["is-site-admin"] = None
        modified_response["data"]["attributes"]["is-admin"] = None
        modified_response["data"]["attributes"]["is-sso-login"] = None
        mock_transport.request.return_value.json.return_value = modified_response

        user_id = "user-MA4GL63FmYRpSFxa"
        user = users_service.read(user_id)

        assert user.is_site_admin is None
        assert user.is_admin is None
        assert user.is_sso_login is None

    def test_read_current_user(
        self, users_service, mock_transport, sample_user_response
    ):
        """Test reading the currently authenticated user."""
        mock_transport.request.return_value.json.return_value = sample_user_response

        user = users_service.read_current()

        mock_transport.request.assert_called_once_with("GET", "/api/v2/account/details")
        assert isinstance(user, User)
        assert user.id == "user-MA4GL63FmYRpSFxa"
        assert user.username == "admin"
        assert user.email == "admin@example.com"

    def test_update_current_user(
        self, users_service, mock_transport, sample_user_response
    ):
        """Test updating the currently authenticated user."""
        mock_transport.request.return_value.json.return_value = sample_user_response
        options = UserUpdateCurrentOptions(
            username="new-admin",
            email="new-admin@example.com",
        )

        user = users_service.update_current(options)

        mock_transport.request.assert_called_once_with(
            "PATCH",
            "/api/v2/account/update",
            json_body={
                "data": {
                    "type": "users",
                    "attributes": {
                        "username": "new-admin",
                        "email": "new-admin@example.com",
                    },
                }
            },
        )
        assert isinstance(user, User)
        assert user.id == "user-MA4GL63FmYRpSFxa"
