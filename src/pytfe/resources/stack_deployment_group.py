# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import (
    InvalidStackConfigurationIDError,
    InvalidStackDeploymentGroupIDError,
)
from ..models.stack_configuration import StackConfiguration
from ..models.stack_deployment_group import (
    StackDeploymentGroup,
    StackDeploymentGroupListOptions,
    StackDeploymentGroupRerunOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class StackDeploymentGroups(_Service):
    """Service for reading and managing deployment groups within a stack configuration."""

    def list(
        self,
        stack_configuration_id: str,
        options: StackDeploymentGroupListOptions | None = None,
    ) -> Iterator[StackDeploymentGroup]:
        """List the deployment groups for a stack configuration.

        Args:
            stack_configuration_id: The stack configuration ID (e.g. ``"stc-abc123"``).
            options: Optional pagination, as a :class:`StackDeploymentGroupListOptions`.

        Returns:
            A single-use ``Iterator[StackDeploymentGroup]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidStackConfigurationIDError: If ``stack_configuration_id`` is empty or
                malformed.
            TFEError: If the API request fails.

        Example:
            >>> for group in client.stack_deployment_groups.list("stc-abc123"):
            ...     print(group.id, group.name, group.status)
        """
        if not valid_string_id(stack_configuration_id):
            raise InvalidStackConfigurationIDError()
        path = f"/api/v2/stack-configurations/{stack_configuration_id}/stack-deployment-groups"
        params: dict[str, Any] = {}
        if options and options.page_size is not None:
            params["page[size]"] = options.page_size
        for item in self._list(path=path, params=params):
            yield self._stack_deployment_group_from(item)

    def read(
        self,
        stack_deployment_group_id: str,
    ) -> StackDeploymentGroup:
        """Read a stack deployment group by its ID.

        Args:
            stack_deployment_group_id: The deployment group ID (e.g. ``"sdg-xyz789"``).

        Returns:
            The :class:`StackDeploymentGroup`.

        Raises:
            InvalidStackDeploymentGroupIDError: If ``stack_deployment_group_id`` is empty
                or malformed.
            TFEError: If the API request fails.

        Example:
            >>> group = client.stack_deployment_groups.read("sdg-xyz789")
            >>> print(group.status)
        """
        if not valid_string_id(stack_deployment_group_id):
            raise InvalidStackDeploymentGroupIDError()
        path = f"/api/v2/stack-deployment-groups/{stack_deployment_group_id}"
        r = self.t.request("GET", path=path)
        payload = r.json()
        data = payload.get("data", {})
        return self._stack_deployment_group_from(data, payload.get("included"))

    def read_by_name(
        self,
        stack_configuration_id: str,
        name: str,
    ) -> StackDeploymentGroup:
        """Read a stack deployment group by its name within a stack configuration.

        Args:
            stack_configuration_id: The stack configuration ID (e.g. ``"stc-abc123"``).
            name: The deployment name (e.g. ``"dev"``).

        Returns:
            The :class:`StackDeploymentGroup`.

        Raises:
            InvalidStackConfigurationIDError: If ``stack_configuration_id`` is empty or
                malformed.
            TFEError: If the API request fails.

        Example:
            >>> group = client.stack_deployment_groups.read_by_name("stc-abc123", "dev")
            >>> print(group.id, group.status)
        """
        if not valid_string_id(stack_configuration_id):
            raise InvalidStackConfigurationIDError()
        path = f"/api/v2/stack-configurations/{stack_configuration_id}/stack-deployment-groups/{name}"
        r = self.t.request("GET", path=path)
        payload = r.json()
        data = payload.get("data", {})
        return self._stack_deployment_group_from(data, payload.get("included"))

    def approve_all_plans(
        self,
        stack_deployment_group_id: str,
    ) -> None:
        """Approve all pending plans in a stack deployment group.

        Args:
            stack_deployment_group_id: The deployment group ID (e.g. ``"sdg-xyz789"``).

        Returns:
            ``None`` on success (HTTP 200, no body).

        Raises:
            InvalidStackDeploymentGroupIDError: If ``stack_deployment_group_id`` is empty
                or malformed.
            TFEError: If the API request fails.

        Example:
            >>> client.stack_deployment_groups.approve_all_plans("sdg-xyz789")
        """
        if not valid_string_id(stack_deployment_group_id):
            raise InvalidStackDeploymentGroupIDError()
        path = f"/api/v2/stack-deployment-groups/{stack_deployment_group_id}/approve-all-plans"
        self.t.request("POST", path=path)

    def rerun(
        self,
        stack_deployment_group_id: str,
        options: StackDeploymentGroupRerunOptions,
    ) -> None:
        """Rerun a failed deployment group by re-executing specific deployments within it.

        This endpoint is intended for deployment groups that have ended up in a
        ``failed`` state. Pass the **deployment names** (the ``deployment`` attribute
        on each run, e.g. ``"dev"``, ``"prod"``), not run IDs.

        Args:
            stack_deployment_group_id: The deployment group ID (e.g. ``"sdg-xyz789"``).
            options: Required rerun options containing the deployment names to re-execute,
                as a :class:`StackDeploymentGroupRerunOptions`. Must include at least one
                deployment name.

        Returns:
            ``None`` on success (HTTP 204, no body).

        Raises:
            InvalidStackDeploymentGroupIDError: If ``stack_deployment_group_id`` is empty
                or malformed.
            ValueError: If ``options.deployments`` is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import StackDeploymentGroupRerunOptions
            >>> client.stack_deployment_groups.rerun(
            ...     "sdg-xyz789",
            ...     StackDeploymentGroupRerunOptions(deployments=["dev", "prod"]),
            ... )
        """
        if not valid_string_id(stack_deployment_group_id):
            raise InvalidStackDeploymentGroupIDError()
        if not options.deployments:
            raise ValueError(
                "options.deployments must contain at least one deployment name"
            )
        path = f"/api/v2/stack-deployment-groups/{stack_deployment_group_id}/rerun"
        params: dict[str, str] = {"deployments": ",".join(options.deployments)}
        self.t.request("POST", path=path, params=params)

    def _stack_deployment_group_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> StackDeploymentGroup:
        """Parse a StackDeploymentGroup from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"stack-configuration": StackConfiguration},
                included=included,
            )
        )
        return attach_jsonapi(
            StackDeploymentGroup.model_validate(attrs), data, included
        )
