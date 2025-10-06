"""Test the SSH Keys functionality."""

from unittest.mock import Mock

import pytest

from src.tfe._http import HTTPTransport
from src.tfe.errors import (
    InvalidOrgError,
    InvalidSSHKeyIDError,
)
from src.tfe.models.ssh_key import (
    SSHKeyCreateOptions,
    SSHKeyUpdateOptions,
)
from src.tfe.resources.ssh_keys import SSHKeys


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
            ssh_keys_service.list("")

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
