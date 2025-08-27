"""
Main client class for Terraform Enterprise/Cloud API.
"""

import logging
from urllib.parse import urljoin

from tfe.config import Config

logger = logging.getLogger(__name__)


class TFEClientError(Exception):
    """Base exception for TFE client errors."""

    pass


class Client:
    """
    Client is the Terraform Enterprise API client. It provides the basic
    functionality to interact with the Terraform API.
    """

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._setup_urls()

        self._api_version = ""
        self._tfe_version = ""
        self._app_name = ""
        self._fetch_api_metadata()

    def _setup_urls(self) -> None:
        """Parse and setup base URLs."""
        # Ensure base path ends with /
        base_path = self.config.base_path
        if not base_path.endswith("/"):
            base_path += "/"

        registry_path = self.config.registry_base_path
        if not registry_path.endswith("/"):
            registry_path += "/"

        self.base_url = urljoin(self.config.address, base_path)
        self.registry_base_url = urljoin(self.config.address, registry_path)

    def _fetch_api_metadata(self) -> None:
        """Fetch API metadata from the server."""
        ping_url = urljoin(self.base_url, "ping")
        headers = {
            "Accept": "application/vnd.api+json",
        }
        if self.config.headers:
            headers.update(self.config.headers)

        response = self.config.http_client.get(ping_url, headers=headers)
        response.raise_for_status()

        # Extract metadata from headers
        self._api_version = response.headers.get("TFP-API-Version", "")
        self._tfe_version = response.headers.get("X-TFE-Version", "")
        self._app_name = response.headers.get("TFP-AppName", "")

    @property
    def remote_api_version(self) -> str:
        """Return the server's declared API version string."""
        return self._api_version

    @property
    def remote_tfe_version(self) -> str:
        """Return the server's declared TFE version string."""
        return self._tfe_version

    @property
    def app_name(self) -> str:
        """Return the name of the instance."""
        return self._app_name

    def is_cloud(self) -> bool:
        """Return True if the client is configured against HCP Terraform."""
        return self._app_name == "HCP Terraform"

    def is_enterprise(self) -> bool:
        """Return True if the client is configured against Terraform Enterprise."""
        return not self.is_cloud()

    def set_fake_remote_api_version(self, version: str) -> None:
        """Set a fake API version for testing purposes."""
        self._api_version = version
