from __future__ import annotations

from typing import Any

from ..models.state_version_output import (
    StateVersionOutput,
    StateVersionOutputsList,
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
    ) -> StateVersionOutputsList:
        """
        Read outputs for the workspace's current state version.
        Note: sensitive outputs are returned with null values by the API.
        """
        if not valid_string_id(workspace_id):
            raise ValueError("invalid workspace id")

        params: dict[str, Any] = {}
        if options:
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size

        r = self.t.request(
            "GET",
            f"/api/v2/workspaces/{workspace_id}/current-state-version-outputs",
            params=params,
        )
        data = r.json()

        items: list[StateVersionOutput] = []
        for item in data.get("data", []):
            attr = item.get("attributes", {}) or {}
            items.append(
                StateVersionOutput(
                    id=_safe_str(item.get("id")),
                    **{k.replace("-", "_"): v for k, v in attr.items()},
                )
            )

        meta = data.get("meta", {}).get("pagination", {}) or {}
        return StateVersionOutputsList(
            items=items,
            current_page=meta.get("current-page"),
            total_pages=meta.get("total-pages"),
            total_count=meta.get("total-count"),
        )
