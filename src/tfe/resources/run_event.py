from __future__ import annotations

from ..errors import InvalidRunEventIDError, InvalidRunIDError
from ..models.run_event import (
    RunEvent,
    RunEventList,
    RunEventListOptions,
    RunEventReadOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class RunEvents(_Service):
    def list(
        self, run_id: str, options: RunEventListOptions | None = None
    ) -> RunEventList:
        """List all the run events of the given run."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )
        r = self.t.request(
            "GET",
            f"/api/v2/runs/{run_id}/run-events",
            params=params,
        )
        jd = r.json()
        items = []
        meta = jd.get("meta", {})
        pagination = meta.get("pagination", {})
        for d in jd.get("data", []):
            attrs = d.get("attributes", {})
            attrs["id"] = d.get("id")
            items.append(RunEvent.model_validate(attrs))
        return RunEventList(
            items=items,
            current_page=pagination.get("current-page"),
            total_pages=pagination.get("total-pages"),
            prev_page=pagination.get("prev-page"),
            next_page=pagination.get("next-page"),
            total_count=pagination.get("total-count"),
        )

    def read(self, run_event_id: str) -> RunEvent:
        """Read a specific run event by its ID."""
        return self.read_with_options(run_event_id, None)

    def read_with_options(
        self, run_event_id: str, options: RunEventReadOptions | None = None
    ) -> RunEvent:
        """Read a specific run event by its ID with the given options."""
        if not valid_string_id(run_event_id):
            raise InvalidRunEventIDError()
        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )
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
