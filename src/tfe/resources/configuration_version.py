from __future__ import annotations

import io
from collections.abc import Iterator
from typing import Any

from ..errors import (
    ERR_INVALID_CONFIG_VERSION_ID,
    ERR_INVALID_WORKSPACE_ID,
    AuthError,
    NotFound,
    ServerError,
    TFEError,
)
from ..models.configuration_version_types import (
    ConfigurationVersion,
    ConfigurationVersionCreateOptions,
    ConfigurationVersionListOptions,
    ConfigurationVersionReadOptions,
)
from ..utils import pack_contents, valid_string_id
from ._base import _Service


class ConfigurationVersions(_Service):
    """Configuration versions service for managing Terraform configuration versions."""

    def list(
        self, workspace_id: str, options: ConfigurationVersionListOptions | None = None
    ) -> Iterator[ConfigurationVersion]:
        """List all configuration versions of a workspace."""
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)

        path = f"/api/v2/workspaces/{workspace_id}/configuration-versions"
        params = {}

        if options:
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])
            if options.page_number:
                params["page[number]"] = str(options.page_number)
            if options.page_size:
                params["page[size]"] = str(options.page_size)

        for item in self._list(path, params=params):
            if item is None:
                continue  # type: ignore[unreachable]
            yield self._parse_configuration_version(item)

    def create(
        self,
        workspace_id: str,
        options: ConfigurationVersionCreateOptions | None = None,
    ) -> ConfigurationVersion:
        """Create a new configuration version."""
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)

        if options is None:
            options = ConfigurationVersionCreateOptions()

        path = f"/api/v2/workspaces/{workspace_id}/configuration-versions"

        # Prepare the data payload
        data: dict[str, Any] = {
            "data": {
                "type": "configuration-versions",
                "attributes": {},
            }
        }

        # Add optional attributes
        if options.auto_queue_runs is not None:
            data["data"]["attributes"]["auto-queue-runs"] = options.auto_queue_runs
        if options.speculative is not None:
            data["data"]["attributes"]["speculative"] = options.speculative
        if options.provisional is not None:
            data["data"]["attributes"]["provisional"] = options.provisional

        response = self.t.request("POST", path, json_body=data)
        response_data = response.json()
        return self._parse_configuration_version(response_data["data"])

    def create_for_registry_module(
        self, module_id: dict[str, str]
    ) -> ConfigurationVersion:
        """Create a configuration version for a registry module (BETA)."""
        # This function creates configuration versions for test runs on registry modules
        # Path format: /api/v2/organizations/{org}/registry-modules/{registry_name}/{namespace}/{name}/provider/{provider}/test-runs
        org_name = module_id["organization"]
        registry_name = module_id["registry_name"]
        namespace = module_id["namespace"]
        name = module_id["name"]
        provider = module_id["provider"]

        path = f"/api/v2/organizations/{org_name}/registry-modules/{registry_name}/{namespace}/{name}/provider/{provider}/test-runs/configuration-versions"

        response = self.t.request("POST", path)
        response_data = response.json()
        return self._parse_configuration_version(response_data["data"])

    def read(self, cv_id: str) -> ConfigurationVersion:
        """Read a configuration version by its ID."""
        return self.read_with_options(cv_id, None)

    def read_with_options(
        self, cv_id: str, options: ConfigurationVersionReadOptions | None = None
    ) -> ConfigurationVersion:
        """Read a configuration version by its ID with options."""
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)

        path = f"/api/v2/configuration-versions/{cv_id}"
        params = {}

        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        response_data = response.json()
        return self._parse_configuration_version(response_data["data"])

    def upload(self, upload_url: str, path: str) -> None:
        """Upload configuration files from a directory path."""
        body = pack_contents(path)
        self.upload_tar_gzip(upload_url, body)

    def upload_tar_gzip(self, upload_url: str, archive: io.IOBase) -> None:
        """Upload a tar gzip archive to the configuration version upload URL."""
        # Get the binary content from the archive
        if hasattr(archive, "getvalue"):
            # BytesIO case
            archive_bytes = archive.getvalue()
        elif hasattr(archive, "read"):
            # File-like object case
            current_pos = archive.tell() if hasattr(archive, "tell") else None
            if current_pos is not None and hasattr(archive, "seek"):
                archive.seek(0)
            archive_bytes = archive.read()
            if current_pos is not None and hasattr(archive, "seek"):
                archive.seek(current_pos)
        else:
            raise ValueError(
                "Archive must be a file-like object with read() or getvalue() method"
            )

        # Use the transport layer's underlying httpx client for binary upload
        # This is a foreign PUT request to the upload URL that requires binary content
        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(archive_bytes)),
        }

        try:
            response = self.t._sync.put(
                upload_url,
                content=archive_bytes,
                headers=headers,
                follow_redirects=True,
            )

            if response.status_code not in [200, 201, 204]:
                if response.status_code == 404:
                    raise NotFound("Upload URL not found or expired")
                elif response.status_code == 403:
                    raise AuthError("No permission to upload to this URL")
                elif response.status_code >= 500:
                    raise ServerError(
                        f"Server error during upload: {response.status_code}"
                    )
                else:
                    raise TFEError(
                        f"Upload failed with status {response.status_code}: {response.text}"
                    )
        except Exception as e:
            if isinstance(e, NotFound | AuthError | ServerError | TFEError):
                raise
            raise TFEError(f"Upload failed: {str(e)}") from e

    def archive(self, cv_id: str) -> None:
        """Archive a configuration version."""
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)

        path = f"/api/v2/configuration-versions/{cv_id}/actions/archive"
        self.t.request("POST", path)

    def download(self, cv_id: str) -> bytes:
        """Download a configuration version."""
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)

        path = f"/api/v2/configuration-versions/{cv_id}/download"
        response = self.t.request("GET", path)
        return response.content

    def soft_delete_backing_data(self, cv_id: str) -> None:
        """Soft delete backing data for a configuration version (Enterprise only)."""
        self._manage_backing_data(cv_id, "soft_delete_backing_data")

    def restore_backing_data(self, cv_id: str) -> None:
        """Restore backing data for a configuration version (Enterprise only)."""
        self._manage_backing_data(cv_id, "restore_backing_data")

    def permanently_delete_backing_data(self, cv_id: str) -> None:
        """Permanently delete backing data for a configuration version (Enterprise only)."""
        self._manage_backing_data(cv_id, "permanently_delete_backing_data")

    def _manage_backing_data(self, cv_id: str, action: str) -> None:
        """Manage backing data for a configuration version."""
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)

        path = f"/api/v2/configuration-versions/{cv_id}/actions/{action}"
        self.t.request("POST", path)

    def _parse_configuration_version(
        self, data: dict[str, Any]
    ) -> ConfigurationVersion:
        """Parse a configuration version from API response data."""
        if data is None:
            raise ValueError("Cannot parse configuration version: data is None")

        attributes = data.get("attributes", {})

        # Parse ingress attributes if present
        ingress_attributes = None
        if "ingress_attributes" in attributes or "ingress-attributes" in attributes:
            ingress_data = attributes.get("ingress_attributes") or attributes.get(
                "ingress-attributes", {}
            )
            if ingress_data:
                ingress_attributes = ingress_data

        # Create the configuration version data dict with aliases
        cv_data = {
            "id": data.get("id", ""),
            "auto-queue-runs": attributes.get("auto-queue-runs", False),
            "error": attributes.get("error"),
            "error-message": attributes.get("error-message"),
            "source": attributes.get("source", "tfe-api"),
            "speculative": attributes.get("speculative", False),
            "status": attributes.get("status", "pending"),
            "status-timestamps": attributes.get("status-timestamps"),
            "provisional": attributes.get("provisional", False),
            "upload-url": attributes.get("upload-url"),
            "ingress-attributes": ingress_attributes,
            "links": data.get("links"),
        }

        return ConfigurationVersion(**cv_data)
