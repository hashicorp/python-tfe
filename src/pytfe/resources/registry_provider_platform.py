# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..models.registry_provider_platform import (
    RegistryProviderPlatform,
    RegistryProviderPlatformCreateOptions,
    RegistryProviderPlatformID,
    RegistryProviderPlatformListOptions,
)
from ..models.registry_provider_version import (
    RegistryProviderVersion,
    RegistryProviderVersionID,
)
from ._base import _Service


class RegistryProviderPlatforms(_Service):
    """Service for managing Terraform registry provider platforms."""

    def create(
        self,
        version_id: RegistryProviderVersionID,
        options: RegistryProviderPlatformCreateOptions,
    ) -> RegistryProviderPlatform:
        """Create a registry provider platform for a provider version.

        Args:
            version_id: The registry provider version identifier, as a
                :class:`RegistryProviderVersionID`.
            options: The platform metadata, as a
                :class:`RegistryProviderPlatformCreateOptions`.

        Returns:
            The :class:`RegistryProviderPlatform`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderVersionID
            >>> from pytfe.models import RegistryProviderPlatformCreateOptions
            >>> version_id = RegistryProviderVersionID(
            ...     organization_name="my-org", registry_name=RegistryName.PRIVATE,
            ...     namespace="my-org", name="aws", version="1.0.0",
            ... )
            >>> platform = client.registry_provider_platforms.create(
            ...     version_id,
            ...     RegistryProviderPlatformCreateOptions(
            ...         os="linux", arch="amd64", shasum="abc123", filename="provider.zip",
            ...     ),
            ... )
        """
        path = f"/api/v2/organizations/{version_id.organization_name}/registry-providers/{version_id.registry_name.value}/{version_id.namespace}/{version_id.name}/versions/{version_id.version}/platforms"
        attributes = options.model_dump(by_alias=True, exclude_none=True)
        payload = {
            "data": {
                "type": "registry-provider-platforms",
                "attributes": attributes,
            }
        }
        r = self.t.request("POST", path=path, json_body=payload)
        data = r.json().get("data", {})
        return self._registry_provider_platform_from(data)

    def list(
        self,
        version_id: RegistryProviderVersionID,
        options: RegistryProviderPlatformListOptions | None = None,
    ) -> Iterator[RegistryProviderPlatform]:
        """List registry provider platforms for a provider version.

        Args:
            version_id: The registry provider version identifier, as a
                :class:`RegistryProviderVersionID`.
            options: Optional pagination options, as a
                :class:`RegistryProviderPlatformListOptions`.

        Returns:
            A single-use ``Iterator[RegistryProviderPlatform]``. Wrap with
            ``list(...)`` to materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderVersionID
            >>> version_id = RegistryProviderVersionID(
            ...     organization_name="my-org", registry_name=RegistryName.PRIVATE,
            ...     namespace="my-org", name="aws", version="1.0.0",
            ... )
            >>> for platform in client.registry_provider_platforms.list(version_id):
            ...     print(platform.os, platform.arch)
        """
        path = (
            f"/api/v2/organizations/{version_id.organization_name}"
            f"/registry-providers/{version_id.registry_name.value}"
            f"/{version_id.namespace}/{version_id.name}"
            f"/versions/{version_id.version}/platforms"
        )
        params = options.model_dump(by_alias=True) if options else {}
        for item in self._list(path=path, params=params):
            yield self._registry_provider_platform_from(item)

    def read(self, platform_id: RegistryProviderPlatformID) -> RegistryProviderPlatform:
        """Read a registry provider platform by ID.

        Args:
            platform_id: The registry provider platform identifier, as a
                :class:`RegistryProviderPlatformID`.

        Returns:
            The :class:`RegistryProviderPlatform`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderPlatformID
            >>> platform_id = RegistryProviderPlatformID(
            ...     organization_name="my-org", registry_name=RegistryName.PRIVATE,
            ...     namespace="my-org", name="aws", version="1.0.0",
            ...     os="linux", arch="amd64",
            ... )
            >>> platform = client.registry_provider_platforms.read(platform_id)
        """
        path = (
            f"/api/v2/organizations/{platform_id.organization_name}"
            f"/registry-providers/{platform_id.registry_name.value}"
            f"/{platform_id.namespace}/{platform_id.name}"
            f"/versions/{platform_id.version}"
            f"/platforms/{platform_id.os}/{platform_id.arch}"
        )
        r = self.t.request("GET", path=path)
        data = r.json().get("data", {})
        return self._registry_provider_platform_from(data)

    def delete(self, platform_id: RegistryProviderPlatformID) -> None:
        """Delete a registry provider platform by ID.

        Args:
            platform_id: The registry provider platform identifier, as a
                :class:`RegistryProviderPlatformID`.

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderPlatformID
            >>> platform_id = RegistryProviderPlatformID(
            ...     organization_name="my-org", registry_name=RegistryName.PRIVATE,
            ...     namespace="my-org", name="aws", version="1.0.0",
            ...     os="linux", arch="amd64",
            ... )
            >>> client.registry_provider_platforms.delete(platform_id)
        """
        path = (
            f"/api/v2/organizations/{platform_id.organization_name}"
            f"/registry-providers/{platform_id.registry_name.value}"
            f"/{platform_id.namespace}/{platform_id.name}"
            f"/versions/{platform_id.version}"
            f"/platforms/{platform_id.os}/{platform_id.arch}"
        )
        self.t.request("DELETE", path=path)
        return None

    def _registry_provider_platform_from(
        self, data: dict[str, Any]
    ) -> RegistryProviderPlatform:
        """Parse a registry provider platform from API response data."""
        attrs = data.get("attributes", {})
        relationships = data.get("relationships", {})
        attrs["id"] = data.get("id")

        if (
            "registry-provider-version" in relationships
            and "data" in relationships["registry-provider-version"]
            and relationships["registry-provider-version"]["data"] is not None
        ):
            attrs["registry-provider-version"] = (
                RegistryProviderVersion.model_construct(
                    id=relationships["registry-provider-version"]["data"].get("id")
                )
            )

        if "links" in data:
            attrs["links"] = data["links"]

        return attach_jsonapi(RegistryProviderPlatform.model_validate(attrs), data)

    def upload_binary(self, platform: RegistryProviderPlatform, binary: bytes) -> None:
        """Upload the provider binary for one platform of a provider version.

        The binary is the zip archive named by the platform's ``filename``, and
        its SHA256 must match the ``shasum`` the platform was created with.
        ``platform.provider_binary_uploaded`` reports whether this step is done.

        Args:
            platform: The platform to upload for, as returned by :meth:`create`.
            binary: The contents of the provider zip archive.

        Returns:
            None.

        Raises:
            ValueError: If ``binary`` is empty, or the platform carries no
                upload link (which is the case once it has been uploaded).
            NotFound: If the upload URL has expired.
            AuthError: If the token may not upload to this URL.
            TFEError: If the upload fails.

        Example:
            >>> from pathlib import Path
            >>> platform = client.registry_provider_platforms.create(version_id, opts)
            >>> client.registry_provider_platforms.upload_binary(
            ...     platform,
            ...     Path("terraform-provider-widget_1.0.0_linux_amd64.zip").read_bytes(),
            ... )
        """
        if not binary:
            raise ValueError("binary must not be empty")
        # Through the transport, not the raw client, so the upload inherits
        # retries, typed errors and the read-only gate. Archivist requires the
        # bearer token, which request() sends by default.
        self.t.request(
            "PUT",
            platform.provider_binary_upload_url(),
            data=binary,
            headers={"Content-Type": "application/octet-stream"},
        )
