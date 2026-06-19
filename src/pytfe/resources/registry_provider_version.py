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
