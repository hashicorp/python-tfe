"""Test the Reserved Tag Keys functionality."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidOrgError,
    ValidationError,
)
from pytfe.models.reserved_tag_key import (
    ReservedTagKeyCreateOptions,
    ReservedTagKeyListOptions,
    ReservedTagKeyUpdateOptions,
)
from pytfe.resources.reserved_tag_key import ReservedTagKey


class TestReservedTagKeyParsing:
    """Test the reserved tag key parsing functionality."""

    @pytest.fixture
    def reserved_tag_key_service(self):
        """Create a ReservedTagKey service for testing parsing."""
        mock_transport = Mock(spec=HTTPTransport)
        return ReservedTagKey(mock_transport)

    def test_parse_reserved_tag_key_minimal(self, reserved_tag_key_service):
        """Test _parse_reserved_tag_key with minimal data."""
        data = {
            "id": "rtk-123",
            "type": "reserved-tag-keys",
            "attributes": {
                "key": "environment",
                "disable-overrides": False,
            },
        }
        reserved_tag_key = reserved_tag_key_service._parse_reserved_tag_key(data)
        assert reserved_tag_key.id == "rtk-123"
        assert reserved_tag_key.key == "environment"
        assert reserved_tag_key.disable_overrides is False

    def test_parse_reserved_tag_key_with_dates(self, reserved_tag_key_service):
        """Test _parse_reserved_tag_key with created_at and updated_at."""
        data = {
            "id": "rtk-456",
            "type": "reserved-tag-keys",
            "attributes": {
                "key": "cost-center",
                "disable-overrides": True,
                "created-at": "2024-08-13T23:06:42.523Z",
                "updated-at": "2024-08-13T23:06:42.523Z",
            },
        }
        reserved_tag_key = reserved_tag_key_service._parse_reserved_tag_key(data)
        assert reserved_tag_key.id == "rtk-456"
        assert reserved_tag_key.key == "cost-center"
        assert reserved_tag_key.disable_overrides is True
        assert reserved_tag_key.created_at is not None
        assert reserved_tag_key.updated_at is not None


class TestReservedTagKey:
    """Test the Reserved Tag Key service."""

    @pytest.fixture
    def reserved_tag_key_service(self):
        """Create a ReservedTagKey service for testing."""
        mock_transport = Mock(spec=HTTPTransport)
        return ReservedTagKey(mock_transport)

    def test_list_reserved_tag_keys_invalid_org(self, reserved_tag_key_service):
        """Test listing reserved tag keys with invalid organization."""
        with pytest.raises(InvalidOrgError):
            reserved_tag_key_service.list("")

    def test_create_reserved_tag_key_invalid_org(self, reserved_tag_key_service):
        """Test creating reserved tag key with invalid organization."""
        options = ReservedTagKeyCreateOptions(
            key="environment", disable_overrides=False
        )
        with pytest.raises(InvalidOrgError):
            reserved_tag_key_service.create("", options)

    def test_read_reserved_tag_key_not_implemented(self, reserved_tag_key_service):
        """Test reading reserved tag key raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            reserved_tag_key_service.read("rtk-123")

    def test_update_reserved_tag_key_invalid_id(self, reserved_tag_key_service):
        """Test updating reserved tag key with invalid ID."""
        options = ReservedTagKeyUpdateOptions(key="updated-key")
        with pytest.raises(ValidationError):
            reserved_tag_key_service.update("", options)

    def test_delete_reserved_tag_key_invalid_id(self, reserved_tag_key_service):
        """Test deleting reserved tag key with invalid ID."""
        with pytest.raises(ValidationError):
            reserved_tag_key_service.delete("")

    def test_reserved_tag_key_create_options_model(self):
        """Test ReservedTagKeyCreateOptions model validation."""
        options = ReservedTagKeyCreateOptions(key="environment", disable_overrides=True)
        assert options.key == "environment"
        assert options.disable_overrides is True

    def test_reserved_tag_key_update_options_model(self):
        """Test ReservedTagKeyUpdateOptions model validation."""
        options = ReservedTagKeyUpdateOptions(
            key="updated-environment", disable_overrides=False
        )
        assert options.key == "updated-environment"
        assert options.disable_overrides is False

    def test_reserved_tag_key_list_options_model(self):
        """Test ReservedTagKeyListOptions model validation."""
        options = ReservedTagKeyListOptions(page_number=2, page_size=50)
        assert options.page_number == 2
        assert options.page_size == 50
