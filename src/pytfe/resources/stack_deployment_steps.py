# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import (
    InvalidStackDeploymentRunIDError,
    InvalidStackDeploymentStepIDError,
)
from ..models.stack_deployment_run import StackDeploymentRun
from ..models.stack_deployment_step import (
    StackDeploymentStep,
    StackDeploymentStepArtifactType,
    StackDeploymentStepListOptions,
    StackDeploymentStepReadOptions,
    StackDiagnostic,
    StackDiagnosticListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class StackDeploymentSteps(_Service):
    """Service for listing and acting on deployment steps within a deployment run."""

    def list(
        self,
        stack_deployment_run_id: str,
        options: StackDeploymentStepListOptions | None = None,
    ) -> Iterator[StackDeploymentStep]:
        """List the deployment steps for a stack deployment run.

        Args:
            stack_deployment_run_id: The deployment run ID (e.g. ``"sdr-abc123"``).
            options: Optional pagination and includes, as a
                :class:`StackDeploymentStepListOptions`.

        Returns:
            A single-use ``Iterator[StackDeploymentStep]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidStackDeploymentRunIDError: If ``stack_deployment_run_id`` is empty or
                malformed.
            TFEError: If the API request fails.

        Example:
            >>> for step in client.stack_deployment_steps.list("sdr-abc123"):
            ...     print(step.id, step.status)
        """
        if not valid_string_id(stack_deployment_run_id):
            raise InvalidStackDeploymentRunIDError()
        path = f"/api/v2/stack-deployment-runs/{stack_deployment_run_id}/stack-deployment-steps"
        params: dict[str, Any] = {}
        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])
        for item in self._list(path=path, params=params):
            yield self._stack_deployment_step_from(item)

    def read(
        self,
        stack_deployment_step_id: str,
        options: StackDeploymentStepReadOptions | None = None,
    ) -> StackDeploymentStep:
        """Read a stack deployment step by its ID.

        Args:
            stack_deployment_step_id: The deployment step ID (e.g. ``"sds-abc123"``).
            options: Optional includes, as a :class:`StackDeploymentStepReadOptions`.

        Returns:
            The :class:`StackDeploymentStep`.

        Raises:
            InvalidStackDeploymentStepIDError: If ``stack_deployment_step_id`` is empty
                or malformed.
            TFEError: If the API request fails.

        Example:
            >>> step = client.stack_deployment_steps.read("sds-abc123")
            >>> print(step.status)
        """
        if not valid_string_id(stack_deployment_step_id):
            raise InvalidStackDeploymentStepIDError()
        path = f"/api/v2/stack-deployment-steps/{stack_deployment_step_id}"
        params: dict[str, str] = {}
        if options and options.include:
            params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request("GET", path=path, params=params)
        payload = r.json()
        data = payload.get("data", {})
        return self._stack_deployment_step_from(data, payload.get("included"))

    def advance(
        self,
        stack_deployment_step_id: str,
    ) -> None:
        """Advance a stack deployment step that is in the ``pending-operator`` state.

        Args:
            stack_deployment_step_id: The deployment step ID (e.g. ``"sds-abc123"``).

        Returns:
            ``None`` on success (HTTP 200, no body).

        Raises:
            InvalidStackDeploymentStepIDError: If ``stack_deployment_step_id`` is empty
                or malformed.
            TFEError: If the API request fails.

        Example:
            >>> client.stack_deployment_steps.advance("sds-abc123")
        """
        if not valid_string_id(stack_deployment_step_id):
            raise InvalidStackDeploymentStepIDError()
        path = f"/api/v2/stack-deployment-steps/{stack_deployment_step_id}/advance"
        self.t.request("POST", path=path)

    def list_diagnostics(
        self,
        stack_deployment_step_id: str,
        options: StackDiagnosticListOptions | None = None,
    ) -> Iterator[StackDiagnostic]:
        """List the diagnostics emitted for a stack deployment step.

        Args:
            stack_deployment_step_id: The deployment step ID (e.g. ``"sds-abc123"``).
            options: Optional pagination, as a :class:`StackDiagnosticListOptions`.

        Returns:
            A single-use ``Iterator[StackDiagnostic]``.

        Raises:
            InvalidStackDeploymentStepIDError: If ``stack_deployment_step_id`` is empty
                or malformed.
            TFEError: If the API request fails.

        Example:
            >>> for diag in client.stack_deployment_steps.list_diagnostics("sds-abc123"):
            ...     print(diag.severity, diag.summary)
        """
        if not valid_string_id(stack_deployment_step_id):
            raise InvalidStackDeploymentStepIDError()
        path = f"/api/v2/stack-deployment-steps/{stack_deployment_step_id}/stack-diagnostics"
        params: dict[str, Any] = {}
        if options and options.page_size is not None:
            params["page[size]"] = options.page_size
        for item in self._list(path=path, params=params):
            yield self._stack_diagnostic_from(item)

    def download_artifact(
        self,
        stack_deployment_step_id: str,
        artifact_type: StackDeploymentStepArtifactType,
    ) -> bytes:
        """Download an artifact for a stack deployment step.

        Follows the redirect to the archivist URL and returns the raw artifact bytes.

        Args:
            stack_deployment_step_id: The deployment step ID (e.g. ``"sds-abc123"``).
            artifact_type: The artifact to download, as a
                :class:`StackDeploymentStepArtifactType`.

        Returns:
            The raw artifact content as ``bytes``.

        Raises:
            InvalidStackDeploymentStepIDError: If ``stack_deployment_step_id`` is empty
                or malformed.
            TFEError: If the API request fails.

        Example:
            >>> content = client.stack_deployment_steps.download_artifact(
            ...     "sds-abc123",
            ...     StackDeploymentStepArtifactType.PLAN_DESCRIPTION,
            ... )
            >>> print(content.decode())
        """
        if not valid_string_id(stack_deployment_step_id):
            raise InvalidStackDeploymentStepIDError()
        path = f"/api/v2/stack-deployment-steps/{stack_deployment_step_id}/artifacts"
        resp = self.t.request("GET", path=path, params={"name": artifact_type.value})
        return resp.content

    def _stack_deployment_step_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> StackDeploymentStep:
        """Parse a StackDeploymentStep from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"stack-deployment-run": StackDeploymentRun},
                included=included,
            )
        )
        return attach_jsonapi(
            StackDeploymentStep.model_validate(attrs), data, included
        )

    def _stack_diagnostic_from(
        self,
        data: dict[str, Any],
    ) -> StackDiagnostic:
        """Parse a StackDiagnostic from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        return attach_jsonapi(StackDiagnostic.model_validate(attrs), data, None)
