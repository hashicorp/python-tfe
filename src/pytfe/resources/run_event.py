# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import InvalidRunEventIDError, InvalidRunIDError
from ..models.run_event import (
    RunEvent,
    RunEventListOptions,
    RunEventReadOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class RunEvents(_Service):
    def list(
        self, run_id: str, options: RunEventListOptions | None = None
    ) -> Iterator[RunEvent]:
        """List all the run events of the given run."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join(options.include)
        path = f"/api/v2/runs/{run_id}/run-events"
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            yield RunEvent.model_validate(attrs)

    def read(self, run_event_id: str) -> RunEvent:
        """Read a specific run event by its ID."""
        return self.read_with_options(run_event_id)

    def read_with_options(
        self, run_event_id: str, options: RunEventReadOptions | None = None
    ) -> RunEvent:
        """Read a specific run event by its ID with the given options."""
        if not valid_string_id(run_event_id):
            raise InvalidRunEventIDError()
        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join(options.include)
        r = self.t.request(
            "GET",
            f"/api/v2/run-events/{run_event_id}",
            params=params,
        )
        d = r.json().get("data", {})
        attr = d.get("attributes", {}) or {}
        return RunEvent(
            id=d.get("id"),
            **{k.replace("-", "_"): v for k, v in attr.items()},
        )
