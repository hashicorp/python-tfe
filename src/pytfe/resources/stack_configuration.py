# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from pytfe.models.configuration_version import IngressAttributes

from .._jsonapi import attach_jsonapi, parse_relationships
from ..models.stack import Stack
from ..models.stack_configuration import (
    StackConfiguration,
    StackConfigurationCreateOptions,
    StackConfigurationListOptions,
    StackConfigurationReadOptions,
    StackConfigurationSource,
)
from ._base import _Service


class StackConfigurations(_Service):
    """Service for managing Terraform stack configurations."""

    def create(
        self,
        stack_id: str,
        options: StackConfigurationCreateOptions | None = None,
        source: StackConfigurationSource = StackConfigurationSource.MANUAL,
    ) -> StackConfiguration:
        """Create a stack configuration for the given stack.

        Args:
            stack_id: The stack ID (e.g. ``"st-xyz789"``).
            options: Optional creation settings, as a
                :class:`StackConfigurationCreateOptions`.
            source: How to source the configuration, as a
                :class:`StackConfigurationSource`.

        Returns:
            The created :class:`StackConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import StackConfigurationCreateOptions
            >>> config = client.stack_configurations.create(
            ...     "st-xyz789",
            ...     StackConfigurationCreateOptions(speculative_enabled=True),
            ... )
        """
        path = f"/api/v2/stacks/{stack_id}/stack-configurations"
        params: dict[str, str] = {}
        if source != StackConfigurationSource.MANUAL:
            params["source"] = source.value

        attributes: dict[str, Any] = {}
        if options:
            attributes = options.model_dump(by_alias=True, exclude_none=True)

        payload = {
            "data": {
                "type": "stack-configurations",
                "attributes": attributes,
            }
        }
        r = self.t.request("POST", path=path, json_body=payload, params=params)
        data = r.json().get("data", {})
        return self._stack_configuration_from(data)

    def list(
        self,
        stack_id: str,
        options: StackConfigurationListOptions | None = None,
    ) -> Iterator[StackConfiguration]:
        """List stack configurations for the given stack.

        Args:
            stack_id: The stack ID (e.g. ``"st-xyz789"``).
            options: Optional pagination and includes, as a
                :class:`StackConfigurationListOptions`.

        Returns:
            A single-use ``Iterator[StackConfiguration]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> for config in client.stack_configurations.list("st-xyz789"):
            ...     print(config.id, config.status)
        """
        path = f"/api/v2/stacks/{stack_id}/stack-configurations"
        params: dict[str, Any] = {}
        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])
        for item in self._list(path=path, params=params):
            yield self._stack_configuration_from(item)

    def read(
        self,
        stack_configuration_id: str,
        options: StackConfigurationReadOptions | None = None,
    ) -> StackConfiguration:
        """Read a stack configuration by its ID.

        Args:
            stack_configuration_id: The stack configuration ID (e.g. ``"stc-abc123"``).
            options: Optional related resources, as a
                :class:`StackConfigurationReadOptions`.

        Returns:
            The :class:`StackConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> config = client.stack_configurations.read("stc-abc123")
            >>> print(config.sequence_number)
        """
        path = f"/api/v2/stack-configurations/{stack_configuration_id}"
        params: dict[str, str] = {}
        if options and options.include:
            params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request("GET", path=path, params=params)
        payload = r.json()
        data = payload.get("data", {})
        return self._stack_configuration_from(data, payload.get("included"))

    def _stack_configuration_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> StackConfiguration:
        """Parse a StackConfiguration from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"stack": Stack, "ingress-attributes": IngressAttributes},
                included=included,
            )
        )
        return attach_jsonapi(StackConfiguration.model_validate(attrs), data, included)
