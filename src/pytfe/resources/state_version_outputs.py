# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

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
        """Read a specific state version output by ID."""
        if not valid_string_id(output_id):
            raise ValueError("invalid output id")

        r = self.t.request("GET", f"/api/v2/state-version-outputs/{output_id}")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        return StateVersionOutput(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
        )

    def read_current(
        self,
        workspace_id: str,
        options: StateVersionOutputsListOptions | None = None,
    ) -> Iterator[StateVersionOutput]:
        """
        Read outputs for the workspace's current state version.
        Note: sensitive outputs are returned with null values by the API.
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
            yield StateVersionOutput(
                id=_safe_str(d.get("id")),
                **{k.replace("-", "_"): v for k, v in attr.items()},
            )
