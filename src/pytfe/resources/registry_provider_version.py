# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import (
    RequiredPrivateRegistryError,
)
from ..models.registry_provider import (
    RegistryName,
    RegistryProvider,
    RegistryProviderID,
)
from ..models.registry_provider_platform import RegistryProviderPlatform
from ..models.registry_provider_version import (
    RegistryProviderVersion,
    RegistryProviderVersionCreateOptions,
    RegistryProviderVersionID,
    RegistryProviderVersionListOptions,
)
from ._base import _Service


class RegistryProviderVersions(_Service):
    """Registry providers service for managing Terraform registry providers."""

    def create(
        self,
        provider_id: RegistryProviderID,
        options: RegistryProviderVersionCreateOptions,
    ) -> RegistryProviderVersion:
        """Create a private registry provider version.

        Args:
            provider_id: The provider identifier, as a :class:`RegistryProviderID`.
            options: The version attributes, as a
                :class:`RegistryProviderVersionCreateOptions`.

        Returns:
            The created :class:`RegistryProviderVersion`.

        Raises:
            RequiredPrivateRegistryError: If ``provider_id`` is not for the private
                registry.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import (
            ...     RegistryName,
            ...     RegistryProviderID,
            ...     RegistryProviderVersionCreateOptions,
            ... )
            >>> provider_id = RegistryProviderID(
            ...     organization_name="my-org",
            ...     registry_name=RegistryName.PRIVATE,
            ...     namespace="my-namespace",
            ...     name="my-provider",
            ... )
            >>> version = client.registry_provider_versions.create(
            ...     provider_id,
            ...     RegistryProviderVersionCreateOptions(
            ...         version="1.0.0", key_id="gpg-key-123", protocols=["5.0"]
            ...     ),
            ... )
        """
        if provider_id.registry_name != RegistryName.PRIVATE:
            raise RequiredPrivateRegistryError()
        path = f"/api/v2/organizations/{provider_id.organization_name}/registry-providers/{provider_id.registry_name.value}/{provider_id.namespace}/{provider_id.name}/versions"
        attributes = options.model_dump(by_alias=True, exclude_none=True)
        payload = {
            "data": {
                "type": "registry-provider-versions",
                "attributes": attributes,
            }
        }
        r = self.t.request(
            "POST",
            path=path,
            json_body=payload,
        )
        data = r.json().get("data", {})
        return self._registry_provider_version_from(data)

    def _registry_provider_version_from(
        self, data: dict[str, Any]
    ) -> RegistryProviderVersion:
        """Parse a registry provider version from API response data."""

        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {
                    "registry-provider": RegistryProvider,
                    # wire relation "platforms" maps to the divergent field name
                    "platforms": (
                        "registry_provider_platforms",
                        RegistryProviderPlatform,
                    ),
                },
            )
        )
        return attach_jsonapi(RegistryProviderVersion.model_validate(attrs), data)

    def list(
        self,
        provider_id: RegistryProviderID,
        options: RegistryProviderVersionListOptions | None = None,
    ) -> Iterator[RegistryProviderVersion]:
        """List private registry provider versions.

        Args:
            provider_id: The provider identifier, as a :class:`RegistryProviderID`.
            options: Optional pagination settings, as a
                :class:`RegistryProviderVersionListOptions`.

        Returns:
            A single-use ``Iterator[RegistryProviderVersion]``. Wrap with
            ``list(...)`` to materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderID
            >>> provider_id = RegistryProviderID(
            ...     organization_name="my-org",
            ...     registry_name=RegistryName.PRIVATE,
            ...     namespace="my-namespace",
            ...     name="my-provider",
            ... )
            >>> for version in client.registry_provider_versions.list(provider_id):
            ...     print(version.version)
        """
        path = f"/api/v2/organizations/{provider_id.organization_name}/registry-providers/{provider_id.registry_name.value}/{provider_id.namespace}/{provider_id.name}/versions"
        params = options.model_dump(by_alias=True) if options else {}
        for item in self._list(path=path, params=params):
            yield self._registry_provider_version_from(item)

    def read(self, version_id: RegistryProviderVersionID) -> RegistryProviderVersion:
        """Read a private registry provider version.

        Args:
            version_id: The provider version identifier, as a
                :class:`RegistryProviderVersionID`.

        Returns:
            The :class:`RegistryProviderVersion`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderVersionID
            >>> version_id = RegistryProviderVersionID(
            ...     organization_name="my-org",
            ...     registry_name=RegistryName.PRIVATE,
            ...     namespace="my-namespace",
            ...     name="my-provider",
            ...     version="1.0.0",
            ... )
            >>> version = client.registry_provider_versions.read(version_id)
        """
        path = f"/api/v2/organizations/{version_id.organization_name}/registry-providers/{version_id.registry_name.value}/{version_id.namespace}/{version_id.name}/versions/{version_id.version}"
        r = self.t.request(
            "GET",
            path=path,
        )
        data = r.json().get("data", {})
        return self._registry_provider_version_from(data)

    def delete(self, version_id: RegistryProviderVersionID) -> None:
        """Delete a private registry provider version.

        Args:
            version_id: The provider version identifier, as a
                :class:`RegistryProviderVersionID`.

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderVersionID
            >>> version_id = RegistryProviderVersionID(
            ...     organization_name="my-org",
            ...     registry_name=RegistryName.PRIVATE,
            ...     namespace="my-namespace",
            ...     name="my-provider",
            ...     version="1.0.0",
            ... )
            >>> client.registry_provider_versions.delete(version_id)
        """
        path = f"/api/v2/organizations/{version_id.organization_name}/registry-providers/{version_id.registry_name.value}/{version_id.namespace}/{version_id.name}/versions/{version_id.version}"
        self.t.request(
            "DELETE",
            path=path,
        )
        return None

    def upload_shasums(self, version: RegistryProviderVersion, shasums: bytes) -> None:
        """Upload the SHA256SUMS file for a private provider version.

        A provider version is not usable until both the SHA256SUMS file and its
        detached signature have been uploaded; ``version.shasums_uploaded``
        reports whether this step is done.

        Args:
            version: The version to upload for, as returned by :meth:`create`.
            shasums: The contents of the ``SHA256SUMS`` file.

        Returns:
            None.

        Raises:
            ValueError: If ``shasums`` is empty, or the version carries no
                upload link (which is the case once it has been uploaded).
            NotFound: If the upload URL has expired.
            AuthError: If the token may not upload to this URL.
            TFEError: If the upload fails.

        Example:
            >>> from pathlib import Path
            >>> version = client.registry_provider_versions.create(provider_id, opts)
            >>> client.registry_provider_versions.upload_shasums(
            ...     version, Path("terraform-provider-widget_1.0.0_SHA256SUMS").read_bytes()
            ... )
        """
        if not shasums:
            raise ValueError("shasums must not be empty")
        self._put(version.shasums_upload_url(), shasums)

    def upload_shasums_sig(
        self, version: RegistryProviderVersion, signature: bytes
    ) -> None:
        """Upload the detached SHA256SUMS signature for a provider version.

        Args:
            version: The version to upload for, as returned by :meth:`create`.
            signature: The contents of the ``SHA256SUMS.sig`` file, signed with
                the GPG key registered as the version's ``key_id``.

        Returns:
            None.

        Raises:
            ValueError: If ``signature`` is empty, or the version carries no
                signature upload link.
            NotFound: If the upload URL has expired.
            AuthError: If the token may not upload to this URL.
            TFEError: If the upload fails.

        Example:
            >>> from pathlib import Path
            >>> client.registry_provider_versions.upload_shasums_sig(
            ...     version,
            ...     Path("terraform-provider-widget_1.0.0_SHA256SUMS.sig").read_bytes(),
            ... )
        """
        if not signature:
            raise ValueError("signature must not be empty")
        self._put(version.shasums_sig_upload_url(), signature)

    def _put(self, upload_url: str, content: bytes) -> None:
        """PUT binary content to a presigned registry upload URL.

        Goes through the transport rather than the underlying HTTP client, so
        the upload inherits retries, typed error translation, and the read-only
        request gate. The bearer token is sent deliberately: these URLs point at
        HashiCorp's Archivist, which requires it.
        """
        self.t.request(
            "PUT",
            upload_url,
            data=content,
            headers={"Content-Type": "application/octet-stream"},
        )
