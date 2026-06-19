# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import (
    ERR_INVALID_ORG,
)
from ..models.registry_provider import (
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
        """List registry providers in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional filters, includes, and pagination settings, as a
                :class:`RegistryProviderListOptions`.

        Returns:
            A single-use ``Iterator[RegistryProvider]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> for provider in client.registry_providers.list("my-org"):
            ...     print(provider.namespace, provider.name)
        """
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
        """Create a registry provider in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The registry provider creation settings, as a
                :class:`RegistryProviderCreateOptions`.

        Returns:
            The created :class:`RegistryProvider`.

        Raises:
            ValueError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderCreateOptions
            >>> provider = client.registry_providers.create(
            ...     "my-org",
            ...     RegistryProviderCreateOptions(
            ...         name="example",
            ...         namespace="my-org",
            ...         registry_name=RegistryName.PRIVATE,
            ...     ),
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

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
        """Read a registry provider by composite ID.

        Args:
            provider_id: The registry provider identifier, as a
                :class:`RegistryProviderID`.
            options: Optional include settings, as a
                :class:`RegistryProviderReadOptions`.

        Returns:
            The :class:`RegistryProvider`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderID
            >>> provider = client.registry_providers.read(
            ...     RegistryProviderID(
            ...         organization_name="my-org",
            ...         registry_name=RegistryName.PRIVATE,
            ...         namespace="my-org",
            ...         name="example",
            ...     )
            ... )
        """
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
        return self._parse_registry_provider(
            response_data["data"], response_data.get("included")
        )

    def delete(self, provider_id: RegistryProviderID) -> None:
        """Delete a registry provider by composite ID.

        Args:
            provider_id: The registry provider identifier, as a
                :class:`RegistryProviderID`.

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RegistryName, RegistryProviderID
            >>> client.registry_providers.delete(
            ...     RegistryProviderID(
            ...         organization_name="my-org",
            ...         registry_name=RegistryName.PRIVATE,
            ...         namespace="my-org",
            ...         name="example",
            ...     )
            ... )
        """
        path = (
            f"/api/v2/organizations/{provider_id.organization_name}/"
            f"registry-providers/{provider_id.registry_name.value}/"
            f"{provider_id.namespace}/{provider_id.name}"
        )

        self.t.request("DELETE", path)

    def _parse_registry_provider(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> RegistryProvider:
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

        return attach_jsonapi(RegistryProvider(**provider_data), data, included)
