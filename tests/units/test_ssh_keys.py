# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Test the SSH Keys functionality."""

from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidOrgError,
    InvalidSSHKeyIDError,
)
from pytfe.models.ssh_key import (
    SSHKey,
    SSHKeyCreateOptions,
    SSHKeyListOptions,
    SSHKeyUpdateOptions,
)
from pytfe.resources.ssh_keys import SSHKeys


class TestSSHKeyParsing:
    """Test the SSH key parsing functionality."""

    @pytest.fixture
    def ssh_keys_service(self):
        """Create an SSHKeys service for testing parsing."""
        mock_transport = Mock(spec=HTTPTransport)
        return SSHKeys(mock_transport)

    def test_parse_ssh_key_minimal(self, ssh_keys_service):
        """Test _parse_ssh_key with minimal data."""
        data = {
            "id": "sshkey-123",
            "type": "ssh-keys",
            "attributes": {
                "name": "My SSH Key",
            },
        }
        ssh_key = ssh_keys_service._parse_ssh_key(data)
        assert ssh_key.id == "sshkey-123"
        assert ssh_key.name == "My SSH Key"


class TestSSHKeys:
    """Test the SSH Keys service."""

    @pytest.fixture
    def ssh_keys_service(self):
        """Create an SSHKeys service for testing."""
        mock_transport = Mock(spec=HTTPTransport)
        return SSHKeys(mock_transport)

    def test_list_ssh_keys_invalid_org(self, ssh_keys_service):
        """Test listing SSH keys with invalid organization."""
        with pytest.raises(InvalidOrgError):
            # Need to consume the iterator to trigger the error
            list(ssh_keys_service.list(""))

    def test_create_ssh_key_invalid_org(self, ssh_keys_service):
        """Test creating SSH key with invalid organization."""
        options = SSHKeyCreateOptions(name="Test", value="ssh-rsa AAAAB3...")
        with pytest.raises(InvalidOrgError):
            ssh_keys_service.create("", options)

    def test_read_ssh_key_invalid_id(self, ssh_keys_service):
        """Test reading SSH key with invalid ID."""
        with pytest.raises(InvalidSSHKeyIDError):
            ssh_keys_service.read("")

    def test_update_ssh_key_invalid_id(self, ssh_keys_service):
        """Test updating SSH key with invalid ID."""
        options = SSHKeyUpdateOptions(name="Updated")
        with pytest.raises(InvalidSSHKeyIDError):
            ssh_keys_service.update("", options)

    def test_delete_ssh_key_invalid_id(self, ssh_keys_service):
        """Test deleting SSH key with invalid ID."""
        with pytest.raises(InvalidSSHKeyIDError):
            ssh_keys_service.delete("")

    def test_list_ssh_keys_success(self, ssh_keys_service):
        """Test successful list operation with iterator."""
        mock_list_data = [
            {
                "id": "sshkey-123",
                "attributes": {
                    "name": "Test SSH Key 1",
                },
            },
            {
                "id": "sshkey-456",
                "attributes": {
                    "name": "Test SSH Key 2",
                },
            },
        ]

        with patch.object(ssh_keys_service, "_list") as mock_list:
            mock_list.return_value = mock_list_data

            # Test with options
            options = SSHKeyListOptions(page_number=1, page_size=5)
            result = list(ssh_keys_service.list("test-org", options))

            # Verify _list was called with correct path
            assert mock_list.call_count == 1
            call_args = mock_list.call_args
            assert call_args[0][0] == "/api/v2/organizations/test-org/ssh-keys"

            # Verify params structure includes pagination and options
            params = call_args[1]["params"]
            assert "page[number]" in params
            assert "page[size]" in params

            # Verify result structure - iterator yields SSHKey objects
            assert len(result) == 2

            # Verify SSH key objects were created correctly from response data
            key1 = result[0]
            assert isinstance(key1, SSHKey)
            assert key1.id == "sshkey-123"
            assert key1.name == "Test SSH Key 1"

            key2 = result[1]
            assert isinstance(key2, SSHKey)
            assert key2.id == "sshkey-456"
            assert key2.name == "Test SSH Key 2"

    def test_list_ssh_keys_empty(self, ssh_keys_service):
        """Test list operation returning empty results."""
        with patch.object(ssh_keys_service, "_list") as mock_list:
            mock_list.return_value = []

            result = list(ssh_keys_service.list("test-org"))

            assert len(result) == 0
            mock_list.assert_called_once()
