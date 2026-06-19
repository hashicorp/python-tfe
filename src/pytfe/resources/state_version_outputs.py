# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..models.state_version_output import (
    StateVersionOutput,
    StateVersionOutputsListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


class StateVersionOutputs(_Service):
    """
    HCPTF and TFE State Version Outputs service.

    Endpoints:
      - GET /api/v2/state-version-outputs/:id
      - GET /api/v2/workspaces/:workspace_id/current-state-version-outputs
    """

    def read(self, output_id: str) -> StateVersionOutput:
        """Read a specific state version output by ID.

        Args:
            output_id: The state version output ID (e.g. ``"wsout-xxxxxxxx"``).

        Returns:
            The :class:`StateVersionOutput`.

        Raises:
            ValueError: If ``output_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> output = client.state_version_outputs.read("wsout-1")
            >>> print(output.name, output.value)
        """
        if not valid_string_id(output_id):
            raise ValueError("invalid output id")

        r = self.t.request("GET", f"/api/v2/state-version-outputs/{output_id}")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        return attach_jsonapi(
            StateVersionOutput(
                id=_safe_str(d.get("id")),
                **{k.replace("-", "_"): v for k, v in attr.items()},
            ),
            d,
        )

    def read_current(
        self,
        workspace_id: str,
        options: StateVersionOutputsListOptions | None = None,
    ) -> Iterator[StateVersionOutput]:
        """Read outputs for the workspace's current state version.

        Sensitive outputs are returned by the API with ``null`` values.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Pagination options, as a :class:`StateVersionOutputsListOptions`.

        Returns:
            A single-use ``Iterator[StateVersionOutput]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import StateVersionOutputsListOptions
            >>> outputs = client.state_version_outputs.read_current(
            ...     "ws-123", StateVersionOutputsListOptions(page_size=5)
            ... )
            >>> for output in outputs:
            ...     print(output.name)
        """
        if not valid_string_id(workspace_id):
            raise ValueError("invalid workspace id")

        params: dict[str, Any] = {}
        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size
        path = f"/api/v2/workspaces/{workspace_id}/current-state-version-outputs"

        for d in self._list(path, params=params):
            attr = d.get("attributes", {}) or {}
            yield attach_jsonapi(
                StateVersionOutput(
                    id=_safe_str(d.get("id")),
                    **{k.replace("-", "_"): v for k, v in attr.items()},
                ),
                d,
            )
