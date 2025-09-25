"""
Comprehensive unit tests for configuration version operations in the Python TFE SDK.

This test suite covers all 12 configuration version methods:
1. list() - List configuration versions for a workspace
2. create() - Create new configuration versions
3. read() - Read configuration version details
4. upload() - Upload Terraform configurations (requires go-slug)
5. download() - Download configuration version archives
6. archive() - Archive configuration versions
7. read_with_options() - Read with include options
8. create_for_registry_module() - Create configuration versions for registry modules (BETA)
9. upload_tar_gzip() - Direct tar.gz archive upload
10. soft_delete_backing_data() - Soft delete backing data (Enterprise only)
11. restore_backing_data() - Restore backing data (Enterprise only)
12. permanently_delete_backing_data() - Permanently delete backing data (Enterprise only)
"""

import io
from unittest.mock import Mock, patch

import pytest

from src.tfe.errors import NotFound, TFEError
from src.tfe.models.configuration_version_types import (
    ConfigurationSource,
    ConfigurationStatus,
    ConfigurationVersionCreateOptions,
    ConfigurationVersionListOptions,
    ConfigurationVersionReadOptions,
    ConfigVerIncludeOpt,
)
from src.tfe.resources.configuration_version import ConfigurationVersions


@pytest.fixture
def mock_transport():
    """Create a mock transport for testing."""
    return Mock()


@pytest.fixture
def configuration_versions_service(mock_transport):
    """Create a ConfigurationVersions service with mocked transport."""
    return ConfigurationVersions(mock_transport)


@pytest.fixture
def sample_cv_data():
    """Sample configuration version data from API."""
    return {
        "id": "cv-ntv3HbhJqvFzamy7",
        "type": "configuration-versions",
        "attributes": {
            "auto-queue-runs": True,
            "error": None,
            "error-message": None,
            "source": "tfe-api",
            "speculative": False,
            "status": "pending",
            "status-timestamps": {},
            "upload-url": "https://archivist.terraform.io/v1/object/dmF1bHQ6djE6WVkraFg2OE1XWkw2SzIyVGN6cHdZb2s2SnBQNnNnTjNLdWRZNk1O",
            "provisional": False,
        },
        "relationships": {
            "workspace": {"data": {"id": "ws-YnyXLq9fy38afEeb", "type": "workspaces"}}
        },
        "links": {"self": "/api/v2/configuration-versions/cv-ntv3HbhJqvFzamy7"},
    }


@pytest.fixture
def sample_cv_with_ingress_data():
    """Sample configuration version data with ingress attributes."""
    return {
        "id": "cv-ntv3HbhJqvFzamy7",
        "type": "configuration-versions",
        "attributes": {
            "auto-queue-runs": True,
            "error": None,
            "error-message": None,
            "source": "github",
            "speculative": False,
            "status": "uploaded",
            "status-timestamps": {"uploaded-at": "2024-01-15T10:30:00Z"},
            "upload-url": None,
            "provisional": False,
            "ingress-attributes": {
                "branch": "main",
                "clone-url": "https://github.com/example/repo.git",
                "commit-message": "Update configuration",
                "commit-sha": "abc123def456",
                "commit-url": "https://github.com/example/repo/commit/abc123def456",
                "compare-url": "https://github.com/example/repo/compare/xyz...abc123def456",
                "identifier": "example/repo",
                "is-pull-request": False,
                "on-default-branch": True,
                "pull-request-number": None,
                "pull-request-url": None,
                "pull-request-title": None,
                "pull-request-body": None,
                "sender-username": "user123",
                "sender-avatar-url": "https://github.com/avatars/user123",
                "sender-html-url": "https://github.com/user123",
                "tag": None,
            },
        },
        "relationships": {
            "workspace": {"data": {"id": "ws-YnyXLq9fy38afEeb", "type": "workspaces"}}
        },
    }


class TestConfigurationVersionsList:
    """Test configuration versions list functionality."""

    def test_list_basic(
        self, configuration_versions_service, mock_transport, sample_cv_data
    ):
        """Test basic list functionality."""
        # Mock the paginated response for the _list method
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [sample_cv_data],
            "meta": {
                "pagination": {"current-page": 1, "page-size": 20, "total-pages": 1}
            },
            "links": {"next": None},
        }
        mock_transport.request.return_value = mock_response

        workspace_id = "ws-YnyXLq9fy38afEeb"
        cv_list = list(configuration_versions_service.list(workspace_id))

        # Verify the request includes default pagination params
        mock_transport.request.assert_called_with(
            "GET",
            f"/api/v2/workspaces/{workspace_id}/configuration-versions",
            params={"page[number]": 1, "page[size]": 100},
        )

        # Verify the result
        assert len(cv_list) == 1
        cv = cv_list[0]
        assert cv.id == "cv-ntv3HbhJqvFzamy7"
        assert cv.status == ConfigurationStatus.PENDING
        assert cv.source == ConfigurationSource.API
        assert cv.auto_queue_runs is True
        assert cv.speculative is False

    def test_list_with_options(
        self, configuration_versions_service, mock_transport, sample_cv_data
    ):
        """Test list with options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [sample_cv_data],
            "meta": {
                "pagination": {"current-page": 1, "page-size": 5, "total-pages": 1}
            },
            "links": {"next": None},
        }
        mock_transport.request.return_value = mock_response

        workspace_id = "ws-YnyXLq9fy38afEeb"
        options = ConfigurationVersionListOptions(
            include=[ConfigVerIncludeOpt.INGRESS_ATTRIBUTES], page_size=5, page_number=1
        )

        list(configuration_versions_service.list(workspace_id, options))

        # Verify the request includes options
        expected_params = {
            "include": "ingress_attributes",
            "page[size]": "5",
            "page[number]": "1",
        }
        mock_transport.request.assert_called_with(
            "GET",
            f"/api/v2/workspaces/{workspace_id}/configuration-versions",
            params=expected_params,
        )

    def test_list_invalid_workspace_id(self, configuration_versions_service):
        """Test list with invalid workspace ID."""
        with pytest.raises(ValueError, match="invalid workspace ID"):
            list(configuration_versions_service.list(""))


class TestConfigurationVersionsCreate:
    """Test configuration versions create functionality."""

    def test_create_basic(
        self, configuration_versions_service, mock_transport, sample_cv_data
    ):
        """Test basic create functionality."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_cv_data}
        mock_transport.request.return_value = mock_response

        workspace_id = "ws-YnyXLq9fy38afEeb"
        options = ConfigurationVersionCreateOptions(
            auto_queue_runs=True, speculative=False
        )

        cv = configuration_versions_service.create(workspace_id, options)

        # Verify the request
        expected_data = {
            "data": {
                "type": "configuration-versions",
                "attributes": {"auto-queue-runs": True, "speculative": False},
            }
        }
        mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/workspaces/{workspace_id}/configuration-versions",
            json_body=expected_data,
        )

        # Verify the result
        assert cv.id == "cv-ntv3HbhJqvFzamy7"
        assert cv.auto_queue_runs is True
        assert cv.speculative is False

    def test_create_with_provisional(
        self, configuration_versions_service, mock_transport, sample_cv_data
    ):
        """Test create with provisional option."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_cv_data}
        mock_transport.request.return_value = mock_response

        workspace_id = "ws-YnyXLq9fy38afEeb"
        options = ConfigurationVersionCreateOptions(
            auto_queue_runs=False, speculative=True, provisional=True
        )

        configuration_versions_service.create(workspace_id, options)

        # Verify provisional is included in request
        call_args = mock_transport.request.call_args
        json_body = call_args.kwargs["json_body"]
        assert json_body["data"]["attributes"]["provisional"] is True

    def test_create_default_options(
        self, configuration_versions_service, mock_transport, sample_cv_data
    ):
        """Test create with default options."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_cv_data}
        mock_transport.request.return_value = mock_response

        workspace_id = "ws-YnyXLq9fy38afEeb"
        configuration_versions_service.create(workspace_id)

        # Should use default options
        call_args = mock_transport.request.call_args
        json_body = call_args.kwargs["json_body"]
        assert json_body["data"]["type"] == "configuration-versions"
        assert json_body["data"]["attributes"] == {}


class TestConfigurationVersionsRead:
    """Test configuration versions read functionality."""

    def test_read_basic(
        self, configuration_versions_service, mock_transport, sample_cv_data
    ):
        """Test basic read functionality."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_cv_data}
        mock_transport.request.return_value = mock_response

        cv_id = "cv-ntv3HbhJqvFzamy7"
        cv = configuration_versions_service.read(cv_id)

        mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/configuration-versions/{cv_id}", params={}
        )

        assert cv.id == cv_id
        assert cv.status == ConfigurationStatus.PENDING

    def test_read_invalid_id(self, configuration_versions_service):
        """Test read with invalid configuration version ID."""
        with pytest.raises(ValueError, match="invalid configuration version ID"):
            configuration_versions_service.read("")


class TestConfigurationVersionsReadWithOptions:
    """Test configuration versions read with options functionality."""

    def test_read_with_options_basic(
        self,
        configuration_versions_service,
        mock_transport,
        sample_cv_with_ingress_data,
    ):
        """Test read with options - basic functionality."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_cv_with_ingress_data}
        mock_transport.request.return_value = mock_response

        cv_id = "cv-ntv3HbhJqvFzamy7"
        options = ConfigurationVersionReadOptions(
            include=[ConfigVerIncludeOpt.INGRESS_ATTRIBUTES]
        )

        cv = configuration_versions_service.read_with_options(cv_id, options)

        # Verify request includes query parameters
        mock_transport.request.assert_called_once_with(
            "GET",
            f"/api/v2/configuration-versions/{cv_id}",
            params={"include": "ingress_attributes"},
        )

        # Verify ingress attributes are parsed
        assert cv.id == cv_id
        assert cv.ingress_attributes is not None
        assert cv.ingress_attributes.branch == "main"
        assert cv.ingress_attributes.clone_url == "https://github.com/example/repo.git"

    def test_read_with_options_no_ingress(
        self, configuration_versions_service, mock_transport, sample_cv_data
    ):
        """Test read with options when no ingress attributes present."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_cv_data}
        mock_transport.request.return_value = mock_response

        cv_id = "cv-ntv3HbhJqvFzamy7"
        options = ConfigurationVersionReadOptions(
            include=[ConfigVerIncludeOpt.INGRESS_ATTRIBUTES]
        )

        cv = configuration_versions_service.read_with_options(cv_id, options)

        assert cv.ingress_attributes is None


class TestConfigurationVersionsUpload:
    """Test configuration versions upload functionality."""

    def test_upload_missing_slug(self, configuration_versions_service):
        """Test upload when go-slug is not available."""
        upload_url = "https://example.com/upload"
        directory_path = "/tmp/test"

        with patch("src.tfe.utils.slug", None):
            with pytest.raises(ImportError, match="go-slug package is required"):
                configuration_versions_service.upload(upload_url, directory_path)

    @patch("src.tfe.utils.slug")
    def test_upload_success(self, mock_slug, configuration_versions_service):
        """Test successful upload."""
        # Mock slug.pack
        mock_packer = Mock()
        mock_packer.pack.return_value = (None, None)  # (size, error)
        mock_slug.Packer.return_value = mock_packer

        upload_url = "https://example.com/upload"
        directory_path = "/tmp/test"

        # Mock transport's underlying httpx client instead of direct httpx
        mock_response = Mock()
        mock_response.status_code = 200
        configuration_versions_service.t._sync.put.return_value = mock_response

        configuration_versions_service.upload(upload_url, directory_path)

        # Verify slug.pack was called
        mock_packer.pack.assert_called_once()


class TestConfigurationVersionsUploadTarGzip:
    """Test configuration versions upload_tar_gzip functionality."""

    def test_upload_tar_gzip_success(self, configuration_versions_service):
        """Test successful tar gzip upload."""
        upload_url = "https://example.com/upload"

        # Create a mock archive
        archive_data = b"mock-tar-gzip-data"
        mock_archive = io.BytesIO(archive_data)

        # Mock the transport's underlying httpx client
        mock_response = Mock()
        mock_response.status_code = 200
        configuration_versions_service.t._sync.put.return_value = mock_response

        configuration_versions_service.upload_tar_gzip(upload_url, mock_archive)

        # Verify transport's httpx client PUT request
        configuration_versions_service.t._sync.put.assert_called_once_with(
            upload_url,
            content=archive_data,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(archive_data)),
            },
            follow_redirects=True,
        )


class TestConfigurationVersionsUploadErrors:
    """Test configuration version upload error functionality."""

    def test_upload_tar_gzip_http_error(self, configuration_versions_service):
        """Test upload_tar_gzip with HTTP error."""
        upload_url = "https://example.com/upload"
        mock_archive = io.BytesIO(b"data")

        # Mock the transport's underlying httpx client to return an error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        configuration_versions_service.t._sync.put.return_value = mock_response

        with pytest.raises(TFEError, match="Upload failed"):
            configuration_versions_service.upload_tar_gzip(upload_url, mock_archive)


class TestConfigurationVersionsDownload:
    """Test configuration versions download functionality."""

    def test_download_success(self, configuration_versions_service, mock_transport):
        """Test successful download."""
        cv_id = "cv-ntv3HbhJqvFzamy7"
        expected_content = b"mock-tar-gzip-content"

        mock_response = Mock()
        mock_response.content = expected_content
        mock_transport.request.return_value = mock_response

        content = configuration_versions_service.download(cv_id)

        mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/configuration-versions/{cv_id}/download"
        )

        assert content == expected_content

    def test_download_invalid_id(self, configuration_versions_service):
        """Test download with invalid configuration version ID."""
        with pytest.raises(ValueError, match="invalid configuration version ID"):
            configuration_versions_service.download("")


class TestConfigurationVersionsArchive:
    """Test configuration versions archive functionality."""

    def test_archive_success(self, configuration_versions_service, mock_transport):
        """Test successful archive."""
        cv_id = "cv-ntv3HbhJqvFzamy7"

        mock_response = Mock()
        mock_transport.request.return_value = mock_response

        configuration_versions_service.archive(cv_id)

        mock_transport.request.assert_called_once_with(
            "POST", f"/api/v2/configuration-versions/{cv_id}/actions/archive"
        )

    def test_archive_invalid_id(self, configuration_versions_service):
        """Test archive with invalid configuration version ID."""
        with pytest.raises(ValueError, match="invalid configuration version ID"):
            configuration_versions_service.archive("")


class TestConfigurationVersionsRegistryModule:
    """Test configuration versions registry module functionality."""

    def test_create_for_registry_module_success(
        self, configuration_versions_service, mock_transport, sample_cv_data
    ):
        """Test successful registry module configuration version creation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": sample_cv_data}
        mock_transport.request.return_value = mock_response

        module_id = {
            "organization": "hashicorp",
            "registry_name": "private",
            "namespace": "hashicorp",
            "name": "example",
            "provider": "aws",
        }

        cv = configuration_versions_service.create_for_registry_module(module_id)

        # Verify the API path construction includes /configuration-versions at end
        expected_path = (
            "/api/v2/organizations/hashicorp/registry-modules/private/"
            "hashicorp/example/provider/aws/test-runs/configuration-versions"
        )
        mock_transport.request.assert_called_once_with("POST", expected_path)

        assert cv.id == "cv-ntv3HbhJqvFzamy7"

    def test_create_for_registry_module_not_found(
        self, configuration_versions_service, mock_transport
    ):
        """Test registry module not found error."""
        mock_transport.request.side_effect = NotFound("Registry module not found")

        module_id = {
            "organization": "hashicorp",
            "registry_name": "private",
            "namespace": "hashicorp",
            "name": "nonexistent",
            "provider": "aws",
        }

        with pytest.raises(NotFound):
            configuration_versions_service.create_for_registry_module(module_id)


class TestConfigurationVersionsEnterpriseBackingData:
    """Test configuration versions Enterprise backing data functionality."""

    def test_soft_delete_backing_data_success(
        self, configuration_versions_service, mock_transport
    ):
        """Test successful soft delete backing data."""
        cv_id = "cv-ntv3HbhJqvFzamy7"
        mock_transport.request.return_value = Mock()

        configuration_versions_service.soft_delete_backing_data(cv_id)

        mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/configuration-versions/{cv_id}/actions/soft_delete_backing_data",
        )

    def test_soft_delete_backing_data_not_enterprise(
        self, configuration_versions_service, mock_transport
    ):
        """Test soft delete backing data on non-Enterprise installation."""
        cv_id = "cv-ntv3HbhJqvFzamy7"
        mock_transport.request.side_effect = NotFound("Configuration version not found")

        with pytest.raises(NotFound):
            configuration_versions_service.soft_delete_backing_data(cv_id)

    def test_restore_backing_data_success(
        self, configuration_versions_service, mock_transport
    ):
        """Test successful restore backing data."""
        cv_id = "cv-ntv3HbhJqvFzamy7"
        mock_transport.request.return_value = Mock()

        configuration_versions_service.restore_backing_data(cv_id)

        mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/configuration-versions/{cv_id}/actions/restore_backing_data",
        )

    def test_permanently_delete_backing_data_success(
        self, configuration_versions_service, mock_transport
    ):
        """Test successful permanent delete backing data."""
        cv_id = "cv-ntv3HbhJqvFzamy7"
        mock_transport.request.return_value = Mock()

        configuration_versions_service.permanently_delete_backing_data(cv_id)

        mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/configuration-versions/{cv_id}/actions/permanently_delete_backing_data",
        )

    def test_enterprise_backing_data_invalid_id(self, configuration_versions_service):
        """Test Enterprise backing data methods with invalid CV ID."""
        with pytest.raises(ValueError, match="invalid configuration version ID"):
            configuration_versions_service.soft_delete_backing_data("")

        with pytest.raises(ValueError, match="invalid configuration version ID"):
            configuration_versions_service.restore_backing_data("")

        with pytest.raises(ValueError, match="invalid configuration version ID"):
            configuration_versions_service.permanently_delete_backing_data("")


class TestConfigurationVersionsParsing:
    """Test configuration version parsing functionality."""

    def test_parse_configuration_version_complete(
        self, configuration_versions_service, sample_cv_with_ingress_data
    ):
        """Test parsing complete configuration version with all fields."""
        cv = configuration_versions_service._parse_configuration_version(
            sample_cv_with_ingress_data
        )

        assert cv.id == "cv-ntv3HbhJqvFzamy7"
        assert cv.status == ConfigurationStatus.UPLOADED
        assert cv.source == ConfigurationSource.GITHUB
        assert cv.auto_queue_runs is True
        assert cv.speculative is False
        assert cv.provisional is False
        assert cv.upload_url is None
        assert cv.error is None
        assert cv.error_message is None

        # Test status timestamps
        assert cv.status_timestamps is not None
        assert "uploaded-at" in cv.status_timestamps

        # Test ingress attributes
        assert cv.ingress_attributes is not None
        assert cv.ingress_attributes.branch == "main"
        assert cv.ingress_attributes.clone_url == "https://github.com/example/repo.git"
        assert cv.ingress_attributes.commit_message == "Update configuration"
        assert cv.ingress_attributes.commit_sha == "abc123def456"
        assert cv.ingress_attributes.is_pull_request is False
        assert cv.ingress_attributes.on_default_branch is True

    def test_parse_configuration_version_minimal(
        self, configuration_versions_service, sample_cv_data
    ):
        """Test parsing minimal configuration version."""
        cv = configuration_versions_service._parse_configuration_version(sample_cv_data)

        assert cv.id == "cv-ntv3HbhJqvFzamy7"
        assert cv.status == ConfigurationStatus.PENDING
        assert cv.source == ConfigurationSource.API
        assert cv.ingress_attributes is None

    def test_parse_configuration_version_none_data(
        self, configuration_versions_service
    ):
        """Test parsing with None data raises error."""
        with pytest.raises(
            ValueError, match="Cannot parse configuration version: data is None"
        ):
            configuration_versions_service._parse_configuration_version(None)


class TestConfigurationVersionsValidation:
    """Test configuration version ID validation."""

    def test_valid_string_id_valid(self, configuration_versions_service):
        """Test valid_string_id with valid configuration version ID."""
        from src.tfe.utils import valid_string_id

        # This should return True and not raise an exception
        result = valid_string_id("cv-ntv3HbhJqvFzamy7")
        assert result is True

    def test_valid_string_id_invalid(self, configuration_versions_service):
        """Test valid_string_id with invalid configuration version ID."""
        from src.tfe.utils import valid_string_id

        # This should return False
        result = valid_string_id("")
        assert result is False

        result = valid_string_id(None)
        assert result is False


class TestConfigurationVersionsIntegration:
    """Integration-style tests that verify end-to-end functionality."""

    def test_full_workflow_simulation(
        self, configuration_versions_service, mock_transport
    ):
        """Test a complete workflow: create -> upload -> read -> archive."""
        cv_id = "cv-workflow-test"
        workspace_id = "ws-workflow-test"

        # Mock data for different states
        pending_cv_data = {
            "id": cv_id,
            "type": "configuration-versions",
            "attributes": {
                "status": "pending",
                "upload-url": "https://example.com/upload",
                "auto-queue-runs": False,
                "speculative": True,
                "source": "tfe-api",
                "provisional": False,
            },
        }

        uploaded_cv_data = {
            "id": cv_id,
            "type": "configuration-versions",
            "attributes": {
                "status": "uploaded",
                "upload-url": None,
                "auto-queue-runs": False,
                "speculative": True,
                "source": "tfe-api",
                "provisional": False,
                "status-timestamps": {"uploaded-at": "2024-01-15T10:30:00Z"},
            },
        }

        # Step 1: Create configuration version
        create_response = Mock()
        create_response.json.return_value = {"data": pending_cv_data}

        # Step 2: Read after upload
        read_response = Mock()
        read_response.json.return_value = {"data": uploaded_cv_data}

        # Step 3: Archive
        archive_response = Mock()

        mock_transport.request.side_effect = [
            create_response,  # create
            read_response,  # read
            archive_response,  # archive
        ]

        # Execute workflow
        options = ConfigurationVersionCreateOptions(
            auto_queue_runs=False, speculative=True
        )

        # Create
        cv = configuration_versions_service.create(workspace_id, options)
        assert cv.status == ConfigurationStatus.PENDING
        assert cv.upload_url == "https://example.com/upload"

        # Read (simulate after upload)
        cv_updated = configuration_versions_service.read(cv_id)
        assert cv_updated.status == ConfigurationStatus.UPLOADED
        assert cv_updated.upload_url is None

        # Archive
        configuration_versions_service.archive(cv_id)

        # Verify all calls were made
        assert mock_transport.request.call_count == 3

        # Verify create call
        create_call = mock_transport.request.call_args_list[0]
        assert create_call[0][0] == "POST"
        assert (
            create_call[0][1]
            == f"/api/v2/workspaces/{workspace_id}/configuration-versions"
        )

        # Verify read call
        read_call = mock_transport.request.call_args_list[1]
        assert read_call[0][0] == "GET"
        assert read_call[0][1] == f"/api/v2/configuration-versions/{cv_id}"

        # Verify archive call
        archive_call = mock_transport.request.call_args_list[2]
        assert archive_call[0][0] == "POST"
        assert (
            archive_call[0][1]
            == f"/api/v2/configuration-versions/{cv_id}/actions/archive"
        )
