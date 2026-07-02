# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import InvalidStackIDError
from ..models.stack import Stack
from ..models.stack_deployment import (
    StackDeployment,
    StackDeploymentListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class StackDeployments(_Service):
    """Service for reading the deployments that belong to a stack."""

    def list(
        self,
        stack_id: str,
        options: StackDeploymentListOptions | None = None,
    ) -> Iterator[StackDeployment]:
        """List the deployments that belong to a stack.

        Args:
            stack_id: The stack ID (e.g. ``"st-xxxxxxxx"``).
            options: Optional pagination and includes, as a
                :class:`StackDeploymentListOptions`.

        Returns:
            A single-use ``Iterator[StackDeployment]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidStackIDError: If ``stack_id`` is empty or malformed.
            TFEError: If the API request fails.

        Example:
            >>> for deployment in client.stack_deployments.list("st-xyz789"):
            ...     print(deployment.id, deployment.name)
        """
        if not valid_string_id(stack_id):
            raise InvalidStackIDError()
        path = f"/api/v2/stacks/{stack_id}/stack-deployments"
        params: dict[str, Any] = {}
        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])
        for item in self._list(path=path, params=params):
            yield self._stack_deployment_from(item)

    def _stack_deployment_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> StackDeployment:
        """Parse a StackDeployment from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"stack": Stack},
                included=included,
            )
        )
        return attach_jsonapi(StackDeployment.model_validate(attrs), data, included)
