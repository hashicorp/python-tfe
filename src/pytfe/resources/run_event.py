# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import RelationMap, attach_jsonapi, parse_relationships
from ..errors import InvalidRunEventIDError, InvalidRunIDError
from ..models.comment import Comment
from ..models.run_event import (
    RunEvent,
    RunEventListOptions,
    RunEventReadOptions,
)
from ..models.user import User
from ..utils import _safe_str, valid_string_id
from ._base import _Service

# Typed relations hydrated from ?include= (actor, comment); see RunEventIncludeOpt.
_RUN_EVENT_REL_MAP: RelationMap = {"actor": User, "comment": Comment}


def _run_event_from(
    d: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> RunEvent:
    attr = d.get("attributes", {}) or {}
    rels = parse_relationships(
        d.get("relationships"), _RUN_EVENT_REL_MAP, included=included
    )
    return attach_jsonapi(
        RunEvent(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
            **rels,
        ),
        d,
        included,
    )


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
        # The run-events endpoint is not paginated; fetch the full set in one request.
        path = f"/api/v2/runs/{run_id}/run-events"
        for item in self._list(path, params=params, paginated=False):
            yield _run_event_from(item)

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
        payload = r.json()
        return _run_event_from(payload.get("data", {}), payload.get("included"))
