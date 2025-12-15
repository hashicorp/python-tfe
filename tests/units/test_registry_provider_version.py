"""Unit tests for the registry_provider_version module."""

from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidKeyIDError,
    InvalidVersionError,
    RequiredPrivateRegistryError,
)
from pytfe.models.registry_provider import (
    RegistryName,
    RegistryProviderID,
)
from pytfe.models.registry_provider_version import (
    RegistryProviderVersion,
    RegistryProviderVersionCreateOptions,
    RegistryProviderVersionID,
)
from pytfe.resources.registry_provider_version import RegistryProviderVersions


class TestRegistryProviderVersions:
    """Test the RegistryProviderVersions service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def versions_service(self, mock_transport):
        """Create a RegistryProviderVersions service with mocked transport."""
        return RegistryProviderVersions(mock_transport)

    @pytest.fixture
    def valid_provider_id(self):
        """Create a valid provider ID."""
        return RegistryProviderID(
            organization_name="test-org",
            registry_name=RegistryName.PRIVATE,
            namespace="test-namespace",
            name="test-provider",
        )

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

    def test_validate_provider_id_success(self, versions_service, valid_provider_id):
        """Test _validate_provider_id with valid provider ID."""
        result = versions_service._validate_provider_id(valid_provider_id)
        assert result is True

    def test_validate_provider_id_invalid_organization(
        self, versions_service, valid_provider_id
    ):
        """Test _validate_provider_id with invalid organization name."""
        valid_provider_id.organization_name = ""
        result = versions_service._validate_provider_id(valid_provider_id)
        assert result is False

    def test_create_version_validations(self, versions_service):
        """Test create method validations."""
        # Test with invalid provider ID
        invalid_provider_id = RegistryProviderID(
            organization_name="",
            registry_name=RegistryName.PRIVATE,
            namespace="test-namespace",
            name="test-provider",
        )
        options = RegistryProviderVersionCreateOptions(
            version="1.0.0", **{"key-id": "test-key-id"}, protocols=["5.0"]
        )

        with pytest.raises(ValueError, match="Invalid provider ID"):
            versions_service.create(invalid_provider_id, options)

    def test_create_version_requires_private_registry(
        self, versions_service, mock_transport
    ):
        """Test create method requires private registry."""
        public_provider_id = RegistryProviderID(
            organization_name="test-org",
            registry_name=RegistryName.PUBLIC,
            namespace="hashicorp",
            name="aws",
        )
        options = RegistryProviderVersionCreateOptions(
            version="1.0.0", **{"key-id": "test-key-id"}, protocols=["5.0"]
        )

        with pytest.raises(RequiredPrivateRegistryError):
            versions_service.create(public_provider_id, options)

    def test_create_version_success(
        self, versions_service, valid_provider_id, mock_transport
    ):
        """Test successful create operation."""
        mock_response_data = {
            "data": {
                "id": "provver-123",
                "type": "registry-provider-versions",
                "attributes": {
                    "version": "1.0.0",
                    "created-at": "2023-01-01T12:00:00Z",
                    "updated-at": "2023-01-01T12:00:00Z",
                    "key-id": "test-key-id",
                    "protocols": ["5.0"],
                    "shasums-uploaded": False,
                    "shasums-sig-uploaded": False,
                    "permissions": {
                        "can-delete": True,
                        "can-upload-asset": True,
                    },
                },
                "relationships": {
                    "registry-provider": {
                        "data": {"id": "prov-123", "type": "registry-providers"}
                    }
                },
                "links": {
                    "shasums-upload": "https://example.com/upload",
                    "shasums-sig-upload": "https://example.com/sig-upload",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = RegistryProviderVersionCreateOptions(
            version="1.0.0", **{"key-id": "test-key-id"}, protocols=["5.0"]
        )

        result = versions_service.create(valid_provider_id, options)

        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/organizations/test-org/registry-providers/private/test-namespace/test-provider/versions",
            json_body={
                "data": {
                    "type": "registry-provider-versions",
                    "attributes": {
                        "version": "1.0.0",
                        "key-id": "test-key-id",
                        "protocols": ["5.0"],
                    },
                }
            },
        )

        assert isinstance(result, RegistryProviderVersion)
        assert result.id == "provver-123"
        assert result.version == "1.0.0"
        assert result.key_id == "test-key-id"
        assert result.protocols == ["5.0"]
        assert result.permissions.can_delete is True

    def test_list_versions_success_without_options(
        self, versions_service, valid_provider_id, mock_transport
    ):
        """Test successful list operation without options."""
        mock_response_data = {
            "data": [
                {
                    "id": "provver-123",
                    "type": "registry-provider-versions",
                    "attributes": {
                        "version": "1.0.0",
                        "created-at": "2023-01-01T12:00:00Z",
                        "updated-at": "2023-01-01T12:00:00Z",
                        "key-id": "test-key-id",
                        "protocols": ["5.0"],
                        "shasums-uploaded": False,
                        "shasums-sig-uploaded": False,
                        "permissions": {
                            "can-delete": True,
                            "can-upload-asset": True,
                        },
                    },
                },
                {
                    "id": "provver-456",
                    "type": "registry-provider-versions",
                    "attributes": {
                        "version": "1.1.0",
                        "created-at": "2023-02-01T12:00:00Z",
                        "updated-at": "2023-02-01T12:00:00Z",
                        "key-id": "test-key-id-2",
                        "protocols": ["5.0", "6.0"],
                        "shasums-uploaded": True,
                        "shasums-sig-uploaded": True,
                        "permissions": {
                            "can-delete": True,
                            "can-upload-asset": False,
                        },
                    },
                },
            ],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "total-pages": 1,
                    "prev-page": None,
                    "next-page": None,
                    "total-count": 2,
                }
            },
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        with patch.object(
            versions_service, "_list", return_value=mock_response_data["data"]
        ):
            result = list(versions_service.list(valid_provider_id))

        assert len(result) == 2
        assert result[0].id == "provver-123"
        assert result[0].version == "1.0.0"
        assert result[0].shasums_uploaded is False
        assert result[1].id == "provver-456"
        assert result[1].version == "1.1.0"
        assert result[1].shasums_uploaded is True

    def test_read_version_validations(self, versions_service):
        """Test read method with invalid version ID."""
        invalid_version_id = RegistryProviderVersionID(
            organization_name="",
            registry_name=RegistryName.PRIVATE,
            namespace="test-namespace",
            name="test-provider",
            version="1.0.0",
        )

        with pytest.raises(ValueError, match="Invalid provider ID"):
            versions_service.read(invalid_version_id)

    def test_read_version_success(
        self, versions_service, valid_version_id, mock_transport
    ):
        """Test successful read operation."""
        mock_response_data = {
            "data": {
                "id": "provver-789",
                "type": "registry-provider-versions",
                "attributes": {
                    "version": "1.0.0",
                    "created-at": "2023-01-01T12:00:00Z",
                    "updated-at": "2023-01-01T12:00:00Z",
                    "key-id": "test-key-id",
                    "protocols": ["5.0", "6.0"],
                    "shasums-uploaded": True,
                    "shasums-sig-uploaded": True,
                    "permissions": {
                        "can-delete": True,
                        "can-upload-asset": False,
                    },
                },
                "relationships": {
                    "registry-provider": {
                        "data": {"id": "prov-123", "type": "registry-providers"}
                    },
                    "platforms": {
                        "data": [
                            {"id": "plat-123", "type": "registry-provider-platforms"}
                        ]
                    },
                },
                "links": {
                    "shasums-download": "https://example.com/download",
                    "shasums-sig-download": "https://example.com/sig-download",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        result = versions_service.read(valid_version_id)

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/organizations/test-org/registry-providers/private/test-namespace/test-provider/versions/1.0.0",
        )

        assert isinstance(result, RegistryProviderVersion)
        assert result.id == "provver-789"
        assert result.version == "1.0.0"
        assert result.key_id == "test-key-id"
        assert result.protocols == ["5.0", "6.0"]
        assert result.shasums_uploaded is True
        assert result.shasums_sig_uploaded is True

    def test_delete_version_success(
        self, versions_service, valid_version_id, mock_transport
    ):
        """Test successful delete operation."""
        result = versions_service.delete(valid_version_id)

        mock_transport.request.assert_called_once_with(
            "DELETE",
            path="/api/v2/organizations/test-org/registry-providers/private/test-namespace/test-provider/versions/1.0.0",
        )

        assert result is None

    def test_registry_provider_version_from_success(self, versions_service):
        """Test _registry_provider_version_from with valid data."""
        data = {
            "id": "provver-123",
            "type": "registry-provider-versions",
            "attributes": {
                "version": "1.0.0",
                "created-at": "2023-01-01T12:00:00Z",
                "updated-at": "2023-01-01T12:00:00Z",
                "key-id": "test-key-id",
                "protocols": ["5.0"],
                "shasums-uploaded": False,
                "shasums-sig-uploaded": False,
                "permissions": {
                    "can-delete": True,
                    "can-upload-asset": True,
                },
            },
            "relationships": {
                "registry-provider": {
                    "data": {"id": "prov-123", "type": "registry-providers"}
                },
                "platforms": {
                    "data": [
                        {"id": "plat-123", "type": "registry-provider-platforms"},
                        {"id": "plat-456", "type": "registry-provider-platforms"},
                    ]
                },
            },
        }

        result = versions_service._registry_provider_version_from(data)

        assert isinstance(result, RegistryProviderVersion)
        assert result.id == "provver-123"
        assert result.version == "1.0.0"
        assert result.key_id == "test-key-id"
        assert result.registry_provider == {
            "id": "prov-123",
            "type": "registry-providers",
        }
        assert result.registry_provider_platforms is not None
        assert len(result.registry_provider_platforms) == 2

    def test_create_options_validation_invalid_version(self):
        """Test RegistryProviderVersionCreateOptions with invalid version."""
        with pytest.raises(InvalidVersionError):
            RegistryProviderVersionCreateOptions(
                version="", **{"key-id": "test-key-id"}, protocols=["5.0"]
            )

    def test_create_options_validation_invalid_key_id(self):
        """Test RegistryProviderVersionCreateOptions with invalid key_id."""
        with pytest.raises(InvalidKeyIDError):
            RegistryProviderVersionCreateOptions(
                version="1.0.0", **{"key-id": ""}, protocols=["5.0"]
            )

    def test_create_options_validation_success(self):
        """Test RegistryProviderVersionCreateOptions with valid data."""
        options = RegistryProviderVersionCreateOptions(
            version="1.0.0", **{"key-id": "test-key-id"}, protocols=["5.0", "6.0"]
        )
        assert options.version == "1.0.0"
        assert options.key_id == "test-key-id"
        assert options.protocols == ["5.0", "6.0"]

    def test_version_id_validation_success(self):
        """Test RegistryProviderVersionID with valid data."""
        version_id = RegistryProviderVersionID(
            organization_name="test-org",
            registry_name=RegistryName.PRIVATE,
            namespace="test-namespace",
            name="test-provider",
            version="1.0.0",
        )
        assert version_id.organization_name == "test-org"
        assert version_id.registry_name == RegistryName.PRIVATE
        assert version_id.namespace == "test-namespace"
        assert version_id.name == "test-provider"
        assert version_id.version == "1.0.0"
