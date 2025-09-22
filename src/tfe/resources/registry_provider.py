from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    ERR_INVALID_ORG,
)
from ..models.registry_provider_types import (
    RegistryName,
    RegistryProvider,
    RegistryProviderCreateOptions,
    RegistryProviderID,
    RegistryProviderListOptions,
    RegistryProviderPermissions,
    RegistryProviderReadOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class RegistryProviders(_Service):
    """Registry providers service for managing Terraform registry providers."""

    def list(
        self, organization: str, options: RegistryProviderListOptions | None = None
    ) -> Iterator[RegistryProvider]:
        """List all the registry providers within an organization."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{organization}/registry-providers"
        params = {}

        if options:
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])
            if options.search:
                params["q"] = options.search
            if options.registry_name:
                params["filter[registry_name]"] = options.registry_name.value
            if options.organization_name:
                params["filter[organization_name]"] = options.organization_name
            if options.page_number:
                params["page[number]"] = str(options.page_number)
            if options.page_size:
                params["page[size]"] = str(options.page_size)

        for item in self._list(path, params=params):
            if item is None:
                continue  # type: ignore[unreachable]  # Skip None items
            yield self._parse_registry_provider(item)

    def create(
        self, organization: str, options: RegistryProviderCreateOptions
    ) -> RegistryProvider:
        """Create a registry provider."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        if not self._validate_create_options(options):
            raise ValueError("Invalid create options")

        path = f"/api/v2/organizations/{organization}/registry-providers"

        # Prepare the data payload
        data = {
            "data": {
                "type": "registry-providers",
                "attributes": {
                    "name": options.name,
                    "namespace": options.namespace,
                    "registry-name": options.registry_name.value,
                },
            }
        }

        response = self.t.request("POST", path, json_body=data)
        response_data = response.json()
        return self._parse_registry_provider(response_data["data"])

    def read(
        self,
        provider_id: RegistryProviderID,
        options: RegistryProviderReadOptions | None = None,
    ) -> RegistryProvider:
        """Read a specific registry provider."""
        if not self._validate_provider_id(provider_id):
            raise ValueError("Invalid provider ID")

        path = (
            f"/api/v2/organizations/{provider_id.organization_name}/"
            f"registry-providers/{provider_id.registry_name.value}/"
            f"{provider_id.namespace}/{provider_id.name}"
        )

        params = {}
        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        response_data = response.json()
        return self._parse_registry_provider(response_data["data"])

    def delete(self, provider_id: RegistryProviderID) -> None:
        """Delete a registry provider."""
        if not self._validate_provider_id(provider_id):
            raise ValueError("Invalid provider ID")

        path = (
            f"/api/v2/organizations/{provider_id.organization_name}/"
            f"registry-providers/{provider_id.registry_name.value}/"
            f"{provider_id.namespace}/{provider_id.name}"
        )

        self.t.request("DELETE", path)

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

    def _validate_create_options(self, options: RegistryProviderCreateOptions) -> bool:
        """Validate create options."""
        if not valid_string_id(options.name):
            return False
        if not valid_string_id(options.namespace):
            return False
        if options.registry_name not in [RegistryName.PRIVATE, RegistryName.PUBLIC]:
            return False
        return True

    def _parse_registry_provider(self, data: dict[str, Any]) -> RegistryProvider:
        """Parse a registry provider from API response data."""
        if data is None:
            raise ValueError("Cannot parse registry provider: data is None")

        attributes = data.get("attributes", {})
        relationships = data.get("relationships", {})

        # Parse timestamps
        created_at = attributes.get("created-at")
        updated_at = attributes.get("updated-at")

        # Parse permissions
        permissions_data = attributes.get("permissions", {})
        permissions = RegistryProviderPermissions(
            **{"can-delete": permissions_data.get("can-delete", False)}
        )

        # Parse relationships
        organization = None
        if "organization" in relationships:
            org_data = relationships["organization"].get("data")
            if org_data:
                organization = {"id": org_data.get("id"), "type": org_data.get("type")}

        registry_provider_versions = None
        if "registry-provider-versions" in relationships:
            versions_data = relationships["registry-provider-versions"].get("data", [])
            registry_provider_versions = [
                {"id": v.get("id"), "type": v.get("type")} for v in versions_data
            ]

        # Parse registry name
        registry_name_str = attributes.get("registry-name", "private")
        registry_name = (
            RegistryName.PRIVATE
            if registry_name_str == "private"
            else RegistryName.PUBLIC
        )

        # Create the provider data dict with aliases
        provider_data = {
            "id": data.get("id", ""),
            "name": attributes.get("name", ""),
            "namespace": attributes.get("namespace", ""),
            "created-at": created_at,
            "updated-at": updated_at,
            "registry-name": registry_name,
            "permissions": permissions,
            "organization": organization,
            "registry-provider-versions": registry_provider_versions,
            "links": data.get("links"),
        }

        return RegistryProvider(**provider_data)
