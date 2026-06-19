# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
import io
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import (
    ERR_INVALID_CONFIG_VERSION_ID,
    ERR_INVALID_WORKSPACE_ID,
    AuthError,
    NotFound,
    ServerError,
    TFEError,
)
from ..models.configuration_version import (
    ConfigurationVersion,
    ConfigurationVersionCreateOptions,
    ConfigurationVersionListOptions,
    ConfigurationVersionReadOptions,
    IngressAttributes,
)
from ..utils import pack_contents, valid_string_id
from ._base import _Service


class ConfigurationVersions(_Service):
    """Configuration versions service for managing Terraform configuration versions."""

    def list(
        self, workspace_id: str, options: ConfigurationVersionListOptions | None = None
    ) -> Iterator[ConfigurationVersion]:
        """List configuration versions for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Optional pagination and include options, as a
                :class:`ConfigurationVersionListOptions`.

        Returns:
            A single-use ``Iterator[ConfigurationVersion]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ConfigurationVersionListOptions
            >>> versions = client.configuration_versions.list(
            ...     "ws-YnyXLq9fy38afEeb",
            ...     ConfigurationVersionListOptions(page_size=20),
            ... )
            >>> for version in versions:
            ...     print(version.id, version.status)
        """
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
        """Create a configuration version for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Optional create settings, as a
                :class:`ConfigurationVersionCreateOptions`.

        Returns:
            The created :class:`ConfigurationVersion`.

        Raises:
            ValueError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ConfigurationVersionCreateOptions
            >>> version = client.configuration_versions.create(
            ...     "ws-YnyXLq9fy38afEeb",
            ...     ConfigurationVersionCreateOptions(auto_queue_runs=True),
            ... )
        """
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
        """Create a configuration version for a registry module test run.

        Args:
            module_id: Registry module identifiers, including ``organization``,
                ``registry_name``, ``namespace``, ``name``, and ``provider``.

        Returns:
            The created :class:`ConfigurationVersion`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> version = client.configuration_versions.create_for_registry_module(
            ...     {
            ...         "organization": "my-org",
            ...         "registry_name": "private",
            ...         "namespace": "networking",
            ...         "name": "vpc",
            ...         "provider": "aws",
            ...     }
            ... )
        """
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
        """Read a configuration version by its ID.

        Args:
            cv_id: The configuration version ID (e.g. ``"cv-xxxxxxxx"``).

        Returns:
            The :class:`ConfigurationVersion`.

        Raises:
            ValueError: If ``cv_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> version = client.configuration_versions.read("cv-ntv3HbhJqvFzamy7")
            >>> print(version.status)
        """
        return self.read_with_options(cv_id, None)

    def read_with_options(
        self, cv_id: str, options: ConfigurationVersionReadOptions | None = None
    ) -> ConfigurationVersion:
        """Read a configuration version by its ID with include options.

        Args:
            cv_id: The configuration version ID (e.g. ``"cv-xxxxxxxx"``).
            options: Optional include options, as a
                :class:`ConfigurationVersionReadOptions`.

        Returns:
            The :class:`ConfigurationVersion`.

        Raises:
            ValueError: If ``cv_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import ConfigVerIncludeOpt
            >>> from pytfe.models import ConfigurationVersionReadOptions
            >>> version = client.configuration_versions.read_with_options(
            ...     "cv-ntv3HbhJqvFzamy7",
            ...     ConfigurationVersionReadOptions(
            ...         include=[ConfigVerIncludeOpt.INGRESS_ATTRIBUTES]
            ...     ),
            ... )
        """
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)

        path = f"/api/v2/configuration-versions/{cv_id}"
        params = {}

        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        response_data = response.json()
        return self._parse_configuration_version(
            response_data["data"], response_data.get("included")
        )

    def upload(self, upload_url: str, path: str) -> None:
        """Upload configuration files to a configuration version upload URL.

        Args:
            upload_url: The presigned upload URL from the configuration version.
            path: The local directory path to package and upload.

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> version = client.configuration_versions.create("ws-YnyXLq9fy38afEeb")
            >>> client.configuration_versions.upload(version.upload_url, "./terraform")
        """
        body = pack_contents(path)
        self.upload_tar_gzip(upload_url, body)

    def upload_tar_gzip(self, upload_url: str, archive: io.IOBase) -> None:
        """Upload a tar.gz archive to a configuration version upload URL.

        Args:
            upload_url: The presigned upload URL from the configuration version.
            archive: A file-like object containing gzipped tar archive bytes.

        Returns:
            None.

        Raises:
            ValueError: If ``archive`` is not a readable file-like object.
            NotFound: If the upload URL is not found or has expired.
            AuthError: If the token has no permission to upload to this URL.
            ServerError: If the upload server returns a server error.
            TFEError: If the upload fails or the API request fails.

        Example:
            >>> import io
            >>> version = client.configuration_versions.create("ws-YnyXLq9fy38afEeb")
            >>> with open("terraform.tar.gz", "rb") as fh:
            ...     client.configuration_versions.upload_tar_gzip(
            ...         version.upload_url, io.BytesIO(fh.read())
            ...     )
        """
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
        """Archive a configuration version.

        Args:
            cv_id: The configuration version ID (e.g. ``"cv-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``cv_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.configuration_versions.archive("cv-ntv3HbhJqvFzamy7")
        """
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)

        path = f"/api/v2/configuration-versions/{cv_id}/actions/archive"
        self.t.request("POST", path)

    def download(self, cv_id: str) -> bytes:
        """Download a configuration version archive.

        Args:
            cv_id: The configuration version ID (e.g. ``"cv-xxxxxxxx"``).

        Returns:
            The raw bytes (the SDK follows the storage/redirect URL for you).

        Raises:
            ValueError: If ``cv_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> archive = client.configuration_versions.download("cv-ntv3HbhJqvFzamy7")
            >>> len(archive)
        """
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)

        path = f"/api/v2/configuration-versions/{cv_id}/download"
        response = self.t.request("GET", path)
        return response.content

    def ingress_attributes(self, cv_id: str) -> IngressAttributes | None:
        """Get VCS ingress attributes for a configuration version.

        Args:
            cv_id: The configuration version ID (e.g. ``"cv-xxxxxxxx"``).

        Returns:
            The :class:`IngressAttributes`, or ``None`` when the configuration version
            was not created from VCS, the API returns ``null``, or older TFE returns
            404 for missing ingress data.

        Raises:
            ValueError: If ``cv_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> ingress = client.configuration_versions.ingress_attributes(
            ...     "cv-ntv3HbhJqvFzamy7"
            ... )
            >>> print(ingress.branch if ingress else "api-driven")
        """
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)
        try:
            response = self.t.request(
                "GET",
                f"/api/v2/configuration-versions/{cv_id}/ingress-attributes",
            )
        except NotFound:
            return None
        body = response.json()
        if body is None:
            return None
        if not isinstance(body, dict):
            return None
        # The OpenAPI spec describes the response as the bare
        # `ingress-attributes` resource, but the live API wraps it in the
        # standard JSON:API envelope. Accept both shapes.
        data = body.get("data", body)
        if not isinstance(data, dict) or not data:
            return None
        attributes = data.get("attributes")
        if not isinstance(attributes, dict):
            return None
        return IngressAttributes.model_validate(attributes)

    def soft_delete_backing_data(self, cv_id: str) -> None:
        """Soft delete backing data for a configuration version.

        Args:
            cv_id: The configuration version ID (e.g. ``"cv-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``cv_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.configuration_versions.soft_delete_backing_data(
            ...     "cv-ntv3HbhJqvFzamy7"
            ... )
        """
        self._manage_backing_data(cv_id, "soft_delete_backing_data")

    def restore_backing_data(self, cv_id: str) -> None:
        """Restore backing data for a configuration version.

        Args:
            cv_id: The configuration version ID (e.g. ``"cv-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``cv_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.configuration_versions.restore_backing_data(
            ...     "cv-ntv3HbhJqvFzamy7"
            ... )
        """
        self._manage_backing_data(cv_id, "restore_backing_data")

    def permanently_delete_backing_data(self, cv_id: str) -> None:
        """Permanently delete backing data for a configuration version.

        Args:
            cv_id: The configuration version ID (e.g. ``"cv-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``cv_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.configuration_versions.permanently_delete_backing_data(
            ...     "cv-ntv3HbhJqvFzamy7"
            ... )
        """
        self._manage_backing_data(cv_id, "permanently_delete_backing_data")

    def _manage_backing_data(self, cv_id: str, action: str) -> None:
        """Manage backing data for a configuration version."""
        if not valid_string_id(cv_id):
            raise ValueError(ERR_INVALID_CONFIG_VERSION_ID)

        path = f"/api/v2/configuration-versions/{cv_id}/actions/{action}"
        self.t.request("POST", path)

    def _parse_configuration_version(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
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

        return attach_jsonapi(ConfigurationVersion(**cv_data), data, included)
