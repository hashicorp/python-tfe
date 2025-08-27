from unittest.mock import Mock, patch

import pytest

from tfe import client, config


@pytest.fixture
def test_config():
    return config.Config(address="https://app.terraform.io", token="test-token")


@pytest.fixture
def mock_response():
    response = Mock()
    response.headers = {
        "TFP-API-Version": "2.5.0",
        "X-TFE-Version": "v202308-1",
        "TFP-AppName": "HCP Terraform",
    }
    response.raise_for_status.return_value = None
    return response


class TestClient:
    @patch("requests.Session.get")
    def test_client_initialization(self, mock_get, test_config, mock_response):
        """Test basic client setup works."""
        mock_get.return_value = mock_response

        client_instance = client.Client(config=test_config)

        assert client_instance.config.address == "https://app.terraform.io"
        assert client_instance.config.token == "test-token"
        assert client_instance.base_url == "https://app.terraform.io/api/v2/"
        assert (
            client_instance.registry_base_url
            == "https://app.terraform.io/api/registry/"
        )

    @patch("requests.Session.get")
    def test_url_normalization(self, mock_get, mock_response):
        """Test that paths get normalized with trailing slashes."""
        mock_get.return_value = mock_response

        cfg = config.Config(
            address="https://example.com",
            token="test",
            base_path="/custom/api",  # no trailing slash
            registry_base_path="/registry",  # no trailing slash
        )

        client_instance = client.Client(config=cfg)

        assert client_instance.base_url == "https://example.com/custom/api/"
        assert client_instance.registry_base_url == "https://example.com/registry/"

    @patch("requests.Session.get")
    def test_api_metadata_extraction(self, mock_get, test_config, mock_response):
        """Test that API metadata gets extracted from response headers."""
        mock_get.return_value = mock_response

        client_instance = client.Client(config=test_config)

        assert client_instance.remote_api_version == "2.5.0"
        assert client_instance.remote_tfe_version == "v202308-1"
        assert client_instance.app_name == "HCP Terraform"

    @patch("requests.Session.get")
    def test_cloud_vs_enterprise_detection(self, mock_get, test_config):
        """Test detection between cloud and enterprise instances."""
        # Test HCP Terraform (cloud)
        cloud_response = Mock()
        cloud_response.headers = {"TFP-AppName": "HCP Terraform"}
        cloud_response.raise_for_status.return_value = None
        mock_get.return_value = cloud_response

        cloud_client = client.Client(config=test_config)
        assert cloud_client.is_cloud() is True
        assert cloud_client.is_enterprise() is False

        # Test Terraform Enterprise
        enterprise_response = Mock()
        enterprise_response.headers = {"TFP-AppName": "Terraform Enterprise"}
        enterprise_response.raise_for_status.return_value = None
        mock_get.return_value = enterprise_response

        enterprise_client = client.Client(config=test_config)
        assert enterprise_client.is_cloud() is False
        assert enterprise_client.is_enterprise() is True

    @patch("requests.Session.get")
    def test_fake_api_version_for_testing(self, mock_get, test_config, mock_response):
        """Test the fake API version setter for testing scenarios."""
        mock_get.return_value = mock_response

        client_instance = client.Client(config=test_config)

        # Original version from mock
        assert client_instance.remote_api_version == "2.5.0"

        # Set fake version
        client_instance.set_fake_remote_api_version("3.0.0")
        assert client_instance.remote_api_version == "3.0.0"
