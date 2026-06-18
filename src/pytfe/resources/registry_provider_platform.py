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
        """Create a registry provider platform"""
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
        """List registry provider platforms for a specific version"""
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
        """Read a specific registry provider platform"""
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
        """Delete a specific registry provider platform"""
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
