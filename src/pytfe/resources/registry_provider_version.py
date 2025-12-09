from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    RequiredPrivateRegistryError,
)
from ..models.registry_provider import (
    RegistryName,
    RegistryProviderID,
)
from ..models.registry_provider_version import (
    RegistryProviderVersion,
    RegistryProviderVersionCreateOptions,
    RegistryProviderVersionID,
    RegistryProviderVersionListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class RegistryProviderVersions(_Service):
    """Registry providers service for managing Terraform registry providers."""

    def create(
        self,
        provider_id: RegistryProviderID,
        options: RegistryProviderVersionCreateOptions,
    ) -> RegistryProviderVersion:
        """Create a registry provider version"""
        if not self._validate_provider_id(provider_id):
            raise ValueError("Invalid provider ID")

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

    def _validate_provider_id(self, provider_id: RegistryProviderID) -> bool:
        """Validate a registry provider ID."""
        if not valid_string_id(provider_id.organization_name):
            return False
        if not valid_string_id(provider_id.name):
            return False
        if not valid_string_id(provider_id.namespace):
            return False
        if provider_id.registry_name not in [RegistryName.PRIVATE, RegistryName.PUBLIC]:
            return False
        return True

    def _registry_provider_version_from(
        self, data: dict[str, Any]
    ) -> RegistryProviderVersion:
        """Parse a registry provider version from API response data."""

        attrs = data.get("attributes", {})
        relationships = data.get("relationships", {})
        attrs["id"] = data.get("id")

        # Parse relationships
        if "registry-provider" in relationships:
            attrs["registry_provider"] = relationships["registry-provider"].get(
                "data", {}
            )

        if "platforms" in relationships:
            attrs["registry_provider_platforms"] = relationships["platforms"].get(
                "data", []
            )

        return RegistryProviderVersion.model_validate(attrs)

    def list(
        self,
        provider_id: RegistryProviderID,
        options: RegistryProviderVersionListOptions | None = None,
    ) -> Iterator[RegistryProviderVersion]:
        """List registry provider versions"""
        if not self._validate_provider_id(provider_id):
            raise ValueError("Invalid provider ID")

        path = f"/api/v2/organizations/{provider_id.organization_name}/registry-providers/{provider_id.registry_name.value}/{provider_id.namespace}/{provider_id.name}/versions"
        params = options.model_dump(by_alias=True) if options else {}
        for item in self._list(path=path, params=params):
            yield self._registry_provider_version_from(item)

    def read(self, version_id: RegistryProviderVersionID) -> RegistryProviderVersion:
        """Read a specific registry provider version"""
        if not self._validate_provider_id(version_id):
            raise ValueError("Invalid provider ID")

        path = f"/api/v2/organizations/{version_id.organization_name}/registry-providers/{version_id.registry_name.value}/{version_id.namespace}/{version_id.name}/versions/{version_id.version}"
        r = self.t.request(
            "GET",
            path=path,
        )
        data = r.json().get("data", {})
        return self._registry_provider_version_from(data)

    def delete(self, version_id: RegistryProviderVersionID) -> None:
        """Delete a specific registry provider version"""
        if not self._validate_provider_id(version_id):
            raise ValueError("Invalid provider ID")

        path = f"/api/v2/organizations/{version_id.organization_name}/registry-providers/{version_id.registry_name.value}/{version_id.namespace}/{version_id.name}/versions/{version_id.version}"
        self.t.request(
            "DELETE",
            path=path,
        )
        return None
