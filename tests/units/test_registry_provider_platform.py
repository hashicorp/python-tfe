# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the registry_provider_platform module."""

from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidArchError,
    InvalidNameError,
    InvalidNamespaceError,
    InvalidOSError,
    InvalidOrgError,
    InvalidVersionError,
    RequiredArchError,
    RequiredFilenameError,
    RequiredOSError,
    RequiredPrivateRegistryError,
    RequiredShasumError,
)
from pytfe.models.registry_provider import RegistryName
from pytfe.models.registry_provider_platform import (
    RegistryProviderPlatform,
    RegistryProviderPlatformCreateOptions,
    RegistryProviderPlatformID,
    RegistryProviderPlatformListOptions,
)
from pytfe.models.registry_provider_version import (
    RegistryProviderVersion,
    RegistryProviderVersionID,
)
from pytfe.resources.registry_provider_platform import RegistryProviderPlatforms


class TestRegistryProviderPlatforms:
    """Test the RegistryProviderPlatforms service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def platforms_service(self, mock_transport):
        """Create a RegistryProviderPlatforms service with mocked transport."""
        return RegistryProviderPlatforms(mock_transport)

    @pytest.fixture
    def valid_version_id(self):
        """Create a valid version ID."""
        return RegistryProviderVersionID(
            organization_name="test-org",
            registry_name=RegistryName.PRIVATE,
            namespace="test-namespace",
            name="test-provider",
            version="1.0.0",
        )

    @pytest.fixture
    def valid_platform_id(self):
        """Create a valid platform ID."""
        return RegistryProviderPlatformID(
            organization_name="test-org",
            registry_name=RegistryName.PRIVATE,
            namespace="test-namespace",
            name="test-provider",
            version="1.0.0",
            os="linux",
            arch="amd64",
        )

    @pytest.fixture
    def platform_api_data(self):
        """Typical API response data for a single platform."""
        return {
            "id": "provpltfrm-123",
            "type": "registry-provider-platforms",
            "attributes": {
                "os": "linux",
                "arch": "amd64",
                "filename": "terraform-provider-test_1.0.0_linux_amd64.zip",
                "shasum": "abc123def456",
                "provider-binary-uploaded": False,
                "permissions": {
                    "can-delete": True,
                    "can-upload-asset": True,
                },
            },
            "relationships": {
                "registry-provider-version": {
                    "data": {
                        "id": "provver-456",
                        "type": "registry-provider-versions",
                    }
                }
            },
            "links": {
                "provider-binary-upload": "https://example.com/upload",
            },
        }

    # -------------------------------------------------------------------------
    # ID validation tests
    # -------------------------------------------------------------------------

    def test_invalid_platform_id_fields(self):
        """Test RegistryProviderPlatformID raises correct error for each invalid field."""
        base = {
            "organization_name": "test-org",
            "registry_name": RegistryName.PRIVATE,
            "namespace": "test-namespace",
            "name": "test-provider",
            "version": "1.0.0",
            "os": "linux",
            "arch": "amd64",
        }
        with pytest.raises(InvalidOrgError):
            RegistryProviderPlatformID(**{**base, "organization_name": ""})
        with pytest.raises(InvalidOrgError):
            RegistryProviderPlatformID(**{**base, "organization_name": "   "})
        with pytest.raises(InvalidNameError):
            RegistryProviderPlatformID(**{**base, "name": ""})
        with pytest.raises(InvalidNamespaceError):
            RegistryProviderPlatformID(**{**base, "namespace": ""})
        with pytest.raises(InvalidVersionError):
            RegistryProviderPlatformID(**{**base, "version": ""})
        with pytest.raises(RequiredPrivateRegistryError):
            RegistryProviderPlatformID(**{**base, "registry_name": RegistryName.PUBLIC})
        with pytest.raises(InvalidOSError):
            RegistryProviderPlatformID(**{**base, "os": ""})
        with pytest.raises(InvalidArchError):
            RegistryProviderPlatformID(**{**base, "arch": ""})

    def test_valid_platform_id(self, valid_platform_id):
        """Test RegistryProviderPlatformID with valid data."""
        assert valid_platform_id.organization_name == "test-org"
        assert valid_platform_id.registry_name == RegistryName.PRIVATE
        assert valid_platform_id.namespace == "test-namespace"
        assert valid_platform_id.name == "test-provider"
        assert valid_platform_id.version == "1.0.0"
        assert valid_platform_id.os == "linux"
        assert valid_platform_id.arch == "amd64"

    # -------------------------------------------------------------------------
    # CreateOptions validation tests
    # -------------------------------------------------------------------------

    def test_create_options_invalid_fields(self):
        """Test RegistryProviderPlatformCreateOptions raises correct error for each invalid field."""
        base = {
            "os": "linux",
            "arch": "amd64",
            "shasum": "abc123",
            "filename": "provider.zip",
        }
        with pytest.raises(RequiredOSError):
            RegistryProviderPlatformCreateOptions(**{**base, "os": ""})
        with pytest.raises(RequiredArchError):
            RegistryProviderPlatformCreateOptions(**{**base, "arch": ""})
        with pytest.raises(RequiredShasumError):
            RegistryProviderPlatformCreateOptions(**{**base, "shasum": ""})
        with pytest.raises(RequiredFilenameError):
            RegistryProviderPlatformCreateOptions(**{**base, "filename": ""})

    def test_create_options_valid(self):
        """Test RegistryProviderPlatformCreateOptions with valid data."""
        options = RegistryProviderPlatformCreateOptions(
            os="linux",
            arch="amd64",
            shasum="abc123def456",
            filename="terraform-provider-test_1.0.0_linux_amd64.zip",
        )
        assert options.os == "linux"
        assert options.arch == "amd64"
        assert options.shasum == "abc123def456"
        assert options.filename == "terraform-provider-test_1.0.0_linux_amd64.zip"

    # -------------------------------------------------------------------------
    # create()
    # -------------------------------------------------------------------------

    def test_create_platform_success(
        self, platforms_service, valid_version_id, mock_transport, platform_api_data
    ):
        """Test successful create operation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": platform_api_data}
        mock_transport.request.return_value = mock_response

        options = RegistryProviderPlatformCreateOptions(
            os="linux",
            arch="amd64",
            shasum="abc123def456",
            filename="terraform-provider-test_1.0.0_linux_amd64.zip",
        )

        result = platforms_service.create(valid_version_id, options)

        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/organizations/test-org/registry-providers/private/test-namespace/test-provider/versions/1.0.0/platforms",
            json_body={
                "data": {
                    "type": "registry-provider-platforms",
                    "attributes": {
                        "os": "linux",
                        "arch": "amd64",
                        "shasum": "abc123def456",
                        "filename": "terraform-provider-test_1.0.0_linux_amd64.zip",
                    },
                }
            },
        )

        assert isinstance(result, RegistryProviderPlatform)
        assert result.id == "provpltfrm-123"
        assert result.os == "linux"
        assert result.arch == "amd64"
        assert result.shasum == "abc123def456"
        assert result.provider_binary_uploaded is False
        assert result.permissions.can_delete is True
        assert result.permissions.can_upload_asset is True

    # -------------------------------------------------------------------------
    # list()
    # -------------------------------------------------------------------------

    def test_list_platforms_success(
        self, platforms_service, valid_version_id, platform_api_data
    ):
        """Test successful list operation."""
        second = {**platform_api_data, "id": "provpltfrm-456"}
        second["attributes"] = {**platform_api_data["attributes"], "os": "darwin", "arch": "arm64"}

        with patch.object(
            platforms_service, "_list", return_value=[platform_api_data, second]
        ):
            result = list(platforms_service.list(valid_version_id))

        assert len(result) == 2
        assert result[0].id == "provpltfrm-123"
        assert result[0].os == "linux"
        assert result[0].arch == "amd64"
        assert result[1].id == "provpltfrm-456"
        assert result[1].os == "darwin"
        assert result[1].arch == "arm64"

    def test_list_platforms_with_options(
        self, platforms_service, valid_version_id, mock_transport, platform_api_data
    ):
        """Test list operation passes page_size param."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": [platform_api_data]}
        mock_transport.request.return_value = mock_response

        options = RegistryProviderPlatformListOptions(page_size=10)

        with patch.object(
            platforms_service, "_list", return_value=[platform_api_data]
        ) as mock_list:
            result = list(platforms_service.list(valid_version_id, options))
            mock_list.assert_called_once_with(
                path="/api/v2/organizations/test-org/registry-providers/private/test-namespace/test-provider/versions/1.0.0/platforms",
                params={"page[size]": 10},
            )

        assert len(result) == 1

    def test_list_platforms_empty(self, platforms_service, valid_version_id):
        """Test list operation returns empty iterator when no platforms exist."""
        with patch.object(platforms_service, "_list", return_value=[]):
            result = list(platforms_service.list(valid_version_id))

        assert result == []

    # -------------------------------------------------------------------------
    # read()
    # -------------------------------------------------------------------------

    def test_read_platform_success(
        self, platforms_service, valid_platform_id, mock_transport, platform_api_data
    ):
        """Test successful read operation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": platform_api_data}
        mock_transport.request.return_value = mock_response

        result = platforms_service.read(valid_platform_id)

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/organizations/test-org/registry-providers/private/test-namespace/test-provider/versions/1.0.0/platforms/linux/amd64",
        )

        assert isinstance(result, RegistryProviderPlatform)
        assert result.id == "provpltfrm-123"
        assert result.os == "linux"
        assert result.arch == "amd64"

    # -------------------------------------------------------------------------
    # delete()
    # -------------------------------------------------------------------------

    def test_delete_platform_success(
        self, platforms_service, valid_platform_id, mock_transport
    ):
        """Test successful delete operation."""
        result = platforms_service.delete(valid_platform_id)

        mock_transport.request.assert_called_once_with(
            "DELETE",
            path="/api/v2/organizations/test-org/registry-providers/private/test-namespace/test-provider/versions/1.0.0/platforms/linux/amd64",
        )

        assert result is None

    # -------------------------------------------------------------------------
    # _registry_provider_platform_from()
    # -------------------------------------------------------------------------

    def test_platform_from_full_data(self, platforms_service, platform_api_data):
        """Test _registry_provider_platform_from with full API response including relationships and links."""
        result = platforms_service._registry_provider_platform_from(platform_api_data)

        assert isinstance(result, RegistryProviderPlatform)
        assert result.id == "provpltfrm-123"
        assert result.os == "linux"
        assert result.arch == "amd64"
        assert result.filename == "terraform-provider-test_1.0.0_linux_amd64.zip"
        assert result.shasum == "abc123def456"
        assert result.provider_binary_uploaded is False
        assert result.permissions.can_delete is True
        assert result.permissions.can_upload_asset is True
        # registry-provider-version relation parsed as typed stub
        assert isinstance(result.registry_provider_version, RegistryProviderVersion)
        assert result.registry_provider_version.id == "provver-456"
        # links preserved
        assert result.links is not None
        assert "provider-binary-upload" in result.links

    def test_platform_from_no_relationships(self, platforms_service):
        """Test _registry_provider_platform_from when relationships are absent."""
        data = {
            "id": "provpltfrm-789",
            "type": "registry-provider-platforms",
            "attributes": {
                "os": "windows",
                "arch": "amd64",
                "filename": "terraform-provider-test_1.0.0_windows_amd64.zip",
                "shasum": "deadbeef",
                "provider-binary-uploaded": True,
                "permissions": {
                    "can-delete": False,
                    "can-upload-asset": False,
                },
            },
        }

        result = platforms_service._registry_provider_platform_from(data)

        assert result.id == "provpltfrm-789"
        assert result.os == "windows"
        assert result.arch == "amd64"
        assert result.registry_provider_version is None
        assert result.links is None

    def test_platform_from_null_version_relationship(self, platforms_service):
        """Test _registry_provider_platform_from when registry-provider-version data is null."""
        data = {
            "id": "provpltfrm-abc",
            "type": "registry-provider-platforms",
            "attributes": {
                "os": "linux",
                "arch": "arm64",
                "filename": "provider.zip",
                "shasum": "abc123",
                "provider-binary-uploaded": False,
                "permissions": {"can-delete": True, "can-upload-asset": True},
            },
            "relationships": {
                "registry-provider-version": {"data": None}
            },
        }

        result = platforms_service._registry_provider_platform_from(data)

        assert result.registry_provider_version is None
