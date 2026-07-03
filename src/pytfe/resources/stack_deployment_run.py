# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import (
    InvalidStackDeploymentGroupIDError,
    InvalidStackDeploymentRunIDError,
)
from ..models.stack_deployment_group import StackDeploymentGroup
from ..models.stack_deployment_run import (
    StackDeploymentRun,
    StackDeploymentRunListOptions,
    StackDeploymentRunReadOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class StackDeploymentRuns(_Service):
    """Service for reading and acting on deployment runs within a deployment group."""

    def list(
        self,
        stack_deployment_group_id: str,
        options: StackDeploymentRunListOptions | None = None,
    ) -> Iterator[StackDeploymentRun]:
        """List the deployment runs for a deployment group.

        Args:
            stack_deployment_group_id: The deployment group ID (e.g. ``"sdg-xyz789"``).
            options: Optional pagination and includes, as a
                :class:`StackDeploymentRunListOptions`.

        Returns:
            A single-use ``Iterator[StackDeploymentRun]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidStackDeploymentGroupIDError: If ``stack_deployment_group_id`` is empty
                or malformed.
            TFEError: If the API request fails.

        Example:
            >>> for run in client.stack_deployment_runs.list("sdg-xyz789"):
            ...     print(run.id, run.status)
        """
        if not valid_string_id(stack_deployment_group_id):
            raise InvalidStackDeploymentGroupIDError()
        path = f"/api/v2/stack-deployment-groups/{stack_deployment_group_id}/stack-deployment-runs"
        params: dict[str, Any] = {}
        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])
        for item in self._list(path=path, params=params):
            yield self._stack_deployment_run_from(item)

    def read(
        self,
        stack_deployment_run_id: str,
        options: StackDeploymentRunReadOptions | None = None,
    ) -> StackDeploymentRun:
        """Read a stack deployment run by its ID.

        Args:
            stack_deployment_run_id: The deployment run ID (e.g. ``"sdr-abc123"``).
            options: Optional includes, as a :class:`StackDeploymentRunReadOptions`.

        Returns:
            The :class:`StackDeploymentRun`.

        Raises:
            InvalidStackDeploymentRunIDError: If ``stack_deployment_run_id`` is empty or
                malformed.
            TFEError: If the API request fails.

        Example:
            >>> run = client.stack_deployment_runs.read("sdr-abc123")
            >>> print(run.status)
        """
        if not valid_string_id(stack_deployment_run_id):
            raise InvalidStackDeploymentRunIDError()
        path = f"/api/v2/stack-deployment-runs/{stack_deployment_run_id}"
        params: dict[str, str] = {}
        if options and options.include:
            params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request("GET", path=path, params=params)
        payload = r.json()
        data = payload.get("data", {})
        return self._stack_deployment_run_from(data, payload.get("included"))

    def approve_all_plans(
        self,
        stack_deployment_run_id: str,
    ) -> None:
        """Approve all pending plans in a stack deployment run.

        This unblocks a run that is in the
        ``pre-deploying-pending-operator`` or ``deploying-pending-operator`` state.

        Args:
            stack_deployment_run_id: The deployment run ID (e.g. ``"sdr-abc123"``).

        Returns:
            ``None`` on success (HTTP 200, no body).

        Raises:
            InvalidStackDeploymentRunIDError: If ``stack_deployment_run_id`` is empty or
                malformed.
            TFEError: If the API request fails.

        Example:
            >>> client.stack_deployment_runs.approve_all_plans("sdr-abc123")
        """
        if not valid_string_id(stack_deployment_run_id):
            raise InvalidStackDeploymentRunIDError()
        path = f"/api/v2/stack-deployment-runs/{stack_deployment_run_id}/approve-all-plans"
        self.t.request("POST", path=path)

    def cancel(
        self,
        stack_deployment_run_id: str,
    ) -> None:
        """Cancel a stack deployment run.

        Args:
            stack_deployment_run_id: The deployment run ID (e.g. ``"sdr-abc123"``).

        Returns:
            ``None`` on success (HTTP 200, no body).

        Raises:
            InvalidStackDeploymentRunIDError: If ``stack_deployment_run_id`` is empty or
                malformed.
            TFEError: If the API request fails.

        Example:
            >>> client.stack_deployment_runs.cancel("sdr-abc123")
        """
        if not valid_string_id(stack_deployment_run_id):
            raise InvalidStackDeploymentRunIDError()
        path = f"/api/v2/stack-deployment-runs/{stack_deployment_run_id}/cancel"
        self.t.request("POST", path=path)

    def _stack_deployment_run_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> StackDeploymentRun:
        """Parse a StackDeploymentRun from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"stack-deployment-group": StackDeploymentGroup},
                included=included,
            )
        )
        return attach_jsonapi(StackDeploymentRun.model_validate(attrs), data, included)
