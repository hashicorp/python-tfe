"""Unit tests for the Users resource."""

from unittest.mock import Mock

import pytest

from pytfe.models.user import User
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
        assert user.permissions == {
            "can-create-organizations": False,
            "can-change-email": True,
            "can-change-username": True,
        }

    def test_read_user_invalid_id(self, users_service):
        """Test reading a user with an invalid user ID."""
        with pytest.raises(ValueError, match="invalid user id"):
            users_service.read("")
