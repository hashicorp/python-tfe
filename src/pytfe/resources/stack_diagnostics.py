# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import (
    InvalidStackConfigurationIDError,
    InvalidStackDiagnosticIDError,
)
from ..models.stack_deployment_step import (
    StackDiagnostic,
    StackDiagnosticListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class StackDiagnostics(_Service):
    """Service for reading and acknowledging stack diagnostics."""

    def read(self, stack_diagnostic_id: str) -> StackDiagnostic:
        """Read a stack diagnostic by its ID.

        Args:
            stack_diagnostic_id: The stack diagnostic ID (e.g. ``"stf-abc123"``).

        Returns:
            The :class:`StackDiagnostic`.

        Raises:
            InvalidStackDiagnosticIDError: If ``stack_diagnostic_id`` is empty or
                malformed.
            TFEError: If the API request fails.

        Example:
            >>> diag = client.stack_diagnostics.read("stf-abc123")
            >>> print(diag.severity, diag.summary, diag.acknowledged)
        """
        if not valid_string_id(stack_diagnostic_id):
            raise InvalidStackDiagnosticIDError()
        path = f"/api/v2/stack-diagnostics/{stack_diagnostic_id}"
        r = self.t.request("GET", path=path)
        payload = r.json()
        data = payload.get("data", {})
        return self._diagnostic_from(data)

    def list_for_configuration(
        self,
        stack_configuration_id: str,
        options: StackDiagnosticListOptions | None = None,
    ) -> Iterator[StackDiagnostic]:
        """List the diagnostics a stack configuration reported while preparing.

        These are the errors that explain why a configuration reached
        ``failed`` - a malformed ``.tfcomponent.hcl``, an unresolvable
        component, a missing ``.terraform-version``. They are distinct from the
        diagnostics on a deployment step, which explain a *plan* or *apply*
        failure; read those with
        ``client.stack_deployment_steps.list_diagnostics``.

        Each diagnostic's ``summary``/``detail`` is a rollup. The per-error
        detail, with source file and line, is in ``diags``.

        Args:
            stack_configuration_id: The configuration ID (e.g. ``"stc-abc123"``).
            options: Optional pagination, as a :class:`StackDiagnosticListOptions`.

        Returns:
            A single-use ``Iterator[StackDiagnostic]``.

        Raises:
            InvalidStackConfigurationIDError: If the ID is empty or malformed.
            TFEError: If the API request fails.

        Example:
            >>> for diag in client.stack_diagnostics.list_for_configuration("stc-abc"):
            ...     print(diag.severity, diag.summary)
            ...     for d in diag.diags or []:
            ...         print("  ", d.get("filename"), d.get("summary"))
        """
        if not valid_string_id(stack_configuration_id):
            raise InvalidStackConfigurationIDError()
        path = (
            f"/api/v2/stack-configurations/{stack_configuration_id}/stack-diagnostics"
        )
        params: dict[str, Any] = {}
        if options and options.page_size is not None:
            params["page[size]"] = options.page_size
        for item in self._list(path=path, params=params):
            yield self._diagnostic_from(item)

    def acknowledge(self, stack_diagnostic_id: str) -> None:
        """Acknowledge a stack diagnostic, marking it as reviewed.

        Args:
            stack_diagnostic_id: The stack diagnostic ID (e.g. ``"stf-abc123"``).

        Returns:
            ``None`` on success.

        Raises:
            InvalidStackDiagnosticIDError: If ``stack_diagnostic_id`` is empty or
                malformed.
            TFEError: If the API request fails.

        Example:
            >>> client.stack_diagnostics.acknowledge("stf-abc123")
        """
        if not valid_string_id(stack_diagnostic_id):
            raise InvalidStackDiagnosticIDError()
        path = f"/api/v2/stack-diagnostics/{stack_diagnostic_id}/acknowledge"
        self.t.request("POST", path=path)

    def _diagnostic_from(self, data: dict[str, Any]) -> StackDiagnostic:
        """Parse a StackDiagnostic from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        return attach_jsonapi(StackDiagnostic.model_validate(attrs), data, None)
